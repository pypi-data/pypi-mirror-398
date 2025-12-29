import pytest
from fastapi_autowire.core.registry import component
from fastapi_autowire.core.resolver import resolve_dependencies


def test_simple_dependency_resolution():
    """Testa che A venga creato prima di B se B dipende da A."""

    @component
    class ServiceA:
        pass

    @component
    class ServiceB:
        def __init__(self, a: ServiceA):
            self.a = a

    services = resolve_dependencies()

    # Verifica che siano stati creati entrambi
    assert len(services) == 2
    # Trova le istanze
    instance_a = next(s for s in services if isinstance(s, ServiceA))
    instance_b = next(s for s in services if isinstance(s, ServiceB))

    # Verifica l'iniezione
    assert instance_b.a is instance_a


def test_circular_dependency_detection():
    """Testa che il sistema vada in panico se c'è un ciclo A -> B -> A."""

    @component
    class ServiceA:
        def __init__(self, b: "ServiceB"): # Forward ref per il test
            pass

    @component
    class ServiceB:
        def __init__(self, a: ServiceA):
            pass

    # Deve sollevare un errore
    with pytest.raises(RuntimeError, match="Circular dependency"):
        resolve_dependencies()


def test_missing_dependency():
    """Testa se un servizio richiede una classe NON registrata."""

    class UnregisteredService:
        pass

    @component
    class MyService:
        def __init__(self, dep: UnregisteredService):
            pass

    # Nota: A seconda di come abbiamo implementato il resolver,
    # potrebbe ignorarlo o lanciare errore. Nel nostro design rigoroso:
    with pytest.raises(TypeError, match="No service registered"):
        resolve_dependencies()