from typing import Type

from app.workflows.base import BaseWorkflow

_REGISTRY: dict[str, Type[BaseWorkflow]] = {}


def register_workflow(cls: Type[BaseWorkflow]) -> Type[BaseWorkflow]:
    """Class decorator that registers a workflow by its ``name`` attribute."""
    _REGISTRY[cls.name] = cls
    return cls


def get_workflow(name: str) -> BaseWorkflow:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise KeyError(f"Workflow {name!r} not found. Available: {list(_REGISTRY)}")
    return cls()


def list_workflows() -> list[str]:
    return list(_REGISTRY.keys())
