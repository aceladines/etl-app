from typing import Any

from app.infrastructure.db.base import BaseConnector
from app.infrastructure.db.oracle import OracleConnector
from app.infrastructure.db.oracle_ldap import OracleLdapConnector
from app.infrastructure.db.sqlserver import SqlServerConnector

_CONNECTOR_MAP: dict[str, type[BaseConnector]] = {
    "oracle": OracleConnector,
    "oracle_ldap": OracleLdapConnector,
    "sqlserver": SqlServerConnector,
}


def create_connector(db_type: str, dsn: str, **kwargs: Any) -> BaseConnector:
    cls = _CONNECTOR_MAP.get(db_type)
    if cls is None:
        raise ValueError(
            f"Unknown db_type {db_type!r}. Available: {list(_CONNECTOR_MAP)}"
        )
    return cls(dsn, **kwargs)
