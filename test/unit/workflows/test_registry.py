import pytest

from app.workflows.registry import _REGISTRY, get_workflow, list_workflows


def test_workflows_registered():
    names = list_workflows()
    assert "contracts_outbound" in names
    assert "purchase_order_outbound" in names
    assert "example_reference" in names


def test_get_workflow_returns_instance():
    wf = get_workflow("contracts_outbound")
    assert wf.name == "contracts_outbound"


def test_get_unknown_workflow():
    with pytest.raises(KeyError, match="not found"):
        get_workflow("does_not_exist")
