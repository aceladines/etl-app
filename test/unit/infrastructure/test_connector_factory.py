import pytest

from app.infrastructure.db.connector_factory import create_connector
from app.infrastructure.db.oracle import OracleConnector
from app.infrastructure.db.oracle_ldap import OracleLdapConnector
from app.infrastructure.db.sqlserver import SqlServerConnector


def test_create_oracle_connector():
    c = create_connector("oracle", "oracle+oracledb://a:b@localhost/x")
    assert isinstance(c, OracleConnector)
    assert c.dsn == "oracle+oracledb://a:b@localhost/x"


def test_create_sqlserver_connector():
    c = create_connector(
        "sqlserver",
        "Server=localhost,1433;Database=x;UID=a;PWD=b;Encrypt=yes;",
    )
    assert isinstance(c, SqlServerConnector)


def test_create_oracle_ldap_connector():
    c = create_connector(
        "oracle_ldap",
        "",
        oracle_user="scott",
        oracle_password="tiger",
        ldap_host="ldap.example.com",
        ldap_port=389,
        ldap_dn="cn=OracleContext,dc=example,dc=com",
        db_service_name="ORCL",
    )
    assert isinstance(c, OracleLdapConnector)
    assert c.oracle_user == "scott"
    assert c.ldap_host == "ldap.example.com"
    assert c.db_service_name == "ORCL"


def test_unknown_db_type():
    with pytest.raises(ValueError, match="Unknown db_type"):
        create_connector("postgres", "postgresql://a:b@localhost/x")
