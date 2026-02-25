"""Example reference workflow — copy this file when creating a new workflow.

Demonstrates:
- A multi-table extract query with JOINs and a WHERE clause
- A custom transform step (not passthrough)
- How to swap in an LDAP connector instead of the default Oracle connector
"""

from app.core.config import settings
from app.infrastructure.db.connector_factory import create_connector
from app.steps.extract.oracle_extract import OracleExtractStep
from app.steps.load.sqlserver_load import SqlServerLoadStep
from app.steps.transform.base_transform import BaseTransformStep
from app.steps.transform.example_transform import ExampleTransformStep
from app.workflows.base import BaseWorkflow
from app.workflows.registry import register_workflow

# ---------------------------------------------------------------------------
# Extract query
# ---------------------------------------------------------------------------
# - Always list columns explicitly (SELECT * is fragile across schema changes)
# - Use table aliases for readability in JOINs
# - Add a WHERE clause to limit rows during development / testing
EXAMPLE_QUERY = """\
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


@register_workflow
class ExampleReferenceWorkflow(BaseWorkflow):
    name = "example_reference"

    def get_extract_step(self) -> OracleExtractStep:
        # Standard Oracle connector (direct host/port/service_name DSN):
        connector = create_connector("oracle", settings.oracle_dsn)

        # To use LDAP resolution instead, replace the line above with:
        #
        # connector = create_connector(
        #     "oracle_ldap",
        #     dsn="",
        #     oracle_user=settings.oracle_ldap_user,
        #     oracle_password=settings.oracle_ldap_password,
        #     ldap_host=settings.oracle_ldap_host,
        #     ldap_port=settings.oracle_ldap_port,
        #     ldap_dn=settings.oracle_ldap_dn,
        # )

        return OracleExtractStep(connector, EXAMPLE_QUERY, settings.batch_size)

    def get_transform_step(self) -> BaseTransformStep:
        # Use ExampleTransformStep for column renaming, computed fields, etc.
        return ExampleTransformStep()

    def get_load_step(self) -> SqlServerLoadStep:
        connector = create_connector("sqlserver", settings.mssql_dsn)
        return SqlServerLoadStep(connector, "dbo.employees_outbound")
