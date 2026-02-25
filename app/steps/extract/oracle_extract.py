from collections.abc import Generator
from typing import Any

from app.infrastructure.db.base import BaseConnector
from app.steps.base import BaseStep


class OracleExtractStep(BaseStep):
    def __init__(self, connector: BaseConnector, query: str, batch_size: int = 1000) -> None:
        self.connector = connector
        self.query = query
        self.batch_size = batch_size

    def execute(self, context: dict[str, Any]) -> Generator[list[dict], None, None]:
        """Yield batches of rows from Oracle."""
        return self.connector.extract_batches(self.query, self.batch_size)
