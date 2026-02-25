from datetime import datetime
from decimal import Decimal

from app.steps.transform.example_transform import ExampleTransformStep


def _make_row(**overrides):
    """Build a typical Oracle-style uppercase row."""
    row = {
        "EMPLOYEE_ID": 1,
        "FIRST_NAME": "Jane",
        "LAST_NAME": "Doe",
        "EMAIL": "jdoe@example.com",
        "HIRE_DATE": datetime(2023, 6, 15, 9, 30),
        "SALARY": Decimal("85000.50"),
        "DEPARTMENT_NAME": "Engineering",
        "MANAGER_FIRST_NAME": "Alice",
        "MANAGER_LAST_NAME": "Smith",
    }
    row.update(overrides)
    return row


def test_column_renaming():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row()])[0]
    assert "employee_id" in result
    assert "first_name" in result
    assert "EMPLOYEE_ID" not in result


def test_full_name_computed():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row()])[0]
    assert result["full_name"] == "Jane Doe"


def test_full_name_first_only():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row(LAST_NAME=None)])[0]
    assert result["full_name"] == "Jane"


def test_hire_date_datetime_to_iso():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row()])[0]
    assert result["hire_date"] == "2023-06-15T09:30:00"


def test_hire_date_string_passthrough():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row(HIRE_DATE="2023-06-15")])[0]
    assert result["hire_date"] == "2023-06-15"


def test_salary_decimal_to_float():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row()])[0]
    assert isinstance(result["salary"], float)
    assert result["salary"] == 85000.50


def test_null_department_default():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row(DEPARTMENT_NAME=None)])[0]
    assert result["department_name"] == "Unassigned"


def test_null_salary_default():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row(SALARY=None)])[0]
    assert result["salary"] == 0.0


def test_manager_name_computed_and_intermediates_dropped():
    step = ExampleTransformStep()
    result = step.transform_batch([_make_row()])[0]
    assert result["manager_name"] == "Alice Smith"
    assert "manager_first_name" not in result
    assert "manager_last_name" not in result


def test_batch_multiple_rows():
    step = ExampleTransformStep()
    rows = [_make_row(EMPLOYEE_ID=i) for i in range(5)]
    results = step.transform_batch(rows)
    assert len(results) == 5
    assert [r["employee_id"] for r in results] == [0, 1, 2, 3, 4]


def test_execute_interface():
    step = ExampleTransformStep()
    batch = [_make_row()]
    result = step.execute({"batch": batch})
    assert len(result) == 1
    assert result[0]["full_name"] == "Jane Doe"
