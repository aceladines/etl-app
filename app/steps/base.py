from abc import ABC, abstractmethod
from typing import Any


class BaseStep(ABC):
    @abstractmethod
    def execute(self, context: dict[str, Any]) -> Any:
        ...
