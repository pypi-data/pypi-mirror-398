//
// Extensions for putting the data results of queries in NumPy containers.
// Authors: Francesc Alted <francesc@continuum.io> (original author)
//          Oscar Villellas <oscar.villellas@continuum.io>
// Copyright: Continuum Analytics 2012-2014
//

#include "numpy/npy_common.h"
#include <cstdlib>
#include <unicode/unistr.h>
#include <unicode/ucnv.h>
#define NPY_NO_DEPRECATED_API NPY_1_25_API_VERSION

#include <Python.h>
#include <stdio.h>
#include <string.h>

#include <vector>

#include "numpy/ndarrayobject.h"
#include "numpy/npy_math.h"
#include "numpy/numpyconfig.h"
#include "numpy/halffloat.h"

#if NPY_ABI_VERSION >= 0x02000000
// If we compile with numpy>=2, include npy_2_compat.h which allows running against numpy<2
#include "numpy/npy_2_compat.h"
#else
// If we compile with numpy<2, we need to define these ourselves
static inline void
PyDataType_SET_ELSIZE(PyArray_Descr *dtype, npy_intp size) {
    dtype->elsize = size;
}
static inline npy_intp
PyDataType_ELSIZE(PyArray_Descr *dtype) {
    return dtype->elsize;
}
#endif

// clang-format off
// Keep ordering of these - the pyodbc headers
// do not correctly specify includes inside themselves,
// and there will be undefined objects if the order is changed.
#include "pyodbc.h"
#include "wrapper.h"
#include "textenc.h"
#include "connection.h"
#include "cursor.h"
#include "dbspecific.h"
#include "errors.h"
#include "pyodbcmodule.h"
#include <sqltypes.h>
// clang-format on

#include "npcontainer.h"

/* controls the maximum text field width, a negative value indicates that the
   text size limit will be dynamic based on the sql type, e.g. varchar (4000) */
Py_ssize_t iopro_text_limit = -1;

namespace {
inline size_t
limit_text_size(size_t sz)
{
    if (iopro_text_limit < 0) {
        return sz;
    }

    size_t sz_limit = static_cast<size_t>(iopro_text_limit);
    return sz < sz_limit ? sz : sz_limit;
}

/* a RAII class for Python GIL */
class PyNoGIL {
   public:
    PyNoGIL() { Py_UNBLOCK_THREADS }
    ~PyNoGIL() { Py_BLOCK_THREADS }

   private:
    PyThreadState *_save;
};

}  // namespace

// The number of rows to be fetched in case the driver cannot specify it
static size_t DEFAULT_ROWS_TO_BE_FETCHED = 10'000;
static size_t DEFAULT_ROWS_TO_BE_ALLOCATED = DEFAULT_ROWS_TO_BE_FETCHED;
// API version 7 is the first one that we can use DATE/TIME
// in a pretty bug-free way. This is set to true in
// the module init function if running on Numpy >= API version 7.
static bool CAN_USE_DATETIME = false;

/**
 * @brief Convert a SQL type to a string description of that type.
 *
 * @param type SQL type to convert
 * @return String description of that type
 */
const char *
sql_type_to_str(SQLSMALLINT type) {
    switch (type) {
        case SQL_CHAR:
            return "char";
        case SQL_VARCHAR:
            return "varchar";
        case SQL_LONGVARCHAR:
            return "longvarchar";
        case SQL_WCHAR:
            return "wchar";
        case SQL_WVARCHAR:
            return "wvarchar";
        case SQL_WLONGVARCHAR:
            return "wlongvarchar";
        case SQL_DECIMAL:
            return "decimal";
        case SQL_NUMERIC:
            return "numeric";
        case SQL_SMALLINT:
            return "smallint";
        case SQL_INTEGER:
            return "integer";
        case SQL_REAL:
            return "real";
        case SQL_FLOAT:
            return "float";
        case SQL_DOUBLE:
            return "double";
        case SQL_BIT:
            return "bit";
        case SQL_TINYINT:
            return "tiny";
        case SQL_BIGINT:
            return "bigint";
        case SQL_BINARY:
            return "binary";
        case SQL_VARBINARY:
            return "varbinary";
        case SQL_LONGVARBINARY:
            return "longvarbinary";
        case SQL_TYPE_DATE:
            return "date";
        case SQL_TYPE_TIME:
            return "time";
        case SQL_TYPE_TIMESTAMP:
            return "timestamp";
        case SQL_GUID:
            return "guid";
        default:
            return "UNKNOWN";
    }
}

/**
 * @brief Convert a SQL C type to a string description of that type.
 *
 * @param type SQL C type to convert
 * @return String description of that type
 */
const char *
sql_c_type_to_str(SQLSMALLINT type) {
    switch (type) {
        case SQL_C_BIT:
            return "bit";
        case SQL_C_CHAR:
            return "char";
        case SQL_C_WCHAR:
            return "wchar";
        case SQL_C_TINYINT:
            return "tinyint";
        case SQL_C_SSHORT:
            return "sshort";
        case SQL_C_SLONG:
            return "slong";
        case SQL_C_SBIGINT:
            return "sbigint";
        case SQL_C_FLOAT:
            return "float";
        case SQL_C_DOUBLE:
            return "double";
        case SQL_C_BINARY:
            return "binary";
        case SQL_C_TYPE_DATE:
            return "date struct";
        case SQL_C_TIMESTAMP:
            return "timestamp struct";
        case SQL_C_TIME:
            return "time struct";
        default:
            return "UNKNOWN";
    }
}

using namespace std;

