import oracledb
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.infrastructure.db.base import BaseConnector


class OracleLdapConnector(BaseConnector):
    """Oracle connector that resolves the database address via LDAP.

    Uses ``oracledb`` thin mode — no Oracle Client libraries required.
    The LDAP URL is built as ``ldap://host:port/service_name,context_dn``
    and passed to ``oracledb.connect()`` through SQLAlchemy's ``creator`` hook.
    """

    def __init__(
        self,
        dsn: str = "",
        *,
        oracle_user: str,
        oracle_password: str,
        ldap_host: str,
        ldap_port: int = 389,
        ldap_dn: str,
        db_service_name: str,
    ) -> None:
        super().__init__(dsn)
        self.oracle_user = oracle_user
        self.oracle_password = oracle_password
        self.ldap_host = ldap_host
        self.ldap_port = ldap_port
        self.ldap_dn = ldap_dn
        self.db_service_name = db_service_name

    def _build_ldap_url(self) -> str:
        return (
            f"ldap://{self.ldap_host}:{self.ldap_port}"
            f"/{self.db_service_name},{self.ldap_dn}"
        )

    def _create_engine(self) -> Engine:
        ldap_url = self._build_ldap_url()

        def _creator() -> oracledb.Connection:
            return oracledb.connect(
                user=self.oracle_user,
                password=self.oracle_password,
                dsn=ldap_url,
            )

        return create_engine(
            "oracle+oracledb://",
            creator=_creator,
            pool_pre_ping=True,
        )
