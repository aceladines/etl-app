from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.infrastructure.db.base import BaseConnector


class SqlServerConnector(BaseConnector):
    def _create_engine(self) -> Engine:
        engine = create_engine(self.dsn, pool_pre_ping=True)

        @event.listens_for(engine, "before_cursor_execute")
        def _enable_fast_executemany(conn, cursor, statement, parameters, context, executemany):
            if executemany:
                cursor.fast_executemany = True

        return engine