// Days per month, regular year and leap year
int _days_per_month_table[2][12] = {{31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
                                    {31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}};

//
// Returns 1 if the given year is a leap year, 0 otherwise.
//
int
is_leapyear(SQLSMALLINT year)
{
    return (year & 0x3) == 0 && /* year % 4 == 0 */
           ((year % 100) != 0 || (year % 400) == 0);
}

//
// Calculates the days offset from the 1970 epoch.
//
// Code strongly based on its NumPy counterpart.
//
npy_int64
get_datestruct_days(const DATE_STRUCT *dts)
{
    int i, month;
    npy_int64 year = 0;
    npy_int64 days = 0;
    int *month_lengths;

    year = dts->year - 1'970;
    days = year * 365;

    /* Adjust for leap years */
    if (days >= 0) {
        /*
         * 1968 is the closest leap year before 1970.
         * Exclude the current year, so add 1.
         */
        year += 1;
        /* Add one day for each 4 years */
        days += year / 4;
        /* 1900 is the closest previous year divisible by 100 */
        year += 68;
        /* Subtract one day for each 100 years */
        days -= year / 100;
        /* 1600 is the closest previous year divisible by 400 */
        year += 300;
        /* Add one day for each 400 years */
        days += year / 400;
    }
    else {
        /*
         * 1972 is the closest later year after 1970.
         * Include the current year, so subtract 2.
         */
        year -= 2;
        /* Subtract one day for each 4 years */
        days += year / 4;
        /* 2000 is the closest later year divisible by 100 */
        year -= 28;
        /* Add one day for each 100 years */
        days -= year / 100;
        /* 2000 is also the closest later year divisible by 400 */
        /* Subtract one day for each 400 years */
        days += year / 400;
    }

    month_lengths = _days_per_month_table[is_leapyear(dts->year)];
    month = dts->month - 1;
    /* make sure month is in range. This prevents an illegal access
       when bad input is passed to this function */
    month = month < 0 || month > 11 ? 0 : month;

    /* Add the months */
    for (i = 0; i < month; ++i) {
        days += month_lengths[i];
    }

    /* Add the days */
    days += dts->day - 1;

    return days;
}

//
// Convert a datetime from a datetimestruct to a datetime64 based
// on some metadata. The date is assumed to be valid.
//
// This code is heavily based on NumPy 1.7 equivalent function.
// Only conversion to microseconds is supported here.
//
npy_datetime
convert_datetimestruct_to_datetime(const TIMESTAMP_STRUCT *dts)
{
    npy_datetime ret;

    // Calculate the number of days to start
    npy_int64 days = get_datestruct_days((DATE_STRUCT *)dts);
    ret = (((days * 24 + dts->hour) * 60 + dts->minute) * 60 + dts->second) * 1'000'000 +
          dts->fraction / 1'000;  // fraction is in ns (billionths of a second)

    return ret;
}

//
// Convert a date from a datestruct to a datetime64 based
// on some metadata. The date is assumed to be valid.
//
npy_datetime
convert_datestruct_to_datetime(const DATE_STRUCT *dts)
{
    // Calculate the number of days to start
    npy_datetime days = get_datestruct_days(dts);

    return days;
}

//
// Convert a time from a timestruct to a timedelta64 based
// on some metadata. The time is assumed to be valid.
//
npy_timedelta
convert_timestruct_to_timedelta(const TIME_STRUCT *dts)
{
    npy_timedelta seconds = (((dts->hour * 60) + dts->minute) * 60) + dts->second;

    return seconds;
}

//
// Fill NA particular values depending on the NumPy type
//
// The only cases that need to be supported are the ones that can
// actually be generated from SQL types
int
fill_NAvalue(void *value, PyArray_Descr *dtype)
{
    switch (dtype->type_num) {
        case NPY_BOOL:
            ((npy_bool *)value)[0] = 0;  // XXX False is a good default?
            break;
        case NPY_BYTE:
            ((npy_byte *)value)[0] = NPY_MAX_BYTE;
            break;
        case NPY_UBYTE:
            ((npy_ubyte *)value)[0] = NPY_MAX_UBYTE;
            break;
        case NPY_SHORT:
            ((npy_short *)value)[0] = NPY_MAX_SHORT;
            break;
        case NPY_USHORT:
            ((npy_ushort *)value)[0] = NPY_MAX_USHORT;
            break;
        case NPY_INT:
            ((npy_int *)value)[0] = NPY_MAX_INT;
            break;
        case NPY_UINT:
            ((npy_uint *)value)[0] = NPY_MAX_UINT;
            break;
        case NPY_LONG:
            ((npy_long *)value)[0] = NPY_MAX_LONG;
            break;
        case NPY_ULONG:
            ((npy_ulong *)value)[0] = NPY_MAX_ULONG;
            break;
        case NPY_LONGLONG:
            ((npy_longlong *)value)[0] = NPY_MAX_LONGLONG;
            break;
        case NPY_ULONGLONG:
            ((npy_ulonglong *)value)[0] = NPY_MAX_ULONGLONG;
            break;
        case NPY_HALF:
            ((npy_half *)value)[0] = NPY_HALF_NAN;
            break;
        case NPY_FLOAT:
            ((npy_float *)value)[0] = NPY_NANF;
            break;
        case NPY_DOUBLE:
            ((npy_float *)value)[0] = NPY_NAN;
            break;
        case NPY_LONGDOUBLE:
            ((npy_float *)value)[0] = NPY_NANL;
            break;
        case NPY_CFLOAT:
            ((npy_cfloat *)value)[0] = {NPY_NANF, NPY_NANF};
            break;
        case NPY_CDOUBLE:
            ((npy_cdouble *)value)[0] = {NPY_NAN, NPY_NAN};
            break;
        case NPY_CLONGDOUBLE:
            ((npy_clongdouble *)value)[0] = {NPY_NANL, NPY_NANL};
            break;
        case NPY_STRING:
        case NPY_UNICODE:
            memset(value, 0, static_cast<size_t>(PyDataType_ELSIZE(dtype)));
            break;
        case NPY_DATETIME:
        case NPY_TIMEDELTA:
            ((npy_int64 *)value)[0] = NPY_DATETIME_NAT;
            break;

#if NPY_ABI_VERSION >= 0x02000000
        case NPY_VSTRING:
#endif
        case NPY_OBJECT:
        case NPY_VOID:
        case NPY_NOTYPE:
        case NPY_USERDEF:
        default:
            PyObject *typestr = PyObject_Str((PyObject *)dtype->typeobj);

            if (typestr == NULL) {
                PyErr_Format(
                    PyExc_TypeError,
                    "Numpy data type doesn't support null values, but nulls were returned from the database. Unable to print string representation of dtype with type_num = %d",
                    dtype->type_num
                );
                return -1;
            }

            const char *str = PyUnicode_AsUTF8(typestr);
            Py_DECREF(typestr);

            if (str == NULL) {
                PyErr_Format(
                    PyExc_TypeError,
                    "Numpy data type doesn't support null values, but nulls were returned from the database. Unable to print string representation of dtype with type_num = %d",
                    dtype->type_num
                );
                return -1;
            }

            PyErr_Format(
                PyExc_TypeError,
                "Numpy data type %s doesn't support null values, but nulls were returned from the database.",
                str
            );
            return -1;
    }
    return 0;
}

static int
fill_NAarray(
    PyArrayObject *array,
    PyArrayObject *array_nulls,
    SQLLEN *nulls,
    size_t offset,
    size_t nrows
) {
    // Fill array with NA info in nullarray coming from ODBC
    npy_intp elsize_array = PyArray_ITEMSIZE(array);
    char *data_array = PyArray_BYTES(array);

    // Only the last nrows have to be updated
    data_array += offset * elsize_array;

    if (array_nulls) {
        char *data_array_nulls = PyArray_BYTES(array_nulls);
        npy_intp elsize_array_nulls = PyArray_ITEMSIZE(array_nulls);

        data_array_nulls += offset * elsize_array_nulls;

        for (size_t i = 0; i < nrows; ++i) {
            if (nulls[i] == SQL_NULL_DATA) {
                *data_array_nulls = NPY_TRUE;
                if (fill_NAvalue(data_array, PyArray_DESCR(array)) < 0) {
                    return -1;
                }
            }
            else {
                *data_array_nulls = NPY_FALSE;
            }
            data_array += elsize_array;
            data_array_nulls += elsize_array_nulls;
        }
    }
    else {
        for (size_t i = 0; i < nrows; ++i) {
            // If NULL are detected, don't show data in array
            if (nulls[i] == SQL_NULL_DATA) {
                if (fill_NAvalue(data_array, PyArray_DESCR(array)) < 0){
                    return -1;
                }
            }
            data_array += elsize_array;
        }
    }

    return 0;
}

//
// convert from ODBC format to NumPy format for selected types
// only types that need conversion are handled.
//
static void
convert_buffer(PyArrayObject *dst_array, void *src, int sql_c_type, SQLLEN offset, npy_intp nrows)
{
    switch (sql_c_type) {
        case SQL_C_TYPE_DATE: {
            npy_datetime *dst = reinterpret_cast<npy_datetime *>(PyArray_DATA(dst_array)) + offset;
            DATE_STRUCT *dates = static_cast<DATE_STRUCT *>(src);
            for (npy_intp i = 0; i < nrows; ++i) {
                dst[i] = convert_datestruct_to_datetime(dates + i);
            }
        } break;

        case SQL_C_TYPE_TIMESTAMP: {
            npy_datetime *dst = reinterpret_cast<npy_datetime *>(PyArray_DATA(dst_array)) + offset;
            TIMESTAMP_STRUCT *timestamps = static_cast<TIMESTAMP_STRUCT *>(src);
            for (npy_intp i = 0; i < nrows; ++i) {
                dst[i] = convert_datetimestruct_to_datetime(timestamps + i);
            }
        } break;

        case SQL_C_TYPE_TIME: {
            npy_timedelta *dst =
                    reinterpret_cast<npy_timedelta *>(PyArray_DATA(dst_array)) + offset;
            TIME_STRUCT *timestamps = static_cast<TIME_STRUCT *>(src);
            for (npy_intp i = 0; i < nrows; ++i) {
                dst[i] = convert_timestruct_to_timedelta(&timestamps[i]);
            }
        } break;

        case SQL_C_WCHAR: {
            // note that this conversion will only be called when using ucs2/utf16
            const SQLWCHAR *utf16 = reinterpret_cast<SQLWCHAR *>(src);
            size_t len = PyArray_ITEMSIZE(dst_array) / sizeof(npy_ucs4);
            npy_ucs4 *ucs4 = reinterpret_cast<npy_ucs4 *>(PyArray_DATA(dst_array)) + offset * len;

            for (npy_intp i = 0; i < nrows; ++i) {
                const SQLWCHAR *src = utf16 + 2 * len * i;
                size_t bufsize = len * sizeof(SQLWCHAR);

                // Create a UnicodeString to convert from the UTF16 stored in the database
                icu::UnicodeString unicode =
                        icu::UnicodeString(reinterpret_cast<const char16_t *>(src), bufsize);

                // Convert the UnicodeString to UTF8
                std::string strbuf;
                unicode.toUTF8String(strbuf);

                // Copy the multi-byte UTF8 string to the destination as a wchar_t string
                npy_ucs4 *dst = ucs4 + len * i;
                std::mbstowcs(reinterpret_cast<wchar_t *>(dst), strbuf.c_str(), len);
            }
        } break;

        default:
            PyErr_WarnEx(PyExc_RuntimeWarning, "Unexpected conversion in fill_dictarray.", 1);
            break;
    }
}

//
// Resize an array to a new length
//
// return 0 on success 1 on failure
//          on failure the returned array is unmodified
static int
resize_array(PyArrayObject *array, npy_intp new_len)
{
    int elsize = PyArray_ITEMSIZE(array);
    void *old_data = PyArray_DATA(array);
    npy_intp old_len = PyArray_DIMS(array)[0];
    void *new_data = NULL;

    // The next test is made so as to avoid a problem with resizing to 0
    // (it seems that this is solved for NumPy 1.7 series though)
    if (new_len > 0) {
        new_data = PyDataMem_RENEW(old_data, new_len * elsize);
        if (new_data == NULL) {
            return 1;
        }
    }
    else {
        free(old_data);
    }

    // this is far from ideal. We should probably be using internal buffers
    // and then creating the NumPy array using that internal buffer. This should
    // be possible and would be cleaner.
#if (NPY_API_VERSION >= 0x7)
    ((PyArrayObject_fields *)array)->data = (char *)new_data;
#else
    array->data = (char *)new_data;
#endif
    if ((old_len < new_len) && PyArray_ISSTRING(array)) {
        memset(PyArray_BYTES(array) + old_len * elsize, 0, (new_len - old_len) * elsize);
    }

    PyArray_DIMS(array)[0] = new_len;

    return 0;
}

namespace {
struct fetch_status {
    fetch_status(SQLHSTMT h, SQLULEN chunk_size);
    ~fetch_status();

    SQLLEN rows_read_;

    /* old stmtattr to restore on destruction */
    SQLHSTMT hstmt_;
    SQLULEN old_row_bind_type_;
    SQLULEN old_row_array_size_;
    SQLULEN *old_rows_fetched_ptr_;
};

fetch_status::fetch_status(SQLHSTMT h, SQLULEN chunk_size) : hstmt_(h)
{
    /* keep old stmt attr */
    SQLGetStmtAttr(hstmt_, SQL_ATTR_ROW_BIND_TYPE, &old_row_bind_type_, SQL_IS_UINTEGER, 0);
    SQLGetStmtAttr(hstmt_, SQL_ATTR_ROW_ARRAY_SIZE, &old_row_array_size_, SQL_IS_UINTEGER, 0);
    SQLGetStmtAttr(hstmt_, SQL_ATTR_ROWS_FETCHED_PTR, &old_rows_fetched_ptr_, SQL_IS_POINTER, 0);

    /* configure our stmt attr */
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROW_BIND_TYPE, SQL_BIND_BY_COLUMN, 0);
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROW_ARRAY_SIZE, (SQLPOINTER)chunk_size, 0);
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROWS_FETCHED_PTR, (SQLPOINTER)&rows_read_, 0);
}

