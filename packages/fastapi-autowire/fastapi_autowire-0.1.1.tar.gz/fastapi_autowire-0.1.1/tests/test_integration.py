from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_autowire import component, Autowired, lifespan


app = FastAPI(lifespan=lifespan)


def test_autowired_endpoint():
    # 1. Definisci i servizi
    @component
    class Repository:
        def get_data(self):
            return "data from db"

    @component
    class Service:
        def __init__(self, repo: Repository):
            self.repo = repo

        def logic(self):
            return self.repo.get_data().upper()

    # 2. Configura l'App

    # 3. Definisci l'endpoint con Autowired
    @app.get("/test")
    def endpoint(svc: Autowired[Service]):
        return {"result": svc.logic()}

    # 4. Esegui la richiesta
    with TestClient(app) as client:
        response = client.get("/test")

        assert response.status_code == 200
        assert response.json() == {"result": "DATA FROM DB"}