"""Dependency descriptor for declarative DI."""

from __future__ import annotations

import inspect
from typing import Any

from .exceptions import (
    DependencyNotResolvedError,
)
from .types import ResolvedDeps, ResourceFactory


class Dependency:
    """Dependency descriptor with factory and kwargs"""

    def __init__(self, factory: ResourceFactory, **kwargs: Any) -> None:
        """Initialize dependency.

        Args:
            factory: Factory function creating the resource.
            **kwargs: Factory arguments (values or Dependency instances).
        """
        self.factory = factory
        self.kwargs = kwargs
        self.name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    async def resolve(self, resolved_deps: ResolvedDeps) -> Any:
        """Resolve dependencies and instantiate resource.

        Args:
            resolved_deps: Already resolved dependencies.

        Returns:
            Resource instance.
        """

        resolved_kwargs = {}
        for key, value in self.kwargs.items():
            if not isinstance(value, Dependency):
                resolved_kwargs[key] = value
            else:
                if value.name not in resolved_deps:
                    raise DependencyNotResolvedError(f"Dependency '{value.name}' not resolved for '{self.name}'")
                resolved_kwargs[key] = resolved_deps[value.name]
        result = self.factory(**resolved_kwargs)

        if inspect.iscoroutine(result):
            result = await result

        return result


__all__ = [
    "Dependency",
]
