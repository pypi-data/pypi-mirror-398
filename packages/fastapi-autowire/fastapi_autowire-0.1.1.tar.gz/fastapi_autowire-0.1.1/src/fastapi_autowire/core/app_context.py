from typing import Type, TypeVar, Any, Dict, Iterable, List, Optional

from logging import getLogger

logger = getLogger(__name__)

T = TypeVar("T")


class AppContext:
    _instance: Optional["AppContext"] = None
    _services_map: Dict[Type, Any]
    _services_list: List[Any]

    def __init__(self, services: Iterable[Any]):
        logger.info("Initializing AppContext from service registry...")
        self._services_list = list(services)
        self._services_map = {type(service): service for service in self._services_list}
        logger.info(f"Loaded {len(self._services_map)} services into context.")

        # Set as singleton
        AppContext._instance = self

    @classmethod
    def current(cls) -> "AppContext":
        """Get the current AppContext instance"""
        if cls._instance is None:
            raise RuntimeError(
                "AppContext not initialized. Call this after app startup."
            )
        return cls._instance

    async def post_construct(self):
        logger.info("Running post-construction of services in AppContext...")
        for service in self._services_list:
            # Chiama initialize solo se il metodo esiste (duck typing)
            if hasattr(service, "post_construct"):
                await service.post_construct()
        logger.info("AppContext services initialized.")

    async def shutdown(self):
        logger.info("Shutting down AppContext...")
        for service in reversed(self._services_list):
            # Chiama shutdown/close solo se il metodo esiste (duck typing)
            if hasattr(service, "shutdown"):
                await service.shutdown()
            elif hasattr(service, "close"):
                await service.close()
        logger.info("AppContext shutdown complete.")

    def get(self, component_type: Type[T]) -> T:
        component = self._services_map.get(component_type)
        if component is None:
            raise ValueError(f"Component of type '{component_type.__name__}' not found")
        return component
