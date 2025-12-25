---
sidebar_position: 1
---

# Development installation

Development installation of npyodbc.

Below includes Microsoft SQL Server 2022 if you follow the VSCode or Docker install. The
password for the server can be found in the Dockerfile and is `StrongPassword2022!`,
which is not secure.

## Dev install using VSCode

Choose to open the repo in the supplied `devcontainer` if you use VSCode. Within the
`devcontainer` will be SQL Server 2022.

## Dev install using Docker

Run the following commands using docker to install the project into a container. This is
similar to the `devcontainer` in VSCode above.

```bash showLineNumbers
# Build the image
docker build . --tag npyodbc
# Start a container
docker run -p 1401:1433 --name npyodbc --hostname npyodbc -m 16GB -d npyodbc
# (OPTIONAL) Log into the container
docker exec -it npyodbc bash
```

If you log into the container, you will have access to SQL Server 2022 as well as the
code in `$HOME/mssql/npyodbc`.

### Dev install using conda

Local development using `conda` or `mamba` can be done with the following commands. If
you are using `mamba`, replace `conda` with `mamba`.

```bash showLineNumbers
conda env create --file environment.yaml
conda activate npyodbc-dev
pip install .[dev,test]
```

Note that editable installs are not available since the codebase is primarily written in
C++, and needs to be compiled in order for Python to have access to the extension. If
you choose to install via the `conda/mamba` route, then you will still need to use the
Dockerfile to install Microsoft SQL 2022. That way you can develop locally and still
have a working version of SQL 2022 to test with.

If you are going to do development on npyodbc, then ensure you install the `dev` and
`test` extras as indicated above.
