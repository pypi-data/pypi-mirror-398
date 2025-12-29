from logging import getLogger
from typing import Type, Any, Dict, List

COMPONENT_REGISTRY: List[Dict[str, Any]] = []

logger = getLogger(__name__)

def _register_component_internal(cls: Type[Any], key: Type[Any] = None) -> Type[Any]:
    actual_key = key if key is not None else cls
    logger.info(f"Registering component: {cls.__name__} as {actual_key.__name__}")
    COMPONENT_REGISTRY.append({"class": cls, "key": actual_key})
    return cls

# --- BASE DECORATOR ---
def component(_cls: Type[Any] = None, *, as_type: Type[Any] = None) -> Any:
    def wrapper(cls: Type[Any]) -> Type[Any]:
        return _register_component_internal(cls, key=as_type)

    if _cls is None:
        return wrapper
    return wrapper(_cls)

# --- SEMANTIC ALIASES ---
service = component
repository = component
configuration = component
provider = component