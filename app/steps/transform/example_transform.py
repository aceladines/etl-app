"""Example transform step demonstrating common ETL transformations.

Use this as a starting point when building a custom transform for a new
workflow.  Copy the file, rename the class, and adjust the logic to match
your source/target schemas.
"""

from datetime import datetime
from decimal import Decimal

from app.steps.transform.base_transform import BaseTransformStep

# Maps Oracle UPPERCASE column names to snake_case target names.
COLUMN_MAP: dict[str, str] = {
    "EMPLOYEE_ID": "employee_id",
    "FIRST_NAME": "first_name",
    "LAST_NAME": "last_name",
    "EMAIL": "email",
    "HIRE_DATE": "hire_date",
    "SALARY": "salary",
    "DEPARTMENT_NAME": "department_name",
    "MANAGER_FIRST_NAME": "manager_first_name",
    "MANAGER_LAST_NAME": "manager_last_name",
}


class ExampleTransformStep(BaseTransformStep):
    """Demonstrates column renaming, computed fields, type coercion,
    NULL defaults, and dropping intermediate columns."""

    def transform_batch(self, batch: list[dict]) -> list[dict]:
        return [self._transform_row(row) for row in batch]

    def _transform_row(self, row: dict) -> dict:
        # 1. Column renaming — Oracle columns arrive as UPPERCASE
        renamed = {
            COLUMN_MAP.get(k, k.lower()): v
            for k, v in row.items()
        }

        # 2. Computed field — combine first + last into full_name
        first = renamed.get("first_name", "") or ""
        last = renamed.get("last_name", "") or ""
        renamed["full_name"] = f"{first} {last}".strip()

        # 3. Type coercion — datetime → ISO-8601 string
        hire = renamed.get("hire_date")
        if isinstance(hire, datetime):
            renamed["hire_date"] = hire.isoformat()

        # 4. Type coercion — Decimal → float
        salary = renamed.get("salary")
        if isinstance(salary, Decimal):
            renamed["salary"] = float(salary)

        # 5. NULL defaults
        if not renamed.get("department_name"):
            renamed["department_name"] = "Unassigned"
        if not renamed.get("salary"):
            renamed["salary"] = 0.0

        # 6. Computed field — combine manager name, then drop intermediates
        mgr_first = renamed.pop("manager_first_name", "") or ""
        mgr_last = renamed.pop("manager_last_name", "") or ""
        renamed["manager_name"] = f"{mgr_first} {mgr_last}".strip()

        return renamed
