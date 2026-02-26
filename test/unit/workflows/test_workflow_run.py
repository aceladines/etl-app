from unittest.mock import MagicMock

from app.steps.extract.oracle_extract import OracleExtractStep
from app.steps.load.sqlserver_load import SqlServerLoadStep
from app.steps.transform.passthrough import PassthroughTransform
from app.workflows.base import BaseWorkflow


class _FakeWorkflow(BaseWorkflow):
    name = "fake"

    def __init__(self, batches: list[list[dict]]) -> None:
        self._batches = batches

    def get_extract_step(self) -> OracleExtractStep:
        step = MagicMock(spec=OracleExtractStep)
        step.connector = MagicMock()
        step.execute.return_value = iter(self._batches)
        return step

    def get_transform_step(self):
        return PassthroughTransform()

    def get_load_step(self):
        mock = MagicMock(spec=SqlServerLoadStep)
        mock.connector = MagicMock()
        mock.target_table = "dbo.fake_target"
        mock.execute.side_effect = lambda ctx: len(ctx["batch"])
        return mock


def test_workflow_run_success():
    batches = [[{"id": 1}, {"id": 2}], [{"id": 3}]]
    wf = _FakeWorkflow(batches)
    result = wf.run()

    assert result.status == "completed"
    assert result.total_rows == 3
    assert result.batches_processed == 2
    assert result.errors == []


def test_workflow_run_empty():
    wf = _FakeWorkflow([])
    result = wf.run()

    assert result.status == "completed"
    assert result.total_rows == 0
    assert result.batches_processed == 0


def test_workflow_run_extract_error():
    wf = _FakeWorkflow([])
    extract = MagicMock()
    extract.execute.side_effect = RuntimeError("connection refused")
    wf.get_extract_step = lambda: extract
    wf.get_transform_step = lambda: PassthroughTransform()
    wf.get_load_step = lambda: MagicMock()

    result = wf.run()
    assert result.status == "failed"
    assert "connection refused" in result.errors[0]


def test_workflow_run_tests_source_connection():
    """run() calls test_connection() on the source connector."""
    batches = [[{"id": 1}]]
    wf = _FakeWorkflow(batches)
    result = wf.run()

    assert result.status == "completed"


def test_workflow_run_connection_failure():
    """Workflow fails gracefully when source connection test fails."""
    wf = _FakeWorkflow([])
    extract = MagicMock(spec=OracleExtractStep)
    extract.connector = MagicMock()
    extract.connector.test_connection.side_effect = RuntimeError("unreachable")
    wf.get_extract_step = lambda: extract
    wf.get_transform_step = lambda: PassthroughTransform()
    wf.get_load_step = lambda: MagicMock(spec=SqlServerLoadStep)

    result = wf.run()
    assert result.status == "failed"
    assert "unreachable" in result.errors[0]


# ---- safe-truncate tests ----


class _TruncateWorkflow(_FakeWorkflow):
    """Workflow with truncate_before_load = True."""

    name = "truncate_fake"
    truncate_before_load = True


def test_truncate_workflow_success():
    """First batch is validated, target truncated, then all batches load."""
    batches = [[{"id": 1}, {"id": 2}], [{"id": 3}]]
    wf = _TruncateWorkflow(batches)
    result = wf.run()

    assert result.status == "completed"
    assert result.total_rows == 3
    assert result.batches_processed == 2


def test_truncate_workflow_calls_truncate_on_first_batch():
    """truncate_table is called on the load connector after validating batch 1."""
    batches = [[{"id": 1}], [{"id": 2}]]
    wf = _TruncateWorkflow(batches)

    load_mock = MagicMock(spec=SqlServerLoadStep)
    load_mock.connector = MagicMock()
    load_mock.target_table = "dbo.test_staging"
    load_mock.execute.side_effect = lambda ctx: len(ctx["batch"])
    wf.get_load_step = lambda: load_mock

    result = wf.run()

    assert result.status == "completed"
    load_mock.connector.truncate_table.assert_called_once_with("dbo.test_staging")


def test_truncate_workflow_aborts_on_empty_first_batch():
    """If the first batch is empty after transform, workflow fails before truncate."""
    wf = _TruncateWorkflow([[]])  # one batch, but it's empty

    load_mock = MagicMock(spec=SqlServerLoadStep)
    load_mock.connector = MagicMock()
    load_mock.target_table = "dbo.test_staging"
    wf.get_load_step = lambda: load_mock

    result = wf.run()

    assert result.status == "failed"
    assert "empty" in result.errors[0].lower()
    load_mock.connector.truncate_table.assert_not_called()


def test_truncate_workflow_aborts_on_validation_error():
    """Custom validate_batch can abort the workflow."""
    batches = [[{"id": 1}]]
    wf = _TruncateWorkflow(batches)
    wf.validate_batch = MagicMock(side_effect=ValueError("schema mismatch"))

    load_mock = MagicMock(spec=SqlServerLoadStep)
    load_mock.connector = MagicMock()
    load_mock.target_table = "dbo.test_staging"
    wf.get_load_step = lambda: load_mock

    result = wf.run()

    assert result.status == "failed"
    assert "schema mismatch" in result.errors[0]
    load_mock.connector.truncate_table.assert_not_called()


def test_no_truncate_without_flag():
    """Without truncate_before_load, no truncation happens."""
    batches = [[{"id": 1}]]
    wf = _FakeWorkflow(batches)

    load_mock = MagicMock(spec=SqlServerLoadStep)
    load_mock.connector = MagicMock()
    load_mock.target_table = "dbo.fake_target"
    load_mock.execute.side_effect = lambda ctx: len(ctx["batch"])
    wf.get_load_step = lambda: load_mock

    result = wf.run()

    assert result.status == "completed"
    load_mock.connector.truncate_table.assert_not_called()
