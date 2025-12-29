from typing import Type, Callable, TypeVar, Generic, Annotated
from fastapi import Request, Depends
from .app_context import AppContext

T = TypeVar("T")


def get_app_context(request: Request) -> AppContext:
    return request.app.state.app_context


def provider_for(component_type: Type[T]) -> Callable[..., T]:
    """
    Questa è una factory di dipendenze.
    Restituisce una funzione di dipendenza che sa come estrarre
    un componente specifico dall'AppContext.
    """

    def get_component(context: AppContext = Depends(get_app_context)) -> T:
        return context.get(component_type)

    return get_component