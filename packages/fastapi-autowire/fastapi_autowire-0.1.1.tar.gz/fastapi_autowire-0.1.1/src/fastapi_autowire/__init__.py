from .core.registry import (
    component,
    service,
    repository,
    configuration,
    provider
)
from .core.lifespan import lifespan
from .types import Autowired

__all__ = [
    "component",
    "service",
    "repository",
    "configuration",
    "provider",
    "lifespan",
    "Autowired"
]