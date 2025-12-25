---
sidebar_position: 1
---

# Intro

Introduction to npyodbc.

npyodbc was developed using [pyodbc](https://github.com/mkleehammer/pyodbc) and
extended using [NumPy](https://numpy.org). We use pyodbc as a subproject within the
npyodbc project, and leverage [meson](https://mesonbuild.com) as the build system.
With the help of meson we can use the latest release of pyodbc and extend it to
include returning result sets from an ODBC compliant SQL server as NumPy arrays.

Documentation for pyodbc can be found on their
[wiki](https://github.com/mkleehammer/pyodbc/wiki). We will only include components of
that wiki that directly relate to how to use npyodbc. Advanced usage of pyodbc
features will be linked directly to the pyodbc wiki.

All example code will assume you have Microsoft SQL 2022 running locally in a Docker
container. The [dev installation documentation](installation/dev-install.md) discusses
how to do this, but we will outline it below for an installation **not** using the
VSCode devcontainer.

Install the npyodbc Docker container by navigating to the repo where the `Dockerfile`
exists and executing the following command in your terminal.

```bash showLineNumbers
# Build the Docker image and tag it as npyodbc
docker build . --tag npyodbc

# Start a container using the npyodbc image and name it npyodbc as well
docker run -p 1401:1433 --name npyodbc --hostname npyodbc -m 16GB -d npyodbc

# (OPTIONAL) Log into the container
docker exec -it npyodbc bash
```

If you log into the container, you can access the SQL 2022 command line by navigating to
it and running the `sqlcmd` command. Below we include the user name and password for
logging into the SQL 2022 server.

```bash showLineNumbers
# Navigate to the SQL bin directory
cd /opt/mssql-tools/bin

# Open the SQL command line utility
./sqlcmd -U SA -P StrongPassword2022! -S localhost
```

You can now add a test table manually here that you can access using npyodbc.

```sql showLineNumbers
DROP TABLE test;
CREATE TABLE test (columnA VARBINARY(20), columnB VARBINARY(20));
INSERT INTO test VALUES(CAST('zort' AS VARBINARY(20)), CAST('troz' AS VARBINARY(20)));
INSERT INTO test VALUES(CAST('poit' AS VARBINARY(20)), CAST('rubber pants' AS VARBINARY(20)));
GO;
```

You must supply the `GO` command otherwise the commands will not get executed by SQL
2022. The `QUIT` command will exit out of `sqlcmd` if you so wish to do so.

## VSCode devcontainer

If you use the devcontainer then all the above applies, except for building the Docker
image and starting a container since that is already done for you with the devcontainer
setup. You will need to navigate to the directory where `sqlcmd` exists, log into it and
create a test table.