fetch_status::~fetch_status()
{
    /* unbind all cols */
    SQLFreeStmt(hstmt_, SQL_UNBIND);
    /* restore stmt attr */
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROW_BIND_TYPE, (SQLPOINTER)old_row_bind_type_, 0);
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROW_ARRAY_SIZE, (SQLPOINTER)old_row_array_size_, 0);
    SQLSetStmtAttr(hstmt_, SQL_ATTR_ROWS_FETCHED_PTR, (SQLPOINTER)old_rows_fetched_ptr_, 0);
    hstmt_ = 0;
}

////////////////////////////////////////////////////////////////////////

struct column_desc {
    column_desc();
    ~column_desc();

    // fields coming from describe col
    SQLCHAR sql_name_[300];
    SQLSMALLINT sql_type_;  // type returned in SQLDescribeCol.
    SQLULEN sql_size_;
    SQLSMALLINT sql_decimal_;
    SQLSMALLINT sql_nullable_;

    // type info
    PyArray_Descr *npy_type_descr_;  // type to be used in NumPy
    int sql_c_type_;                 // c_type to be use when binding the column.

    // buffers used
    PyArrayObject *npy_array_;        // the numpy array that will hold the result
    PyArrayObject *npy_array_nulls_;  // the boolean numpy array holding null information
    void *scratch_buffer_;            // source buffer when it needs conversion
    SQLLEN *null_buffer_;
    SQLLEN element_buffer_size_;
};

column_desc::column_desc()
    : npy_type_descr_(0),
      npy_array_(0),
      npy_array_nulls_(0),
      scratch_buffer_(0),
      null_buffer_(0),
      element_buffer_size_(0)
{
}

