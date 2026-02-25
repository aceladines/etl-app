from app.core.config import settings
from app.infrastructure.db.connector_factory import create_connector
from app.steps.extract.oracle_extract import OracleExtractStep
from app.steps.load.sqlserver_load import SqlServerLoadStep
from app.steps.transform.base_transform import BaseTransformStep
from app.steps.transform.passthrough import PassthroughTransform
from app.workflows.base import BaseWorkflow
from app.workflows.registry import register_workflow

PO_QUERY = """\
SELECT *
FROM purchase_orders
WHERE ROWNUM <= 10000
"""


@register_workflow
class PurchaseOrderOutboundWorkflow(BaseWorkflow):
    name = "purchase_order_outbound"

    def get_extract_step(self) -> OracleExtractStep:
        connector = create_connector("oracle", settings.oracle_dsn)
        return OracleExtractStep(connector, PO_QUERY, settings.batch_size)

    def get_transform_step(self) -> BaseTransformStep:
        return PassthroughTransform()

    def get_load_step(self) -> SqlServerLoadStep:
        connector = create_connector("sqlserver", settings.mssql_dsn)
        return SqlServerLoadStep(connector, "dbo.purchase_orders_outbound")
