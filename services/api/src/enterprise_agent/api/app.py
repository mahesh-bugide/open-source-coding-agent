from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from enterprise_agent.agent.session_store import SessionService
from enterprise_agent.api.events import EventBus
from enterprise_agent.api.middleware import RequestContextMiddleware
from enterprise_agent.api.routes import router
from enterprise_agent.core.cache import create_cache
from enterprise_agent.core.config import get_settings
from enterprise_agent.core.logging import setup_logging
from enterprise_agent.core.metrics import MetricsStore
from enterprise_agent.db.session import Database

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title=settings.app_name)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.database = Database(settings)
    app.state.event_bus = EventBus()
    app.state.session_service = SessionService(settings)
    app.state.metrics = MetricsStore()
    app.state.run_tasks: dict[str, asyncio.Task[None]] = {}
    app.state.run_orchestrators: dict[str, object] = {}

    app.include_router(router)

    @app.on_event("startup")
    async def startup() -> None:
        try:
            await app.state.database.init_models()
        except Exception as exc:
            logger.warning("database_init_failed", extra={"error": str(exc)})
        app.state.cache = await create_cache(settings.redis_url)

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await app.state.database.dispose()

    return app
