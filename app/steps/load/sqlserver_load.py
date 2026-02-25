from typing import Any

from app.infrastructure.db.base import BaseConnector
from app.steps.base import BaseStep


class SqlServerLoadStep(BaseStep):
    def __init__(self, connector: BaseConnector, target_table: str) -> None:
        self.connector = connector
        self.target_table = target_table

    def execute(self, context: dict[str, Any]) -> int:
        """Load a batch of rows into SQL Server. Returns rows inserted."""
        return self.connector.load_batch(self.target_table, context["batch"])
