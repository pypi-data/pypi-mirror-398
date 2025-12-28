import os
from collections.abc import Iterator

import pyodbc
import pytest

# Default connection string - override with MSSQL_CONNECTION_STRING env var
# Matches docker-compose.yaml settings
DEFAULT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=sa;"
    "PWD=TestDb@Password123;"
    "TrustServerCertificate=yes;"
)


def get_connection_string() -> str:
    return os.environ.get("MSSQL_CONNECTION_STRING", DEFAULT_CONNECTION_STRING)


@pytest.fixture(scope="function")
def conn() -> Iterator[pyodbc.Connection]:
    conn = pyodbc.connect(get_connection_string(), autocommit=True)
    yield conn
    conn.close()


@pytest.fixture(scope="function", autouse=True)
def clear_test_db(conn: pyodbc.Connection) -> None:
    """Delete all tables before each test."""
    cursor = conn.cursor()

    # Check if tables exist and delete data
    tables = [
        "checkpoint_writes",
        "checkpoint_blobs",
        "checkpoints",
        "checkpoint_migrations",
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except pyodbc.ProgrammingError:
            pass  # Table doesn't exist yet
