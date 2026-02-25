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
        step.execute.return_value = iter(self._batches)
        return step

    def get_transform_step(self):
        return PassthroughTransform()

    def get_load_step(self):
        mock = MagicMock(spec=SqlServerLoadStep)
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
    # transform and load still needed to avoid AttributeError
    wf.get_transform_step = lambda: PassthroughTransform()
    wf.get_load_step = lambda: MagicMock()

    result = wf.run()
    assert result.status == "failed"
    assert "connection refused" in result.errors[0]
