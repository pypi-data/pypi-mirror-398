"""Abstract base container implementation."""

from __future__ import annotations

from abc import ABC

from msgspec_settings import BaseSettings

from exit_stack_container.container.helpers import extract_origin, extract_origin_base, make_resolution_order

from ..dependency import Dependency
from ..exceptions import InvalidContainerInheritance
from ..models import BaseResources


class AbstractContainer[T = BaseSettings, V = BaseResources](ABC):
    """Abstract base for sync and async containers"""

    _settings: T

    def __init__(self) -> None:
        """Initialize container."""
        self._resources_class: type[V] | None = None
        self._dependencies: dict[str, Dependency] = {}
        self._resolution_order: list[str] = []

    @property
    def resources_class(self) -> type[V]:
        """Resources class extracted from generic parameters."""
        if self._resources_class is None:
            self._resources_class = self._extract_resources_class()
        return self._resources_class

    @property
    def dependencies(self) -> dict[str, Dependency]:
        """Scanned dependency descriptors."""
        if not self._dependencies:
            self._dependencies = self._scan_dependencies()
        return self._dependencies

    @property
    def resolution_order(self) -> list[str]:
        """Topologically sorted dependency names."""
        if not self._resolution_order:
            self._resolution_order = make_resolution_order(self.dependencies)
        return self._resolution_order

    def _extract_resources_class(self) -> type[V[T]]:
        """Extract Resources class from second generic argument."""
        origin_base = extract_origin_base(self.__class__)
        origin = extract_origin(origin_base)
        if not issubclass(origin, AbstractContainer):
            raise InvalidContainerInheritance(
                f"{self.__class__.__name__} must inherit from AbstractContainer subclass, got {origin.__name__}"
            )
        if args := getattr(origin_base, "__args__", None):
            if len(args) == 2:
                resources_cls = args[1]
                if issubclass(resources_cls, BaseResources):
                    return resources_cls
        raise InvalidContainerInheritance(f"{self.__class__.__name__} requires Resources subclass as second generic parameter")

    def _scan_dependencies(self) -> dict[str, Dependency]:
        """Scan container class for Dependency descriptors."""
        dependencies = {}
        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Dependency):
                dependencies[name] = attr
        return dependencies
