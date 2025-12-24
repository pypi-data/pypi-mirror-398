import asyncio
import logging
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import cache, discovery, fusion, matching, query, star_schema, system
from src.core.infrastructure.config import settings
from src.core.middleware.middleware import RequestIDMiddleware
from src.core.middleware.rate_limit import RateLimitMiddleware
from src.core.middleware.request_limit import RequestSizeLimitMiddleware
from src.core.monitoring.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.

    Handles startup and shutdown events for graceful shutdown.
    """
    # Startup
    logger.info("SchemaFusion API starting up...")

    # Initialize database
    try:
        from src.core.infrastructure.models import init_db

        init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}")

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    yield

    # Shutdown
    logger.info("SchemaFusion API shutting down...")

    # Wait for in-flight requests to complete (with timeout)
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=30.0)
        logger.info("Graceful shutdown completed")
    except TimeoutError:
        logger.warning("Shutdown timeout reached, forcing shutdown")

    # Close connections
    try:
        from src.core.query.trino_client import trino_client

        if hasattr(trino_client, "_pool") and trino_client._pool:
            trino_client._pool.close_all()
            logger.info("Trino connection pool closed")
    except Exception as exc:
        logger.warning(f"Error closing connections: {exc}")


def create_app() -> FastAPI:
    """
    Factory for the SchemaFusion headless API.

    This orchestrates query planning, source selection, and
    execution against Trino and underlying data sources.
    """
    app = FastAPI(
        title="SchemaFusion Headless API",
        version="0.16.0",
        description="Middleware layer for EasyBDI 2.0-style data virtualization and federation.",
        lifespan=lifespan,
    )

    # Add CORS middleware (if enabled) - should be first
    if settings.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add request size limiting middleware
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size_mb=settings.max_request_size_mb,
    )

    # Add middleware for request ID tracking
    app.add_middleware(RequestIDMiddleware)

    # Add rate limiting middleware
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.rate_limit_per_minute,
        )

    # Add Prometheus metrics
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app)

        # Import custom metrics to register them
        import src.core.monitoring.metrics  # noqa: F401
    except ImportError:
        # Prometheus instrumentation is optional
        pass

    # Register routers
    app.include_router(system.router)
    app.include_router(discovery.router)
    app.include_router(matching.router)
    app.include_router(fusion.router)
    app.include_router(query.router)
    app.include_router(cache.router)
    app.include_router(star_schema.router)  # Star schema endpoints

    # Events router (recent activity for dashboard)
    try:
        from src.api import events

        app.include_router(events.router)
        logger.info("Events API enabled")
    except ImportError as exc:
        logger.warning(f"Events API not available: {exc}")

    # Register connector management router
    try:
        from src.api import connectors

        app.include_router(connectors.router)
        logger.info("Connector management API enabled")
    except ImportError as exc:
        logger.warning(f"Connector management API not available: {exc}")

    # Register Cube.js router if enabled
    if settings.cubejs_enabled:
        try:
            from src.api import cubejs

            app.include_router(cubejs.router)
            logger.info("Cube.js integration enabled")
        except ImportError as exc:
            logger.warning(f"Cube.js integration not available: {exc}")

    return app


app = create_app()
