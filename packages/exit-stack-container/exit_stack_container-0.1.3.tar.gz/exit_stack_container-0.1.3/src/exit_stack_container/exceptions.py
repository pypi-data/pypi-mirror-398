"""Container-specific exceptions."""


class ContainerError(Exception):
    """Base exception for all container errors"""


class CircularDependencyError(ContainerError):
    """Circular dependency detected during resolution"""


class DependencyNotResolvedError(ContainerError):
    """Dependency referenced before resolution"""


class ContainerReuseError(ContainerError):
    """Container instance re-entered before exit"""


class InvalidContainerInheritance(ContainerError):
    """Invalid generic inheritance structure"""


__all__ = [
    "ContainerError",
    "CircularDependencyError",
    "DependencyNotResolvedError",
    "ContainerReuseError",
    "InvalidContainerInheritance",
]
