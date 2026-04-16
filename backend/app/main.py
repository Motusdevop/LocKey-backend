from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app.api import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db import DatabaseManager


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings)
    database_manager = DatabaseManager(app_settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database_manager = database_manager
        logger.info("Starting application")
        yield
        await database_manager.dispose()
        logger.info("Stopping application")

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.state.database_manager = database_manager
    app.include_router(api_router, prefix=app_settings.api_prefix)
    return app


app = create_app()
