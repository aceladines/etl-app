import ldap3
import oracledb
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.infrastructure.db.base import BaseConnector


class OracleLdapConnector(BaseConnector):
    """Oracle connector that resolves the database address via LDAP.

    Uses ``oracledb`` thin mode — no Oracle Client libraries required.
    Queries the LDAP directory with ``ldap3`` for the
    ``orclNetDescString`` attribute (the Oracle connect descriptor),
    then passes the resolved descriptor to ``oracledb.connect()``
    through SQLAlchemy's ``creator`` hook.
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

    def _resolve_via_ldap(self) -> str:
        """Query the LDAP directory for the Oracle connect descriptor."""
        server = ldap3.Server(self.ldap_host, port=self.ldap_port)
        conn = ldap3.Connection(server, auto_bind=True)
        try:
            conn.search(
                self.ldap_dn,
                f"(cn={self.db_service_name})",
                attributes=["orclNetDescString"],
            )
            if not conn.entries:
                raise ConnectionError(
                    f"LDAP lookup failed: no entry for "
                    f"cn={self.db_service_name} under {self.ldap_dn}"
                )
            descriptor = conn.entries[0].orclNetDescString.value
        finally:
            conn.unbind()
        logger.debug("LDAP resolved {} to connect descriptor", self.db_service_name)
        return descriptor

    def _create_engine(self) -> Engine:
        connect_descriptor = self._resolve_via_ldap()

        def _creator() -> oracledb.Connection:
            return oracledb.connect(
                user=self.oracle_user,
                password=self.oracle_password,
                dsn=connect_descriptor,
            )

        return create_engine(
            "oracle+oracledb://",
            creator=_creator,
            pool_pre_ping=True,
        )