column_desc::~column_desc()
{
    if (null_buffer_) {
        free(null_buffer_);
    }

    if (scratch_buffer_) {
        free(scratch_buffer_);
    }

    Py_XDECREF(npy_array_nulls_);
    Py_XDECREF(npy_array_);
    Py_XDECREF(npy_type_descr_);
}

inline PyArray_Descr *
dtype_from_string(const char *dtype_str_spec)
/*
  returns a dtype (PyArray_Descr) built from a string that describes it
*/
{
    PyObject *python_str = Py_BuildValue("s", dtype_str_spec);
    if (python_str) {
        PyArray_Descr *dtype = 0;
        PyArray_DescrConverter(python_str, &dtype);
        Py_DECREF(python_str);
        return dtype;
    }
    return 0;
}

inline PyArray_Descr *
string_dtype(size_t length)
{
    PyArray_Descr *result = PyArray_DescrNewFromType(NPY_STRING);
    if (result) {
        PyDataType_SET_ELSIZE(result, static_cast<int>(length + 1) * sizeof(char));
    }
    return result;
}

inline PyArray_Descr *
unicode_dtype(size_t length)
{
    PyArray_Descr *result = PyArray_DescrNewFromType(NPY_UNICODE);
    if (result) {
        PyDataType_SET_ELSIZE(result, static_cast<int>(length + 1) * sizeof(npy_ucs4));
    }
    return result;
}

/**
 * @brief Coerce the column to the given dtype, without considering how the database stores the data.
 *
 * See the table at https://learn.microsoft.com/en-us/sql/odbc/reference/appendixes/c-data-types?view=sql-server-ver16
 * and compare to https://numpy.org/doc/stable/user/basics.types.html
 *
 * @param cd Column descriptor containing data about the column
 * @param unicode If true, string types are all treated as unicode (they use the SQL_C_WCHAR type)
 * @param descr dtype descriptor to use for the column; must not be NULL. Steals a reference
 * to descr, as it gets stored on column_desc
 * @return 0 if successful, nonzero otherwise
 */
int coerce_column_desc_types(column_desc &cd, bool unicode, PyArray_Descr *descr) {
    cd.npy_type_descr_ = descr;
    Py_INCREF(descr);

    switch (descr->type_num) {
        case NPY_STRING:
            cd.sql_c_type_ = SQL_C_BINARY;
            PyDataType_SET_ELSIZE(
                descr,
                static_cast<npy_int>(cd.sql_size_)
            );
            cd.element_buffer_size_ = PyDataType_ELSIZE(descr);
            break;
        case NPY_UNICODE:
            cd.sql_c_type_ = SQL_C_WCHAR;
            PyDataType_SET_ELSIZE(
                descr,
                static_cast<npy_int>(cd.sql_size_)
            );
            cd.element_buffer_size_ = PyDataType_ELSIZE(descr);
            break;
        case NPY_INT8:
            cd.sql_c_type_ = SQL_C_STINYINT;
            break;
        case NPY_INT16:
            cd.sql_c_type_ = SQL_C_SSHORT;
            break;
        case NPY_INT32:
            cd.sql_c_type_ = SQL_C_SLONG;
            break;
        case NPY_INT64:
            cd.sql_c_type_ = SQL_C_SBIGINT;
            break;
        case NPY_UINT8:
            cd.sql_c_type_ = SQL_C_UTINYINT;
            break;
        case NPY_UINT16:
            cd.sql_c_type_ = SQL_C_USHORT;
            break;
        case NPY_UINT32:
            cd.sql_c_type_ = SQL_C_ULONG;
            break;
        case NPY_UINT64:
            cd.sql_c_type_ = SQL_C_UBIGINT;
            break;
        case NPY_FLOAT:
            cd.sql_c_type_ = SQL_C_FLOAT;
            break;
        case NPY_DOUBLE:
            cd.sql_c_type_ = SQL_C_DOUBLE;
            break;
        default:
            return 1;
    }
    return 0;
}

/**
 * @brief Infer the numpy type and the sql_c_type to use from the sql_type.
 *
 * @param cd Column descriptor
 * @param unicode If true, unicode is assumed and all character-like types are treated as unicde
 * @param descr Numpy dtype descriptor to be used; if NULL, the old style type inference is used
 * @return
 */
int
map_column_desc_types(column_desc &cd, bool unicode)
{
    PyArray_Descr *dtype = 0;
    size_t sql_size = cd.sql_size_;

    switch (cd.sql_type_) {
        // string types ------------------------------------------------
        case SQL_CHAR:
        case SQL_VARCHAR:
        case SQL_LONGVARCHAR:
        case SQL_GUID:
        case SQL_SS_XML:
            if (!unicode) {
                dtype = string_dtype(limit_text_size(sql_size));
                if (dtype) {
                    cd.element_buffer_size_ = PyDataType_ELSIZE(dtype);
                    cd.npy_type_descr_ = dtype;
                    cd.sql_c_type_ = SQL_C_CHAR;
                    return 0;
                }
                break;
            }
            // else: fallthrough

        case SQL_WCHAR:
        case SQL_WVARCHAR:
        case SQL_WLONGVARCHAR: {
            dtype = unicode_dtype(limit_text_size(sql_size));
            if (dtype) {
                cd.element_buffer_size_ = PyDataType_ELSIZE(dtype);
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_WCHAR;
                return 0;
            }
        } break;

        // real types --------------------------------------------------
        case SQL_REAL:
            dtype = PyArray_DescrFromType(NPY_FLOAT);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_FLOAT;
                return 0;
            }
            break;

        case SQL_FLOAT:
        case SQL_DOUBLE:
            dtype = PyArray_DescrFromType(NPY_DOUBLE);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_DOUBLE;
                return 0;
            }
            break;

        // integer types -----------------------------------------------
        case SQL_BIT:
            dtype = PyArray_DescrFromType(NPY_BOOL);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_BIT;
                return 0;
            }
            break;

        case SQL_TINYINT:
            dtype = PyArray_DescrFromType(NPY_UINT8);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_TINYINT;
                return 0;
            }
            break;

        case SQL_SMALLINT:
            dtype = PyArray_DescrFromType(NPY_INT16);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_SSHORT;
                return 0;
            }
            break;

        case SQL_INTEGER:
            dtype = PyArray_DescrFromType(NPY_INT32);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_SLONG;
                return 0;
            }
            break;

        case SQL_BIGINT:
            dtype = PyArray_DescrFromType(NPY_INT64);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_SBIGINT;
                return 0;
            }
            break;

        // time related types ------------------------------------------
        case SQL_TYPE_DATE:
            if (CAN_USE_DATETIME) {
                dtype = dtype_from_string("M8[D]");
                if (dtype) {
                    cd.npy_type_descr_ = dtype;
                    cd.sql_c_type_ = SQL_C_TYPE_DATE;
                    return 0;
                }
            }
            break;

        case SQL_TYPE_TIME:
        case SQL_SS_TIME2:
            if (CAN_USE_DATETIME) {
                dtype = dtype_from_string("m8[s]");
                if (dtype) {
                    cd.npy_type_descr_ = dtype;
                    cd.sql_c_type_ = SQL_C_TYPE_TIME;
                    return 0;
                }
            }
            break;

        case SQL_TYPE_TIMESTAMP:
            if (CAN_USE_DATETIME) {
                dtype = dtype_from_string("M8[us]");
                if (dtype) {
                    cd.npy_type_descr_ = dtype;
                    cd.sql_c_type_ = SQL_C_TYPE_TIMESTAMP;
                    return 0;
                }
            }
            break;

        // decimal -----------------------------------------------------
        // Note: these are mapped as double as per a request
        //       this means precision may be lost.
        case SQL_DECIMAL:
        case SQL_NUMERIC:
            dtype = PyArray_DescrFromType(NPY_DOUBLE);
            if (dtype) {
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_DOUBLE;
                return 0;
            }
            break;

        // Binary data types. These are null-padded bytestrings with a maximum
        // length fixed by the length of the longest bytestring in the array.
        // https://numpy.org/doc/stable/reference/c-api/dtype.html#c.NPY_TYPES.NPY_STRING
        case SQL_BINARY:
        case SQL_VARBINARY:
        case SQL_LONGVARBINARY:
            dtype = PyArray_DescrFromType(NPY_STRING);
            if (dtype != NULL) {
                // Set the element size for numpy
                PyDataType_SET_ELSIZE(
                    dtype,
                    static_cast<npy_int>(cd.sql_size_)
                );

                // Set the element size that gets passed to SQLBindCol
                cd.element_buffer_size_ = PyDataType_ELSIZE(dtype);
                cd.npy_type_descr_ = dtype;
                cd.sql_c_type_ = SQL_C_BINARY;
                return 0;
            }
        default:
            break;
    }

    return 1;
}

