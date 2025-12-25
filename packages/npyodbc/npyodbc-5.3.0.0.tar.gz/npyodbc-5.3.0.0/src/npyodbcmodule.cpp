#include <Python.h>
#include "methodobject.h"
#include "modsupport.h"
#include "pyodbc.h"
#include "wrapper.h"
#include "textenc.h"
#include "connection.h"
#include "pyodbcmodule.h"

#include "numpy/numpyconfig.h"
#include <sql.h>
#include <sqlext.h>

// Set declaration for the pyodbc initialization function
// defined in pyodbcmodule.h -> pyodbcmodule.cpp
extern "C" {
PyMODINIT_FUNC
PyInit_pyodbc();
}

PyMODINIT_FUNC
PyInit_npyodbc(void)
{
    // Initialize the pyodbc module, and just return that. Adding additional methods
    // to the module can be done here.
    // PyObject *module = PyInit_pyodbc();
    PyInit_pyodbc();

    if (pModule == NULL) {
        PyErr_SetString(PyExc_ImportError, "Error initializing pyodbc.");
        return NULL;
    }

    // Add the numpy ABI version this package was compiled against
    PyModule_AddIntConstant(
        pModule,
        "numpy_abi_version",
        NPY_VERSION
    );

    return pModule;
}
