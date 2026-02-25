from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.infrastructure.db.base import BaseConnector


class OracleConnector(BaseConnector):
    def _create_engine(self) -> Engine:
        return create_engine(
            self.dsn,
            thick_mode=False,
            pool_pre_ping=True,
        )