struct query_desc {
    SQLRETURN init_from_statement(SQLHSTMT hstmt);
    SQLRETURN bind_cols();

    void lowercase_fields();
    int translate_types(bool use_unicode, PyObject *target_dtype, int &unsupported_fields);
    int ensure();
    int convert(size_t read);
    void advance(size_t read);

    int allocate_buffers(size_t initial_result_count, size_t chunk_size, bool keep_nulls);
    int resize(size_t new_count);
    void cleanup();

    query_desc() : allocated_results_count_(0), chunk_size_(0), offset_(0) {}

    std::vector<column_desc> columns_;
    size_t allocated_results_count_;
    size_t chunk_size_;
    size_t offset_;
    SQLHSTMT hstmt_;
};

/*
  Fill the column descriptor from the sql statement handle hstmt.

  returns SQL_SUCCESS if successful, otherwise it returns the
  SQLRESULT from the SQL command that failed.
*/
SQLRETURN
query_desc::init_from_statement(SQLHSTMT hstmt)
{
    cleanup();

    hstmt_ = hstmt;

    SQLRETURN ret;
    SQLSMALLINT field_count = 0;

    ret = SQLNumResultCols(hstmt, &field_count);

    if (!SQL_SUCCEEDED(ret)) {
        return ret;
    }

    columns_.resize(field_count);
    // columns are 1 base on ODBC...
    for (SQLSMALLINT field = 1; field <= field_count; field++) {
        column_desc &c_desc = columns_[field - 1];
        ret = SQLDescribeCol(
            hstmt,
            field,
            &c_desc.sql_name_[0],
            _countof(c_desc.sql_name_), // Max column name size is 300
            NULL,
            &c_desc.sql_type_,
            &c_desc.sql_size_, // Maximum string length that can be stored in the column
            &c_desc.sql_decimal_,
            &c_desc.sql_nullable_
        );

        if (!SQL_SUCCEEDED(ret)) {
            return ret;
        }
    }

    return SQL_SUCCESS;
}

SQLRETURN
query_desc::bind_cols()
{
    SQLUSMALLINT col_number = 1;

    for (std::vector<column_desc>::iterator it = columns_.begin(); it < columns_.end(); ++it) {
        void *bind_ptr;
        if (it->scratch_buffer_) {
            bind_ptr = it->scratch_buffer_;
        }
        else {
            PyArrayObject *array = it->npy_array_;
            bind_ptr = static_cast<void *>(PyArray_BYTES(array) +
                                           (this->offset_ * PyArray_ITEMSIZE(array)));
        }

        SQLRETURN status = SQLBindCol(
            hstmt_,
            col_number,
            it->sql_c_type_,
            bind_ptr,
            it->element_buffer_size_,
            it->null_buffer_
        );
        if (!SQL_SUCCEEDED(status)) {
            return status;
        }

        col_number++;
    }

    return SQL_SUCCESS;
}

/*
  Converts all the field names to lowercase
*/
void
query_desc::lowercase_fields()
{
    for (std::vector<column_desc>::iterator it = columns_.begin(); it < columns_.end(); ++it) {
        _strlwr((char *)&it->sql_name_[0]);
    }
}

/**
 * @brief Map the SQL types to numpy dtype and C type.
 *
 * @param use_unicode If true, unicode is assumed and all character-like types are treated as unicode
 * @param target_dtypes A python dictionary of {column name: numpy dtype}
 * @param unsupported_fields An integer which will be written with the number of unsupported columns
 * @return 0 if successful, -1 if an error occurred; the Python error indicator will be set
 */
int
query_desc::translate_types(bool use_unicode, PyObject *target_dtypes, int &unsupported_fields)
{
    if (target_dtypes == NULL) {
        for (auto &column: this->columns_) {
            unsupported_fields += map_column_desc_types(column, use_unicode);
        }
    } else {
        if (!PyDict_Check(target_dtypes)) {
            PyErr_SetString(
                PyExc_ValueError,
                "target_dtypes must be a dictionary of {column name: dtype}"
            );
            return -1;
        }

        PyArray_Descr *descr = NULL;

        for (auto &column: this->columns_) {
            PyObject *target_dtype = PyDict_GetItemString(
                target_dtypes,
                reinterpret_cast<const char *>(column.sql_name_)
            );
            if (target_dtype == NULL) {
                unsupported_fields += map_column_desc_types(column, use_unicode);
            } else {
                int conversion_result = PyArray_DescrConverter(target_dtype, &descr);

                // Sometimes PyArray_DescrConverter returns < 0 to indicate errors, other
                // times it doesn't but descr == NULL. In either case, we need to do error handling.
                if (conversion_result < 0 || descr == NULL) {
                    // Get the string representation of the requested dtype
                    PyObject *target_dtype_str = PyObject_Str(target_dtype);
                    if (target_dtype_str == NULL) {
                        PyErr_Format(
                            PyExc_TypeError,
                            "Invalid dtype for column '%s'; cannot print dtype due to error calling __str__.",
                            column.sql_name_
                        );
                        Py_XDECREF(descr);
                        return -1;
                    }

                    // Convert the python string to a unicode const char *
                    const char *str = PyUnicode_AsUTF8(target_dtype);
                    if (str == NULL) {
                        PyErr_Format(
                            PyExc_TypeError,
                            "Invalid dtype for column '%s'; error getting the unicode representation of str(<requested dtype>)",
                            column.sql_name_
                        );
                        Py_DECREF(target_dtype_str);
                        Py_XDECREF(descr);
                        return -1;
                    }

                    // Print the error string
                    PyErr_Format(
                        PyExc_TypeError,
                        "Invalid dtype '%s' for column '%s'",
                        str,
                        column.sql_name_
                    );
                    Py_DECREF(target_dtype_str);
                    Py_XDECREF(descr);
                    return -1;
                }
                // coerce_column_desc_types takes ownership of descr; no Py_DECREF needed
                unsupported_fields += coerce_column_desc_types(column, use_unicode, descr);
            }
        }
    }
    return 0;
}

