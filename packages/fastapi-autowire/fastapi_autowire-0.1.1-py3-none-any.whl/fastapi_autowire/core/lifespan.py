from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from .app_context import AppContext
from .resolver import resolve_dependencies
from .logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Loading application context")

    instantiated_services = resolve_dependencies()

    app.state.app_context = AppContext(services=instantiated_services)
    logger.debug("Loaded application context")

    logger.debug("Running post_construct of services in AppContext...")
    await app.state.app_context.post_construct()
    logger.debug("Post-configuration services initialized.")

    yield

    logger.debug("Shutting down application")
    await app.state.app_context.shutdown()
    logger.debug("Application shutted down successfully")
