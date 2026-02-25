from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    oracle_dsn: str = "oracle+oracledb://user:pass@localhost:1521/?service_name=ORCL"
    mssql_dsn: str = (
        "mssql+pyodbc://user:pass@localhost:1433/db"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&TrustServerCertificate=yes"
    )
    batch_size: int = 1000
    log_level: str = "INFO"

    # Oracle LDAP connection (optional — only needed for oracle_ldap connector)
    oracle_ldap_host: str | None = None
    oracle_ldap_port: int = 389
    oracle_ldap_dn: str | None = None
    oracle_ldap_user: str | None = None
    oracle_ldap_password: str | None = None


settings = Settings()
