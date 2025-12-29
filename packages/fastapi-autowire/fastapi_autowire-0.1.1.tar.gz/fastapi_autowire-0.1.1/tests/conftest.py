import pytest
from fastapi_autowire.core import registry


@pytest.fixture(autouse=True)
def reset_registry():
    """
    Pulisce il registro dei servizi prima e dopo ogni test.
    Fondamentale perché il registro è una variabile globale.
    """
    # Salva lo stato originale (vuoto o pre-esistente)
    original_registry = list(registry.COMPONENT_REGISTRY)
    registry.COMPONENT_REGISTRY.clear()

    yield

    # Ripristina (opzionale, ma buona pratica)
    registry.COMPONENT_REGISTRY.clear()
    registry.COMPONENT_REGISTRY.extend(original_registry)