"""Sample workflow: Oracle (LDAP thin-mode) → Transform → MSSQL with truncate.

Demonstrates:
- OracleLdapConnector for source (thin mode, no Oracle Client needed)
- ExampleTransformStep for column mapping / computed fields
- Safe-truncate pattern: validate first batch → TRUNCATE → load all batches

Flow:
  1. Test source connection
  2. Extract batch 1 → Transform → validate (row count, columns)
  3. TRUNCATE staging table
  4. Load batch 1 → staging
  5. Extract batch N → Transform → Load → staging (repeat until done)
"""

from app.core.config import settings
from app.infrastructure.db.connector_factory import create_connector
from app.steps.extract.oracle_extract import OracleExtractStep
from app.steps.load.sqlserver_load import SqlServerLoadStep
from app.steps.transform.base_transform import BaseTransformStep
from app.steps.transform.example_transform import ExampleTransformStep
from app.workflows.base import BaseWorkflow
from app.workflows.registry import register_workflow

SAMPLE_QUERY = """\
SELECT e.EMPLOYEE_ID,
       e.FIRST_NAME,
       e.LAST_NAME,
       e.EMAIL,
       e.HIRE_DATE,
       e.SALARY,
       d.DEPARTMENT_NAME,
       m.FIRST_NAME  AS MANAGER_FIRST_NAME,
       m.LAST_NAME   AS MANAGER_LAST_NAME
FROM   EMPLOYEES e
       LEFT JOIN DEPARTMENTS d ON e.DEPARTMENT_ID = d.DEPARTMENT_ID
       LEFT JOIN EMPLOYEES   m ON e.MANAGER_ID    = m.EMPLOYEE_ID
WHERE  e.HIRE_DATE >= DATE '2020-01-01'
"""

EXPECTED_COLUMNS = {
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "hire_date",
    "salary",
    "department_name",
    "full_name",
    "manager_name",
}


@register_workflow
class LdapSampleOutboundWorkflow(BaseWorkflow):
    name = "ldap_sample_outbound"
    truncate_before_load = True

    def get_extract_step(self) -> OracleExtractStep:
        connector = create_connector(
            "oracle_ldap",
            dsn="",
            oracle_user=settings.oracle_ldap_user,
            oracle_password=settings.oracle_ldap_password,
            ldap_host=settings.oracle_ldap_host,
            ldap_port=settings.oracle_ldap_port,
            ldap_dn=settings.oracle_ldap_dn,
            db_service_name=settings.oracle_ldap_db_service_name,
        )
        return OracleExtractStep(connector, SAMPLE_QUERY, settings.batch_size)

    def get_transform_step(self) -> BaseTransformStep:
        return ExampleTransformStep()

    def get_load_step(self) -> SqlServerLoadStep:
        connector = create_connector("sqlserver", settings.mssql_dsn)
        return SqlServerLoadStep(connector, "dbo.employees_staging")

    def validate_batch(self, batch: list[dict]) -> None:
        """Check the first batch before we truncate staging."""
        super().validate_batch(batch)

        actual_cols = set(batch[0].keys())
        missing = EXPECTED_COLUMNS - actual_cols
        if missing:
            raise ValueError(
                f"First batch missing expected columns: {sorted(missing)}"
            )
