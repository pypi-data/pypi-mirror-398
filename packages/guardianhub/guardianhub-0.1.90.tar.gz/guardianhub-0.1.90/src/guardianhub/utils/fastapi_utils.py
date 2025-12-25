"""Standardized FastAPI utilities for GuardianHub Microservices."""
import uuid
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from guardianhub.config.settings import settings
from guardianhub.logging.logging import get_logger
from guardianhub.observability.instrumentation import configure_instrumentation
from .app_state import AppState
from .metrics import setup_metrics, get_metrics_registry

logger = get_logger(__name__)

def initialize_guardian_app(app: FastAPI) -> None:
    """
    The 'Golden Path' for service initialization.

    This single call handles:
    1. Settings & Env discovery
    2. OpenTelemetry Tracing (Incoming & Outgoing)
    3. Prometheus Metrics setup
    4. Custom GuardianHub Middleware (Tracing, Timing, Logging)
    5. Standardized Health & Metrics endpoints
    """
    # 1. Initialize App State
    app_state = AppState()
    app_state.set("startup_time", datetime.now())
    app_state.set("active_requests", 0)
    app_state.set("total_requests", 0)
    app.state.app_state = app_state

    # Add this "Gold Standard" Startup Log
    banner = f"""
        ╔════════════════════════════════════════════════════════════════╗
        ║  GUARDIANHUB SDK INITIALIZED                                   ║
        ╠════════════════════════════════════════════════════════════════╣
        ║ SERVICE:     {settings.service.name:<49} ║
        ║ ENVIRONMENT: {settings.endpoints.ENVIRONMENT:<49} ║
        ║ OTEL ENDPT:  {settings.endpoints.OTEL_OTLP_EXPORTER_ENDPOINT:<49} ║
        ║ LANGFUSE_OTLP_TRACES_ENDPOINT:  {settings.endpoints.LANGFUSE_OTLP_TRACES_ENDPOINT:<49} ║
        ║ LANGFUSE_HOST:  {settings.endpoints.LANGFUSE_HOST:<49} ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    for line in banner.strip().split('\n'):
        logger.info(line)

    # 2. Configure OpenTelemetry (OTEL)
    # Automatically uses settings.endpoints.OTEL_EXPORTER_OTLP_ENDPOINT
    configure_instrumentation(app)

    # 3. Setup Prometheus Metrics
    metrics_map = setup_metrics(settings.service.name)

    # 4. Add Standard Middleware
    _add_standard_middleware(app, metrics_map, app_state)

    # 5. Attach System Endpoints (/health, /metrics)
    _attach_system_endpoints(app, app_state)

    logger.info(f"GuardianHub Service [{settings.service.name}] successfully initialized.")

def _add_standard_middleware(app: FastAPI, metrics: Dict[str, Any], app_state: AppState):
    """Internal: Configures CORS and Observability logic."""

    # CORS Logic - Pulling from our dynamic settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Can be refined in settings.py later
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        # Skip logic for internal paths
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Start tracking
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()

        metrics['active_requests'].inc()
        app_state.increment("active_requests")
        app_state.increment("total_requests")

        try:
            response = await call_next(request)

            # Calculate Duration
            duration_ms = (time.time() - start_time) * 1000

            # Update Prometheus
            metrics['request_latency'].labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration_ms / 1000)

            metrics['request_count'].labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()

            # Add Standard Headers
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Request-ID"] = request_id

            logger.info(
                f"{request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {duration_ms:.2f}ms"
            )
            return response

        except Exception as e:
            logger.error(f"Uncaught Exception in {request.url.path}: {str(e)}", exc_info=True)
            raise
        finally:
            metrics['active_requests'].dec()
            app_state.decrement("active_requests")

def _attach_system_endpoints(app: FastAPI, app_state: AppState):
    """Internal: Sets up the /health and /metrics routes."""

    @app.get("/health", tags=["System"])
    async def health():
        startup_time = app_state.get("startup_time")
        uptime = (datetime.now() - startup_time).total_seconds()
        return {
            "status": "healthy",
            "service": settings.service.name,
            "environment": settings.endpoints.ENVIRONMENT,
            "version": settings.service.id.split('-')[-1], # Example version extraction
            "uptime_seconds": int(uptime),
            "stats": {
                "active_requests": app_state.get("active_requests", 0),
                "total_requests": app_state.get("total_requests", 0)
            }
        }

    @app.get("/metrics", tags=["System"])
    async def metrics():
        registry = get_metrics_registry()
        return Response(
            content=generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST
        )