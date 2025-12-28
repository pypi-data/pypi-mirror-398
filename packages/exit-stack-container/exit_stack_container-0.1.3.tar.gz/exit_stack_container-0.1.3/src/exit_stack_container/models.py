"""Base resource models for DI containers."""

from __future__ import annotations

from msgspec_settings import BaseSettings


class BaseResources[T = BaseSettings]:
    """Base resource container with settings"""

    settings: T


__all__ = [
    "BaseResources",
]
