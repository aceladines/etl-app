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

    @abstractmethod
    def get_extract_step(self) -> OracleExtractStep:
        ...

    @abstractmethod
    def get_transform_step(self) -> BaseTransformStep:
        ...

    @abstractmethod
    def get_load_step(self) -> SqlServerLoadStep:
        ...

    def run(self) -> WorkflowResult:
        result = WorkflowResult(workflow_name=self.name)
        result.status = "running"

        extract = self.get_extract_step()
        transform = self.get_transform_step()
        load = self.get_load_step()

        try:
            batches = extract.execute({})
            for batch in batches:
                transformed = transform.transform_batch(batch)
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