/**
 * @brief Allocate buffers to execute the query.
 *
 * If the number of rows to fetch < 0, buffer_element_count and chunk_element_count are set to
 * DEFAULT_ROWS_TO_BE_ALLOCATE and DEFAULT_ROWS_TO_BE_FETCHED respectively, and can thus be
 * different. Otherwise they are the same number.
 *
 * @param buffer_element_count Initial rows to preallocate for the results
 * @param chunk_element_count Rows to allocate for "per-chunk" buffers
 * @param keep_nulls
 * @return The number of failed allocations.
 */
int
query_desc::allocate_buffers(
    size_t buffer_element_count,
    size_t chunk_element_count,
    bool keep_nulls
) {
    int alloc_errors = 0;
    npy_intp npy_array_count = static_cast<npy_intp>(buffer_element_count);

    for (std::vector<column_desc>::iterator it = columns_.begin(); it < columns_.end(); ++it) {
        // Allocate the numpy buffer for the result; only one dimension is needed here, and it is
        // of size npy_array_count.
        PyObject *arr = PyArray_SimpleNewFromDescr(1, &npy_array_count, it->npy_type_descr_);
        if (!arr) {
            // failed to allocate mem_buffer
            alloc_errors++;
            continue;
        }
        PyArrayObject *array = reinterpret_cast<PyArrayObject *>(arr);

        if (PyArray_ISSTRING(array)) {
            // clear memory on strings or undefined
            memset(PyArray_BYTES(array), 0, buffer_element_count * PyArray_ITEMSIZE(array));
        }

        it->npy_array_ = array;

        if (!arr) {
            alloc_errors++;
        }

        // SimpleNewFromDescr steals the reference for the dtype
        Py_INCREF(it->npy_type_descr_);
        // if it is a type that needs to perform conversion,
        // allocate a buffer for the data to be read in.
        //
        // TODO: make the type logic decide what size per element
        // it needs (if any).  this will make the logic about
        // conversion simpler.
        switch (it->sql_c_type_) {
            case SQL_C_TYPE_DATE: {
                void *mem = malloc(chunk_element_count * sizeof(DATE_STRUCT));
                it->scratch_buffer_ = mem;
                if (!mem) {
                    alloc_errors++;
                }
            } break;
            case SQL_C_TYPE_TIMESTAMP: {
                void *mem = malloc(chunk_element_count * sizeof(TIMESTAMP_STRUCT));
                it->scratch_buffer_ = mem;
                if (!mem) {
                    alloc_errors++;
                }
            } break;
            case SQL_C_TYPE_TIME: {
                void *mem = malloc(chunk_element_count * sizeof(TIME_STRUCT));
                it->scratch_buffer_ = mem;
                if (!mem) {
                    alloc_errors++;
                }
            } break;
            case SQL_C_WCHAR: {
                // this case is quite special, as a scratch
                // buffer/conversions will only be needed when the
                // underlying ODBC manager does not use UCS4 for
                // its unicode strings.
                //
                // - MS ODBC manager uses UTF-16, which may
                //   include surrogates (thus variable length encoded).
                //
                // - unixODBC seems to use UCS-2, which is
                //   compatible with UTF-16, but may not include
                //   surrogates limiting encoding to Basic
                //   Multilingual Plane (not sure about this, it
                //   will be handled using the same codepath as MS
                //   ODBC, so it will work even if it produces
                //   surrogates).
                //
                // - iODBC uses UCS-4 (UTF-32), so it shouldn't
                //   need any kind of translation.
                //
                // In order to check if no translation is needed, the
                // size of SQLWCHAR is used.
                if (sizeof(SQLWCHAR) == 2) {
                    size_t item_count = PyArray_ITEMSIZE(it->npy_array_) / sizeof(npy_ucs4);
                    // 2 due to possibility of surrogate.
                    // doing the math, the final buffer could be used instead of a
                    // scratch buffer, but would require code that can do the conversion
                    // in-place.
                    void *mem =
                            malloc(chunk_element_count * item_count * sizeof(SQLWCHAR) * 2);
                    it->scratch_buffer_ = mem;
                    if (!mem) {
                        alloc_errors++;
                    }
                }
            } break;
            default:
                break;
        }

        if (it->sql_nullable_) {
            // if the type is nullable, allocate a buffer for null
            // data (ODBC buffer, that has SQLLEN size)
            void *mem = malloc(chunk_element_count * sizeof(SQLLEN));
            it->null_buffer_ = static_cast<SQLLEN *>(mem);
            if (!mem) {
                alloc_errors++;
            }

            if (keep_nulls) {
                // also allocate a numpy array for bools if null data is wanted
                arr = PyArray_SimpleNew(1, &npy_array_count, NPY_BOOL);
                it->npy_array_nulls_ = reinterpret_cast<PyArrayObject *>(arr);
                if (!it->npy_array_nulls_) {
                    alloc_errors++;
                }
            }
        }
    }

    if (!alloc_errors) {
        allocated_results_count_ = buffer_element_count;
        chunk_size_ = chunk_element_count;
    }

    return alloc_errors;
}

/*
  resize the numpy array elements to the new_size.
  the chunk_size and associated buffers are to be preserved.
 */
int
query_desc::resize(size_t new_size)
{
    int alloc_fail = 0;
    npy_intp size = static_cast<npy_intp>(new_size);
    for (std::vector<column_desc>::iterator it = columns_.begin(); it < columns_.end(); ++it) {
        int failed = resize_array(it->npy_array_, size);

        // if it has an array for nulls, resize it as well
        if (it->npy_array_nulls_) {
            failed += resize_array(it->npy_array_nulls_, size);
        }

        if (failed) {
            alloc_fail += failed;
        }
    }

    if (!alloc_fail) {
        allocated_results_count_ = new_size;
    }

    return alloc_fail;
}

/*
  make sure there is space allocated for the next step
  return 0 if everything ok, any other value means a problem was found
  due to resizing
 */
int
query_desc::ensure()
{
    if (allocated_results_count_ < offset_ + chunk_size_) {
        return resize(offset_ + chunk_size_);
    }

    return 0;
}

/*
  Converts any column that requires conversion from the type returned
  by ODBC to the type expected in NumPy. Right now this is only needed
  for fields related to time. Note that ODBC itself may handle other
  conversions, like decimal->double with the appropriate SQLBindCol.

  The conversion also includes the handling of nulls. In the case of
  NULL a default value is inserted in the resulting column.
 */
int
query_desc::convert(size_t count)
{
    for (std::vector<column_desc>::iterator it = columns_.begin(); it < columns_.end(); ++it) {
        // TODO: It should be possible to generalize this and make it
        //       more convenient to add types if a conversion function
        //       was placed in the column structure.
        //       Probably nulls could be handled by that conversion
        //       function as well.
        if (it->scratch_buffer_) {  // a conversion is needed
            convert_buffer(it->npy_array_, it->scratch_buffer_, it->sql_c_type_, this->offset_, count);
        }

        // When used with SQLFetchScroll (as is the case here), SQLBindCol can set values in
        // the `null_buffer_` to one of the following:
        // - The length of the data available to return
        // - SQL_NO_TOTAL (length of data is unknown)
        // - SQL_NULL_DATA (no data was returned)
        if (it->null_buffer_) {
            if (
                fill_NAarray(
                    it->npy_array_,
                    it->npy_array_nulls_,
                    it->null_buffer_,
                    this->offset_,
                    count
                ) < 0
            ) {
                return -1;
            }
        }
    }
    return 0;
}

