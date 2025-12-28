"""Cleanup registration decorator."""

from __future__ import annotations

from typing import Callable

from .defaults import CLEANUP_ATTR_NAME
from .types import CleanupGetter, ResourceFactory


def on_exit(cleanup_getter: CleanupGetter) -> Callable[[ResourceFactory], ResourceFactory]:
    """Register cleanup callback for resource factory.

    Args:
        cleanup_getter: Function extracting cleanup method from instance.

    Returns:
        Decorated factory function.
    """

    def decorator(factory: ResourceFactory) -> ResourceFactory:
        setattr(factory, CLEANUP_ATTR_NAME, cleanup_getter)
        return factory

    return decorator


__all__ = [
    "on_exit",
]
