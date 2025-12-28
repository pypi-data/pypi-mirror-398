"""Type aliases for container module."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

ResourceFactory: TypeAlias = Callable[..., Any]
CleanupFn: TypeAlias = Callable[[], None] | Callable[[], Awaitable[None]]
CleanupGetter: TypeAlias = Callable[[Any], CleanupFn]
ResolvedDeps: TypeAlias = dict[str, Any]
DependencyGraph: TypeAlias = dict[str, set[str]]

__all__ = [
    "ResourceFactory",
    "CleanupFn",
    "CleanupGetter",
    "ResolvedDeps",
    "DependencyGraph",
]
