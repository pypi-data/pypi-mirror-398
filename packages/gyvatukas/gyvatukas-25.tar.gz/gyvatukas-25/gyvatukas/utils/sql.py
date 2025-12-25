import sqlite3
import textwrap
from contextlib import contextmanager
import pathlib
from threading import local


def get_inline_sql(sql: str) -> str:
    """Convert pretty SQL statement in docstring to something that looks good in console output or logs.

    - Cleanup PII if you are going to log all SQL queries 🤠
    """
    # Dedent first to normalize indentation
    sql = textwrap.dedent(sql)
    # Replace multiple whitespace characters with a single space
    sql = " ".join(sql.split())
    # Remove starting and ending whitespace
    sql = sql.strip()
    return sql


_thread_local = local()


class DictCursor(sqlite3.Cursor):
    def __init__(self, connection):
        super().__init__(connection)
        self.row_factory = self._dict_factory

    def _dict_factory(self, cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}


@contextmanager
def get_conn_cur(path_db: pathlib.Path):
    """Thread-safe context manager that yields SQLite connection and cursor.
    Reuses connection within same thread."""
    if not hasattr(_thread_local, "connection"):
        _thread_local.connection = sqlite3.connect(path_db, check_same_thread=False)

    try:
        cursor = DictCursor(_thread_local.connection)
        yield _thread_local.connection, cursor
        _thread_local.connection.commit()
    except Exception:
        _thread_local.connection.rollback()
        raise
    finally:
        cursor.close()


def init_db(path_db: pathlib.Path, sql_script: str):
    """Initialize database with SQL script."""
    with get_conn_cur(path_db) as (conn, cur):
        cur.executescript(sql_script)


def close_connections():
    """Close thread's database connection."""
    if hasattr(_thread_local, "connection"):
        _thread_local.connection.close()
        del _thread_local.connection
