from unittest.mock import MagicMock, patch

from app.infrastructure.db.oracle_ldap import OracleLdapConnector


def _make_connector(**overrides):
    defaults = dict(
        oracle_user="scott",
        oracle_password="tiger",
        ldap_host="ldap.example.com",
        ldap_port=389,
        ldap_dn="cn=OracleContext,dc=example,dc=com",
        db_service_name="ORCL",
    )
    defaults.update(overrides)
    return OracleLdapConnector(**defaults)


def test_oracle_ldap_connector_init():
    c = _make_connector()
    assert c.oracle_user == "scott"
    assert c.oracle_password == "tiger"
    assert c.ldap_host == "ldap.example.com"
    assert c.ldap_port == 389
    assert c.ldap_dn == "cn=OracleContext,dc=example,dc=com"
    assert c.db_service_name == "ORCL"
    assert c.dsn == ""


def test_build_ldap_url():
    c = _make_connector()
    assert c._build_ldap_url() == (
        "ldap://ldap.example.com:389/ORCL,cn=OracleContext,dc=example,dc=com"
    )


def test_build_ldap_url_custom_port():
    c = _make_connector(ldap_port=636)
    assert c._build_ldap_url() == (
        "ldap://ldap.example.com:636/ORCL,cn=OracleContext,dc=example,dc=com"
    )


def test_build_ldap_url_custom_service():
    c = _make_connector(db_service_name="PRODDB")
    assert c._build_ldap_url() == (
        "ldap://ldap.example.com:389/PRODDB,cn=OracleContext,dc=example,dc=com"
    )


@patch("app.infrastructure.db.oracle_ldap.create_engine")
def test_create_engine_uses_creator(mock_create_engine):
    mock_create_engine.return_value = MagicMock()
    c = _make_connector()
    engine = c._create_engine()

    mock_create_engine.assert_called_once()
    args, kwargs = mock_create_engine.call_args
    assert args == ("oracle+oracledb://",)
    assert "creator" in kwargs
    assert callable(kwargs["creator"])
    assert kwargs["pool_pre_ping"] is True


@patch("app.infrastructure.db.oracle_ldap.oracledb")
@patch("app.infrastructure.db.oracle_ldap.create_engine")
def test_creator_calls_oracledb_connect(mock_create_engine, mock_oracledb):
    mock_create_engine.return_value = MagicMock()
    c = _make_connector()
    c._create_engine()

    # Extract the creator callable that was passed to create_engine
    creator = mock_create_engine.call_args.kwargs["creator"]
    creator()

    mock_oracledb.connect.assert_called_once_with(
        user="scott",
        password="tiger",
        dsn="ldap://ldap.example.com:389/ORCL,cn=OracleContext,dc=example,dc=com",
    )
