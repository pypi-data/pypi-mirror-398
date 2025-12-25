#!/bin/bash

export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=postgres_db
export PGUSER=postgres_user
export PGPASSWORD=postgres_pwd

# Create test database
psql -c "CREATE DATABASE test WITH encoding='UTF8' LC_COLLATE='en_US.utf8' LC_CTYPE='en_US.utf8'"

export PYODBC_POSTGRESQL="DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;UID=postgres_user;PWD=postgres_pwd;DATABASE=test"

# pytest -vv ./tests/postgresql_test.py::test_native_uuid
