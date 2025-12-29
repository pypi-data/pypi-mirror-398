import inspect
from typing import Type, Any, Dict, List, get_type_hints, get_origin, get_args, Annotated
from .logger import logger
from .registry import COMPONENT_REGISTRY

def resolve_dependencies() -> List[Any]:
    logger.info("Starting dependency resolution...")
    instantiated: Dict[Type, Any] = {}
    resolving: set[Type] = set()

    service_map: Dict[Type, Type] = {
        item["key"]: item["class"] for item in COMPONENT_REGISTRY
    }

    def _find_type_by_name(name: str) -> Type:
        for registered_type in service_map.keys():
            if hasattr(registered_type, "__name__") and registered_type.__name__ == name:
                return registered_type
        return None

    def _resolve(key: Type) -> Any:
        if key in instantiated:
            return instantiated[key]

        if key not in service_map:
            type_name = key.__name__ if hasattr(key, "__name__") else str(key)
            raise TypeError(f"No service registered for type: {type_name}")

        if key in resolving:
            raise RuntimeError(f"Circular dependency for: {key.__name__}")

        resolving.add(key)
        cls_to_build = service_map[key]
        logger.debug(f"Resolving component: {cls_to_build.__name__}")

        dependencies = {}
        try:
            hints = get_type_hints(
                cls_to_build.__init__,
                globalns=inspect.getmodule(cls_to_build).__dict__ if inspect.getmodule(cls_to_build) else None
            )
        except Exception:
            hints = {}

        signature = inspect.signature(cls_to_build.__init__)
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            param_type = hints.get(param_name, param.annotation)

            if param_type is inspect.Parameter.empty:
                continue

            actual_type = param_type
            type_display_name = actual_type.__name__ if hasattr(actual_type, "__name__") else str(actual_type)
            logger.debug(f"  -> Found dependency '{param_name}' of type {type_display_name}")

            if get_origin(param_type) is Annotated:
                actual_type = get_args(param_type)[0]

            if isinstance(actual_type, str):
                resolved_type = _find_type_by_name(actual_type)
                if resolved_type:
                    actual_type = resolved_type

            if actual_type in service_map:
                dependencies[param_name] = _resolve(actual_type)
            elif inspect.isclass(actual_type) and param.default is inspect.Parameter.empty:
                # Se è una classe reale non registrata, allora è un errore
                raise TypeError(f"No service registered for type: {actual_type.__name__}")

        instance = cls_to_build(**dependencies)
        logger.debug(f"Successfully instantiated {cls_to_build.__name__}")
        instantiated[key] = instance
        resolving.remove(key)
        return instance

    for key in list(service_map.keys()):
        _resolve(key)

    return list(instantiated.values())