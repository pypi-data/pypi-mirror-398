from typing import Type, TypeVar, Annotated, Generic
from fastapi import Depends
from fastapi_autowire.core.dependencies import provider_for

T = TypeVar("T")

class Autowired(Generic[T]):
    """
    Dependency Injection marker.
    Usage:
        repo: Autowired[UserRepository]
    """
    def __class_getitem__(cls, item: Type[T]):
        return Annotated[item, Depends(provider_for(item))]