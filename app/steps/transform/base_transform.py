from abc import abstractmethod

from app.steps.base import BaseStep


class BaseTransformStep(BaseStep):
    @abstractmethod
    def transform_batch(self, batch: list[dict]) -> list[dict]:
        ...

    def execute(self, context: dict) -> list[dict]:
        return self.transform_batch(context["batch"])
