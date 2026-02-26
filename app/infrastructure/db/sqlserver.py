from mssql_python import connect as mssql_connect

from app.infrastructure.db.base import BaseConnector


class SqlServerConnector(BaseConnector):
    """SQL Server connector using Microsoft's mssql-python driver.

    Uses Direct Database Connectivity (DDBC) — no ODBC driver required.
    Connection pooling is built-in and enabled by default.

    Connection string format:
        Server=host,port;Database=db;UID=user;PWD=pass;Encrypt=yes;
    """

    # --- SQLAlchemy engine not used — all methods overridden ---

    def _create_engine(self):
        raise NotImplementedError(
            "SqlServerConnector uses mssql-python directly, not SQLAlchemy"
        )

    def test_connection(self) -> None:
        with mssql_connect(self.dsn) as conn:
            conn.cursor().execute("SELECT 1")

    def truncate_table(self, table: str) -> None:
        with mssql_connect(self.dsn) as conn:
            conn.setautocommit(True)
            conn.cursor().execute(f"TRUNCATE TABLE {table}")

    def load_batch(self, table: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        columns = list(rows[0].keys())
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(columns)
        sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
        params = [tuple(row[c] for c in columns) for row in rows]
        with mssql_connect(self.dsn) as conn:
            conn.cursor().executemany(sql, params)
            conn.commit()
        return len(rows)

    def dispose(self) -> None:
        pass  # Connection pooling managed by mssql-python globally
