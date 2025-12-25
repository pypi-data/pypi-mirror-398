---
sidebar_position: 2
---

# Creating a table

Creating a table using npyodbc.

We will assume you have the `iPython` REPL installed. If not, install it using the
`.[dev,test]` command line flags if installing npyodbc from a locally cloned git repo,
or your favorite method for doing so.

```python showLineNumbers
import pyodbc

driver = "ODBC Driver 17 for SQL Server"
server = "localhost,1401"
uid = "SA"
# NOTE: This is not secure and should not be used only for testing purposes.
pwd = "StrongPassword2022!"
connection_string = f"DRIVER={driver};SERVER={server};UID={uid};PWD={pwd}"
# Connect to the database running in Docker, or in the VSCode devcontainer.
connection = pyodbc.connect(connection_string)

# Create a test table.
with connection as conn:
    try:
        conn.execute("DROP TABLE test;")
    except ProgrammingError:
        print("Table `test` already exists.")
with connection as conn:
    conn.execute("CREATE TABLE test (columnA VARBINARY(20), columnB VARBINARY(20));")

# Add data to the test table.
with connection as conn:
    conn.execute(
        "INSERT INTO test "
        "VALUES(CAST('zort' AS VARBINARY(20)), CAST('troz' AS VARBINARY(20)));"
    )
    conn.execute(
        "INSERT INTO test "
        "VALUES(CAST('poit' AS VARBINARY(20)), CAST('rubber pants' AS VARBINARY(20)));"
    )

# Retrieve the data from the test table.
connection.execute("SELECT * FROM test;").fetchall()
```

We have used the `with` context in Python for executing commands to the connected
database. If you want, you can also create a cursor with the statement to execute, and
then commit the command to the connection, example below.

```python showLineNumbers
import pyodbc

driver = "ODBC Driver 17 for SQL Server"
server = "localhost,1401"
uid = "SA"
# NOTE: This is not secure and should not be used only for testing purposes.
pwd = "StrongPassword2022!"
connection_string = f"DRIVER={driver};SERVER={server};UID={uid};PWD={pwd}"
# Connect to the database running in Docker, or in the VSCode devcontainer.
connection = pyodbc.connect(connection_string)

# Create a cursor
cursor = connection.cursor()
sql = "CREATE TABLE test (columnA VARBINARY(20), columnB VARBINARY(20));"
cursor.execute(sql)
connection.commit()
```

## sqlcmd

If you want to use `sqlcmd` to create the table, you can do so. You will need to log
into Docker container, or use the terminal in the VSCode devcontainer.

```bash showLineNumbers
# Change directory to the tool
cd /opt/mssql-tools/bin
# Start the sqlcmd tool
./sqlcmd -S localhost -U SA -P StrongPassword2022!
```

Below we will create a test table and add data to it.

```sql showLineNumbers
1> CREATE TABLE test (columnA VARBINARY(20), columnB VARBINARY(20));
2> INSERT INTO test VALUES(CAST('zort' AS VARBINARY(20)), CAST('troz' AS VARBINARY(20)));
3> INSERT INTO test VALUES(CAST('poit' AS VARBINARY(20)), CAST('rubber pants' AS VARBINARY(20)));
4> GO;
```

Finally we can query the table.

```sql showLineNumbers
1> SELECT * FROM test;
```

```bash
columnA                                    columnB
------------------------------------------ ------------------------------------------
0x7A6F7274                                 0x74726F7A
0x706F6974                                 0x7275626265722070616E7473

```

Note that what is returned is `BINARY`. If you want the string representation of what is
in the table, you need to convert it.

```sql showLineNumbers
1> SELECT CONVERT(VARCHAR(20), columnA) AS columnA,
2>        CONVERT(VARCHAR(20), columnB) AS columnB
3> FROM test;
2> GO;
```

```bash
columnA              columnB
-------------------- --------------------
zort                 troz
poit                 rubber pants
```
