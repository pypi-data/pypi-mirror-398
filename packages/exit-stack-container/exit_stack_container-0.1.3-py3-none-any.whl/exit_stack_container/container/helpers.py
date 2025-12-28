"""Helper utilities for dependency resolution and lifecycle management."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable
from typing import Callable

from ..dependency import Dependency
from ..exceptions import CircularDependencyError, InvalidContainerInheritance
from ..types import CleanupFn, DependencyGraph


def extract_origin_base(cls: type) -> type:
    """Extract first original base class from __orig_bases__."""
    if orig_bases := getattr(cls, "__orig_bases__", None):
        return orig_bases[0]
    raise InvalidContainerInheritance(f"{cls.__name__} missing __orig_bases__, ensure proper generic inheritance")


def extract_origin(cls: type) -> type:
    """Extract __origin__ from generic type."""
    if origin := getattr(cls, "__origin__", None):
        return origin
    raise InvalidContainerInheritance(f"{cls} is not a generic type")


def make_resolution_order(dependencies: dict[str, Dependency]) -> list[str]:
    """Compute topological sort of dependency graph."""
    graph: DependencyGraph = {}
    for name, dep in dependencies.items():
        deps = set()
        for value in dep.kwargs.values():
            if isinstance(value, Dependency) and value.name:
                deps.add(value.name)
        graph[name] = deps

    in_degree = {name: len(deps) for name, deps in graph.items()}
    queue = [name for name, degree in in_degree.items() if degree == 0]
    queue.sort()
    ordered_deps = []

    while queue:
        node = queue.pop(0)
        ordered_deps.append(node)

        for name, deps in graph.items():
            if node in deps:
                in_degree[name] -= 1
                if in_degree[name] == 0 and name not in ordered_deps:
                    queue.append(name)

    if len(ordered_deps) != len(graph):
        pending = [name for name, degree in in_degree.items() if degree > 0]
        raise CircularDependencyError(f"Circular dependency detected: {pending} (resolved: {ordered_deps})")

    return ordered_deps


def make_cleanup(cleanup_fn: CleanupFn) -> Callable[[], Awaitable[None]]:
    """Wrap sync or async cleanup function as async."""
    if inspect.iscoroutinefunction(cleanup_fn):
        return cleanup_fn

    async def _wrapper() -> None:
        result = cleanup_fn()
        if inspect.iscoroutine(result):
            await result

    return _wrapper
