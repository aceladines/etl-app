from app.core.config import Settings


def test_default_settings():
    s = Settings(
        oracle_dsn="oracle+oracledb://a:b@localhost/x",
        mssql_dsn="mssql+pyodbc://a:b@localhost/x",
    )
    assert s.batch_size == 1000
    assert s.log_level == "INFO"


def test_custom_batch_size():
    s = Settings(
        oracle_dsn="oracle+oracledb://a:b@localhost/x",
        mssql_dsn="mssql+pyodbc://a:b@localhost/x",
        batch_size=500,
    )
    assert s.batch_size == 500
