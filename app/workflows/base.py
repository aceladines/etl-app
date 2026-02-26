from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.steps.extract.oracle_extract import OracleExtractStep
from app.steps.load.sqlserver_load import SqlServerLoadStep
from app.steps.transform.base_transform import BaseTransformStep


@dataclass
class WorkflowResult:
    workflow_name: str
    status: str = "pending"
    total_rows: int = 0
    batches_processed: int = 0
    errors: list[str] = field(default_factory=list)


class BaseWorkflow(ABC):
    name: str = "base"
    truncate_before_load: bool = False

    @abstractmethod
    def get_extract_step(self) -> OracleExtractStep:
        ...

    @abstractmethod
    def get_transform_step(self) -> BaseTransformStep:
        ...

    @abstractmethod
    def get_load_step(self) -> SqlServerLoadStep:
        ...

    def validate_batch(self, batch: list[dict]) -> None:
        """Validate the first transformed batch before truncating the target.

        Override for custom checks (schema, null ratios, etc.).
        Raise ``ValueError`` to abort the workflow *before* truncation.
        """
        if not batch:
            raise ValueError("First batch is empty — aborting before truncate")

    def run(self) -> WorkflowResult:
        result = WorkflowResult(workflow_name=self.name)
        result.status = "running"

        extract = self.get_extract_step()
        transform = self.get_transform_step()
        load = self.get_load_step()

        try:
            # --- connection test ---
            extract.connector.test_connection()
            logger.info("{name} | source connection OK", name=self.name)

            batches = extract.execute({})
            is_first_batch = True

            for batch in batches:
                transformed = transform.transform_batch(batch)

                # --- safe-truncate on first batch ---
                if is_first_batch and self.truncate_before_load:
                    self.validate_batch(transformed)
                    logger.info(
                        "{name} | first batch validated ({rows} rows) — truncating target",
                        name=self.name,
                        rows=len(transformed),
                    )
                    load.connector.truncate_table(load.target_table)

                is_first_batch = False

                loaded = load.execute({"batch": transformed})
                result.batches_processed += 1
                result.total_rows += loaded
                logger.info(
                    "{name} | batch {n} loaded ({rows} rows)",
                    name=self.name,
                    n=result.batches_processed,
                    rows=loaded,
                )
        except Exception as exc:
            result.status = "failed"
            result.errors.append(str(exc))
            logger.error("{name} failed: {err}", name=self.name, err=exc)
            return result

        result.status = "completed"
        logger.info(
            "{name} completed — {total} rows in {batches} batches",
            name=self.name,
            total=result.total_rows,
            batches=result.batches_processed,
        )
        return result
