from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.db.oracle_ldap import OracleLdapConnector

SAMPLE_DESCRIPTOR = (
    "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbhost.example.com)(PORT=1521))"
    "(CONNECT_DATA=(SERVICE_NAME=ORCL)))"
)


def _make_connector(**overrides):
    defaults = {
        "oracle_user": "scott",
        "oracle_password": "tiger",
        "ldap_host": "ldap.example.com",
        "ldap_port": 389,
        "ldap_dn": "cn=OracleContext,dc=example,dc=com",
        "db_service_name": "ORCL",
    }
    return OracleLdapConnector(**(defaults | overrides))


def test_oracle_ldap_connector_init():
    c = _make_connector()
    assert c.oracle_user == "scott"
    assert c.oracle_password == "tiger"
    assert c.ldap_host == "ldap.example.com"
    assert c.ldap_port == 389
    assert c.ldap_dn == "cn=OracleContext,dc=example,dc=com"
    assert c.db_service_name == "ORCL"
    assert c.dsn == ""


@patch("app.infrastructure.db.oracle_ldap.ldap3")
def test_resolve_via_ldap_queries_directory(mock_ldap3):
    entry = MagicMock()
    entry.orclNetDescString.value = SAMPLE_DESCRIPTOR
    mock_conn = MagicMock()
    mock_conn.entries = [entry]
    mock_ldap3.Connection.return_value = mock_conn

    c = _make_connector()
    result = c._resolve_via_ldap()

    mock_ldap3.Server.assert_called_once_with("ldap.example.com", port=389)
    mock_ldap3.Connection.assert_called_once_with(
        mock_ldap3.Server.return_value, auto_bind=True,
    )
    mock_conn.search.assert_called_once_with(
        "cn=OracleContext,dc=example,dc=com",
        "(cn=ORCL)",
        attributes=["orclNetDescString"],
    )
    mock_conn.unbind.assert_called_once()
    assert result == SAMPLE_DESCRIPTOR


@patch("app.infrastructure.db.oracle_ldap.ldap3")
def test_resolve_via_ldap_raises_on_no_entries(mock_ldap3):
    mock_conn = MagicMock()
    mock_conn.entries = []
    mock_ldap3.Connection.return_value = mock_conn

    c = _make_connector()
    with pytest.raises(ConnectionError, match="no entry for"):
        c._resolve_via_ldap()

    mock_conn.unbind.assert_called_once()


@patch("app.infrastructure.db.oracle_ldap.ldap3")
def test_resolve_via_ldap_custom_port(mock_ldap3):
    entry = MagicMock()
    entry.orclNetDescString.value = SAMPLE_DESCRIPTOR
    mock_conn = MagicMock()
    mock_conn.entries = [entry]
    mock_ldap3.Connection.return_value = mock_conn

    c = _make_connector(ldap_port=636)
    c._resolve_via_ldap()

    mock_ldap3.Server.assert_called_once_with("ldap.example.com", port=636)


@patch("app.infrastructure.db.oracle_ldap.OracleLdapConnector._resolve_via_ldap")
@patch("app.infrastructure.db.oracle_ldap.create_engine")
def test_create_engine_uses_resolved_descriptor(mock_create_engine, mock_resolve):
    mock_resolve.return_value = SAMPLE_DESCRIPTOR
    mock_create_engine.return_value = MagicMock()

    c = _make_connector()
    c._create_engine()

    mock_resolve.assert_called_once()
    mock_create_engine.assert_called_once()
    _, kwargs = mock_create_engine.call_args
    assert callable(kwargs["creator"])
    assert kwargs["pool_pre_ping"] is True


@patch("app.infrastructure.db.oracle_ldap.OracleLdapConnector._resolve_via_ldap")
@patch("app.infrastructure.db.oracle_ldap.oracledb")
@patch("app.infrastructure.db.oracle_ldap.create_engine")
def test_creator_passes_resolved_descriptor_to_oracledb(
    mock_create_engine, mock_oracledb, mock_resolve,
):
    mock_resolve.return_value = SAMPLE_DESCRIPTOR
    mock_create_engine.return_value = MagicMock()

    c = _make_connector()
    c._create_engine()

    creator = mock_create_engine.call_args.kwargs["creator"]
    creator()

    mock_oracledb.connect.assert_called_once_with(
        user="scott",
        password="tiger",
        dsn=SAMPLE_DESCRIPTOR,
    )
