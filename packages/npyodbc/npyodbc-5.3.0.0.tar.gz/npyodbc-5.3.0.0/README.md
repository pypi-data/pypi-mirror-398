# `npyodbc`

A python interface to Open Database Connectivity (ODBC) drivers built on top of
[`pyodbc`](https://github.com/mkleehammer/pyodbc) that incorporates native
support for `numpy`.

## Features

- Native support for `numpy` arrays
- Compatible with many ODBC drivers
- Can be used anywhere `pyodbc` is used

## Requirements

You'll need a database and an ODBC driver to use `npyodbc`. There are many
different options:

* Google BigQuery
* Hive from Ubuntu/Debian
* Microsoft Access
* Microsoft Excel
* Microsoft SQL Server
* MySQL
* Netezza
* Oracle
* PostgreSQL
* SQLite
* Teradata
* Vertica

Install the appropriate ODBC driver for the database you want to connect to
before continuing.

## Installation

You can install `npyodbc` via pip:

```sh
pip install npyodbc
```

### Development installation

If you've cloned this repository and want to work on it locally,

```sh
pip install -e .
```

### Development installation using conda

If you're using `conda`, use the included `environment.yaml` to install
requirements:

```bash
conda env create --file environment.yaml
conda activate npyodbc-dev
pip install -e .
```

## Usage

Let's set up a containerized database as an example (you'll need `docker` before
we begin):

1. Create a `docker-compose.yml` containing the following:

```docker-compose
services:
  postgres:
    image: postgres:11
    environment:
      - POSTGRES_DB=postgres_db
      - POSTGRES_USER=postgres_user
      - POSTGRES_PASSWORD=postgres_pwd
      - POSTGRES_HOST_AUTH_METHOD=trust

    ports:
      - "5432:5432"
```

2. Start the container: `docker compose up --build`
3. Configure your ODBC driver by setting `/etc/odbc.ini`:

```ini
[PostgreSQL Unicode]
Description = PostgreSQL connection to database
Driver = PostgreSQL Unicode
Servername = localhost
Port = 5432
Database = postgres_db
Username = postgres_user
Password = postgres_pwd
```

We also need to configure `/etc/odbcinst.ini`:

```ini
[PostgreSQL Unicode]
Description = PostgreSQL ODBC driver (Unicode)
Driver = /usr/lib/psqlodbcw.so
```

Now your system is ready to connect.

3.  Create a database to connect to:

```bash
# Set your environment to match the settings in the container
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=postgres_db
export PGUSER=postgres_user
export PGPASSWORD=postgres_pwd

# Create a new database
psql -c "CREATE DATABASE test WITH encoding='UTF8' LC_COLLATE='en_US.utf8' LC_CTYPE='en_US.utf8'"
```

4. Connect with `npyodbc`:

```python
import npyodbc

# Set the connection string to match the settings in your `odbc.ini` and `odbcinst.ini`
connection = npyodbc.connect(
    "DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;UID=postgres_user;PWD=postgres_pwd;DATABASE=test"
)

cursor = connection.cursor()

# Create a table and insert some values
cursor.execute('create table t1(col text)')
cursor.execute('insert into t1 values (?)', 'a test string')

# Retrieve entries from the table as Python objects
rows = cursor.execute('select * from t1').fetchall()

# Returns [('a test string',)]
print(rows)
```
