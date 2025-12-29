from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_autowire.core.registry import component
from fastapi_autowire.core.lifespan import lifespan

HOOKS_CALLED = {"post_construct": False, "shutdown": False}

def test_lifespan_hooks():
    # Reset dei flag
    HOOKS_CALLED["post_construct"] = False
    HOOKS_CALLED["shutdown"] = False

    # Spostiamo la registrazione e l'app dentro il test per evitare conflitti con conftest.py
    @component
    class LifecycleService:
        async def post_construct(self):
            HOOKS_CALLED["post_construct"] = True

        async def shutdown(self):
            HOOKS_CALLED["shutdown"] = True

    # Crea l'app QUI
    app = FastAPI(lifespan=lifespan)

    with TestClient(app) as client:
        assert HOOKS_CALLED["post_construct"] is True
        assert HOOKS_CALLED["shutdown"] is False

    assert HOOKS_CALLED["shutdown"] is True