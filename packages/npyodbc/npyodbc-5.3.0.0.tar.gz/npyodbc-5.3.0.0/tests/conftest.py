import npyodbc
import pytest


def get_running_test_dbs() -> dict[str, npyodbc.Connection]:
    """Get the running database services.

    Returns
    -------
    dict[str, npyodbc.Connection]
        Mapping between the connection name and an npyodbc Connection, if available.
    """
    connections = {
        "sqlite": "Driver=SQLite3;Database=:memory:;Charset=UTF8",
        "postgres": "DRIVER={PostgreSQL Unicode};SERVER=localhost;PORT=5432;UID=postgres_user;PWD=postgres_pwd;DATABASE=test",
        "mysql": "DRIVER={MySQL ODBC 8.0 ANSI Driver};SERVER=localhost;UID=root;PWD=root;DATABASE=test;CHARSET=utf8mb4",
        "mssql_2017": "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1401;UID=sa;PWD=StrongPassword2017;DATABASE=test;Encrypt=Optional",
        "mssql_2019": "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1402;UID=sa;PWD=StrongPassword2019;DATABASE=test;Encrypt=Optional",
        "mssql_2022": "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1403;UID=sa;PWD=StrongPassword2022;DATABASE=test;Encrypt=Optional",
    }
    for db, connection_str in connections.items():
        try:
            npyodbc.connect(connection_str, timeout=1)
            print(f"{db} database service is running.")
        except Exception:
            connections[db] = None
            print(f"{db} database service is not running; tests will be skipped.")
    return connections


DATABASES = get_running_test_dbs()

def pytest_runtest_setup(item: pytest.Item):
    """Check that all tests that have database markers have a running database service.

    Tests marked with databases that are not running are skipped.

    Parameters
    ----------
    item : pytest.Item
        Test invocation item; potentially annotated
    """
    for marker in item.iter_markers():
        if marker.name in DATABASES and DATABASES[marker.name] is None:
            pytest.skip(f"{marker.name} database is not running.")
