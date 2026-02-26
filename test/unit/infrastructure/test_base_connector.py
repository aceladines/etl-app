from unittest.mock import MagicMock, patch, call

from sqlalchemy import text

from app.infrastructure.db.base import BaseConnector


class _FakeConnector(BaseConnector):
    """Concrete subclass for testing BaseConnector methods."""

    def _create_engine(self):
        return MagicMock()


def test_test_connection_executes_select_1():
    connector = _FakeConnector(dsn="fake://")
    mock_conn = MagicMock()
    connector.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    connector.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    connector.test_connection()

    mock_conn.execute.assert_called_once()
    executed_sql = str(mock_conn.execute.call_args[0][0].text)
    assert executed_sql == "SELECT 1"


def test_test_connection_raises_on_failure():
    connector = _FakeConnector(dsn="fake://")
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("connection refused")
    connector.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    connector.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    try:
        connector.test_connection()
        assert False, "Should have raised"
    except Exception as exc:
        assert "connection refused" in str(exc)


def test_truncate_table():
    connector = _FakeConnector(dsn="fake://")
    mock_conn = MagicMock()
    connector.engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    connector.engine.begin.return_value.__exit__ = MagicMock(return_value=False)

    connector.truncate_table("dbo.my_table")

    mock_conn.execute.assert_called_once()
    executed_sql = str(mock_conn.execute.call_args[0][0].text)
    assert executed_sql == "TRUNCATE TABLE dbo.my_table"
