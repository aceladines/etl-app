import pytest


@pytest.mark.anyio
async def test_list_workflows(client):
    resp = await client.get("/api/v1/workflows/")
    assert resp.status_code == 200
    data = resp.json()
    assert "contracts_outbound" in data
    assert "purchase_order_outbound" in data


@pytest.mark.anyio
async def test_trigger_workflow(client):
    resp = await client.post(
        "/api/v1/workflows/trigger",
        json={"workflow_name": "contracts_outbound"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "run_id" in data
    assert data["status"] == "running"


@pytest.mark.anyio
async def test_trigger_unknown_workflow(client):
    resp = await client.post(
        "/api/v1/workflows/trigger",
        json={"workflow_name": "nope"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_status_not_found(client):
    resp = await client.get("/api/v1/workflows/status/nonexistent-id")
    assert resp.status_code == 404
