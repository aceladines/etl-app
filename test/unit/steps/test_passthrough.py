from app.steps.transform.passthrough import PassthroughTransform


def test_passthrough_returns_same_rows():
    rows = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    t = PassthroughTransform()
    result = t.transform_batch(rows)
    assert result is rows


def test_passthrough_execute():
    rows = [{"id": 1}]
    t = PassthroughTransform()
    result = t.execute({"batch": rows})
    assert result == rows