/*
  Advance the current position
 */
void
query_desc::advance(size_t count)
{
    offset_ += count;
}

void
query_desc::cleanup()
{
    std::vector<column_desc> tmp;
    columns_.swap(tmp);
}

}  // namespace

size_t
print_error_types(query_desc &qd, size_t err_count, char *buff, size_t buff_size)
{
    size_t acc =
            snprintf(buff, buff_size, "%d fields with unsupported types found:\n", (int)err_count);

    for (std::vector<column_desc>::iterator it = qd.columns_.begin(); it < qd.columns_.end();
         ++it) {
        if (0 == it->npy_type_descr_) {
            // if numpy type descr is empty means a failed translation.
            acc += snprintf(buff + acc, acc < buff_size ? buff_size - acc : 0,
                            "\t'%s' type: %s (%d) size: %d decimal: %d\n", it->sql_name_,
                            sql_type_to_str(it->sql_type_), (int)it->sql_type_, (int)it->sql_size_,
                            (int)it->sql_decimal_);
        }
    }

    return acc;
}

int
raise_unsupported_types_exception(int err_count, query_desc &qd)
{
    char error[4'096];
    char *use_string = error;
    size_t count = print_error_types(qd, err_count, error, sizeof(error));

    if (count >= sizeof(error)) {
        // did not fit, truncated
        char *error_alloc = (char *)malloc(count);
        if (error_alloc) {
            use_string = error_alloc;
            print_error_types(qd, count, error_alloc, count);
        }
    }

    RaiseErrorV(0, PyExc_TypeError, use_string);

    if (use_string != error) {
        // we had to allocate
        free(use_string);
    }
    return 0;
}

/**
 * @brief Create a python dictionary of numpy arrays from the ODBC cursor.
 *
 * @param result Query descriptor that stores the data fetched from the database
 * @param cur ODBC cursor pointing to data to fetch
 * @param nrows Number of rows to fetch
 * @param lower If true, make the column names all lowercase
 * @param want_nulls If true, null values are kept
 * @param target_dtypes A python dictionary of dtypes to cast the result to;
 * if unspecified, the old type inference behavior is used
 * @return 0 if no errors were encountered, nonzero otherwise
 */
static int
perform_array_query(query_desc &result, Cursor *cur, npy_intp nrows, bool lower, bool want_nulls, PyObject *target_dtypes)
{
    SQLRETURN rc;
    /* XXX is true a good default?
       was: bool use_unicode = cur->cnxn->unicode_results; */
    bool use_unicode = true;
    size_t outsize, chunk_size;

    if (nrows < 0) {
        // chunked, no know final size
        outsize = DEFAULT_ROWS_TO_BE_ALLOCATED;
        chunk_size = DEFAULT_ROWS_TO_BE_FETCHED;
    }
    else {
        // all in one go
        outsize = static_cast<size_t>(nrows);
        chunk_size = static_cast<size_t>(nrows);
    }

    assert(cur->hstmt != SQL_NULL_HANDLE && cur->colinfos != 0);

    if (cur->cnxn->hdbc == SQL_NULL_HANDLE) {
        /*
          Is this needed or just convenient?
          Won't ODBC fail gracefully (through an ODBC error code) when
          trying to use a bad handle?
         */
        return 0 == RaiseErrorV(0, ProgrammingError, "The cursor's connection was closed.");
    }

    {
        PyNoGIL ctxt;
        rc = result.init_from_statement(cur->hstmt);
    }

    if (cur->cnxn->hdbc == SQL_NULL_HANDLE) {
        // The connection was closed by another thread in the
        // ALLOW_THREADS block above.
        return 0 == RaiseErrorV(0, ProgrammingError, "The cursor's connection was closed.");
    }

    if (!SQL_SUCCEEDED(rc)) {
        // Note: The SQL Server driver sometimes returns HY007 here if
        // multiple statements (separated by ;) were submitted.  This
        // is not documented, but I've seen it with multiple
        // successful inserts.
        return 0 == RaiseErrorFromHandle(cur->cnxn, "ODBC failed to describe the resulting columns",
                                         cur->cnxn->hdbc, cur->hstmt);
    }

    if (lower) {
        result.lowercase_fields();
    }

    int unsupported_fields = 0;
    if (result.translate_types(use_unicode, target_dtypes, unsupported_fields) < 0) {
        return -1;
    }
    if (unsupported_fields > 0) {
        // TODO: add better diagnosis, pointing out the fields and
        // their types in a human readable form.
        return 0 == raise_unsupported_types_exception(unsupported_fields, result);
    }

    int allocation_errors = result.allocate_buffers(outsize, chunk_size, want_nulls);
    if (allocation_errors) {
        return 0 == RaiseErrorV(0, PyExc_MemoryError, "Can't allocate result buffers", outsize);
    }

    fetch_status status(cur->hstmt, result.chunk_size_);
    do {
        int error = result.ensure();
        if (error) {
            return 0 == RaiseErrorV(0, PyExc_MemoryError, "Can't allocate result buffers");
        }

        rc = result.bind_cols();
        if (!SQL_SUCCEEDED(rc)) {
            return 0 == RaiseErrorFromHandle(cur->cnxn, "ODBC failed when binding columns",
                                             cur->cnxn->hdbc, cur->hstmt);
        }

        // Do the fetch
        // According to the microsoft sql docs for SQLFetchScroll:
        //
        //    SQL_FETCH_NEXT 	Return the next rowset. This is equivalent to calling
        //                      SQLFetch.
        //                      SQLFetchScroll ignores the value of FetchOffset.
        //
        // Why is this used here?
        {
            PyNoGIL ctxt;
            rc = SQLFetchScroll(status.hstmt_, SQL_FETCH_NEXT, 0);
        }

        // Sometimes (test_exhaust_execute_buffer), the SQLite ODBC
        // driver returns an error here, but it should not!  I'm not
        // sure that this solution is the correct one, but anyway.
        if ((rc == SQL_NO_DATA) || (rc == -1)) {  // XXX
            break;
        }
        else if (rc < 0) {
            PyErr_SetString(PyExc_RuntimeError, "error in SQLFetchScroll");
            return rc;
        }

        // The next check creates false positives on SQLite, as the
        // NumRowsFetched seems arbitrary (i.e. not set).  Probably
        // reveals a problem in the ODBC driver.
        if (status.rows_read_ > static_cast<SQLLEN>(result.chunk_size_)) {
            // The rows read reported is greater than requested. Let's reset its
            // value to 0 instead (the most probable value here)
            status.rows_read_ = 0;
        }

        if (result.convert(status.rows_read_) < 0) {
            return -1;
        }
        result.advance(status.rows_read_);

        // This exits the loop when the amount of rows was known
        // a-priori, so it is enough with a single call
        if (nrows >= 0) {
            break;
        }

        // We assume that when the number of rows read is lower than
        // the number we asked for, this means we are done.
    } while (status.rows_read_ == static_cast<SQLLEN>(result.chunk_size_));

    // Finally, shrink size of final container, if needed
    if (result.offset_ < result.allocated_results_count_) {
        int alloc_failures = result.resize(result.offset_);
        if (alloc_failures) {
            // note that this shouldn't be happening, as a shrinking realloc
            // should always succeed!
            return 0 == RaiseErrorV(0, PyExc_MemoryError, "Can't allocate result buffers");
        }
    }
    return 0;
}

/**
 * @brief Build a dictionary of numpy arrays from the a query descriptor.
 *
 * @param qd Query descriptor containing query results
 * @param null_suffix Suffix to add to the column name for the bool column holding any
 * nulls. NULL means null values are not returned
 * @return A python dictionary filled with numpy arrays
 */
static PyObject *
query_desc_to_dictarray(query_desc &qd, const char *null_suffix)
{
    PyObject *dictarray = PyDict_New();
    if (dictarray == NULL) {
        return PyErr_NoMemory();
    }

    int rv;
    for (
        std::vector<column_desc>::iterator it = qd.columns_.begin();
        it < qd.columns_.end();
        ++it
    ) {
        rv = PyDict_SetItemString(
            dictarray,
            reinterpret_cast<char *>(it->sql_name_),
            reinterpret_cast<PyObject *>(it->npy_array_)
        );

        if (rv < 0) {
            // PyDict_SetItemString will set the error indicator if something goes
            // wrong; just return NULL.
            Py_DECREF(dictarray);
            return NULL;
        }

        if (it->npy_array_nulls_) {
            char column_nulls_name[350];
            snprintf(column_nulls_name, sizeof(column_nulls_name), "%s%s", it->sql_name_,
                     null_suffix);
            rv = PyDict_SetItemString(dictarray, column_nulls_name,
                                      reinterpret_cast<PyObject *>(it->npy_array_nulls_));
            if (rv < 0) {
                Py_DECREF(dictarray);
                return NULL;
            }
        }
    }

    return dictarray;
}

/**
 * @brief Create and fill a dictionary of numpy arrays from a SQL query.
 *
 * @param cursor Cursor to fetch the rows from
 * @param nrows Number of rows to fetch; if nrows = -1, all rows are fetched
 * @param null_suffix Suffix to add to the column name for the bool column holding the
 * nulls; NULL means nulls are not returned
 * @param target_dtypes A python dictionary containing numpy dtypes to use for the columns
 * @return A Python dictionary filled with numpy arrays
 */
static PyObject *
create_fill_dictarray(Cursor *cursor, npy_intp nrows, const char *null_suffix, PyObject *target_dtypes)
{
    query_desc qd;
    if (perform_array_query(qd, cursor, nrows, lowercase(), null_suffix != 0, target_dtypes) != 0) {
        return NULL;
    }
    return query_desc_to_dictarray(qd, null_suffix);
}

static const char *Cursor_npfetch_kwnames[] = {
    "size",          // keyword to read the maximum number of rows. Defaults to all.
    "return_nulls",  // keyword to make a given fetch to add boolean columns for
                     // nulls
    "null_suffix",   // keyword providing the string to use as suffix
    "target_dtypes", // dict of numpy dtypes to use for each column
    NULL
};

/**
 * @brief Underlying fetchdictarray method which turns SQL query results into a dict of arrays.
 *
 * @param self Cursor which has been queried, and has results waiting to be read
 * @param args Python arguments; see Cursor_npfetch_kwnames for valid arguments
 * @param kwargs Python keyword arguments; see Cursor_npfetch_kwnames for valid arguments
 * @return A dictionary containing {column name: np.ndarray} key value pairs
 */
PyObject *
Cursor_fetchdictarray(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *numpy = PyImport_ImportModule("numpy");
    if (!numpy) {
        return NULL;
    }
    Cursor *cursor = Cursor_Validate(self, CURSOR_REQUIRE_RESULTS | CURSOR_RAISE_ERROR);
    if (!cursor) {
        Py_DECREF(numpy);
        return NULL;
    }

    Py_ssize_t nrows = -1;
    bool return_nulls = false;
    const char *null_suffix = "_isnull";
    PyObject *target_dtypes = NULL;

    if (
        !PyArg_ParseTupleAndKeywords(
            args,
            kwargs,
            "|npsO",
            const_cast<char **>(Cursor_npfetch_kwnames),
            &nrows,
            &return_nulls,
            &null_suffix,
            &target_dtypes
        )
    ) {
        Py_DECREF(numpy);
        return NULL;
    }

    // Initialize numpy function pointer table so the C-API can be used
    import_array();
    if (PyArray_GetNDArrayCFeatureVersion() >= 7) {
        CAN_USE_DATETIME = true;
    }

    PyObject *dictarr = create_fill_dictarray(cursor, nrows, return_nulls ? null_suffix : 0, target_dtypes);
    Py_DECREF(numpy);
    return dictarr;
}

char fetchdictarray_doc[] =
        "fetchdictarray(size=-1, return_nulls=False, null_suffix='_isnull', target_dtypes=None)\n"
        "                               --> a dictionary of column arrays.\n"
        "\n"
        "Fetch as many rows as specified by size into a dictionary of NumPy\n"
        "ndarrays (dictarray). The dictionary will contain a key for each column,\n"
        "with its value being a NumPy ndarray holding its value for the fetched\n"
        "rows. Optionally, extra columns will be added to signal nulls on\n"
        "nullable columns.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "size : int, optional\n"
        "    The number of rows to fetch. Use -1 (the default) to fetch all\n"
        "    remaining rows.\n"
        "return_nulls : boolean, optional\n"
        "    If True, information about null values will be included adding a\n"
        "    boolean array using as key a string  built by concatenating the\n"
        "    column name and null_suffix.\n"
        "target_dtypes : dict, optional\n"
        "    If provided, this mapping between {column name: dtype} coerces \n"
        "    the values read from the database into arrays of the requested\n"
        "    dtypes.\n"
        "null_suffix : string, optional\n"
        "    A string used as a suffix when building the key for null values.\n"
        "    Only used if return_nulls is True.\n"
        "\n"
        "Returns\n"
        "-------\n"
        "out: dict\n"
        "    A dictionary mapping column names to an ndarray holding its values\n"
        "    for the fetched rows. The dictionary will use the column name as\n"
        "    key for the ndarray containing values associated to that column.\n"
        "    Optionally, null information for nullable columns will be provided\n"
        "    by adding additional boolean columns named after the nullable column\n"
        "    concatenated to null_suffix\n"
        "\n"
        "Remarks\n"
        "-------\n"
        "Similar to fetchmany(size), but returning a dictionary of NumPy ndarrays\n"
        "for the results instead of a Python list of tuples of objects, reducing\n"
        "memory footprint as well as improving performance.\n"
        "fetchdictarray is overall more efficient that fetchsarray.\n"
        "\n"
        "See Also\n"
        "--------\n"
        "fetchmany : Fetch rows into a Python list of rows.\n"
        "fetchall : Fetch the remaining rows into a Python list of rows.\n"
        "\n";
