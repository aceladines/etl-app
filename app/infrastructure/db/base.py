from abc import ABC, abstractmethod
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class BaseConnector(ABC):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._engine: Engine | None = None

    @abstractmethod
    def _create_engine(self) -> Engine:
        ...

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def test_connection(self) -> None:
        """Verify connectivity with a lightweight query. Raises on failure."""
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def extract_batches(
        self, query: str, batch_size: int = 1000
    ) -> Generator[list[dict], None, None]:
        """Stream rows from the source in fixed-size batches."""
        with self.engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(text(query))
            columns = list(result.keys())
            for partition in result.partitions(batch_size):
                yield [dict(zip(columns, row)) for row in partition]

    def truncate_table(self, table: str) -> None:
        """TRUNCATE the given table."""
        with self.engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table}"))

    def load_batch(self, table: str, rows: list[dict]) -> int:
        """Insert a batch of rows into a target table. Returns row count."""
        if not rows:
            return 0
        columns = list(rows[0].keys())
        placeholders = ", ".join(f":{c}" for c in columns)
        col_list = ", ".join(columns)
        stmt = text(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})")
        with self.engine.begin() as conn:
            conn.execute(stmt, rows)
        return len(rows)

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
