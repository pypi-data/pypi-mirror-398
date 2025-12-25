"""
Centralized OpenTelemetry instrumentation and observability configuration.

This module provides a consistent way to configure distributed tracing and metrics
across all services in the GuardianHub ecosystem. It sets up:

1. Distributed Tracing:
   - Automatic instrumentation for FastAPI (incoming requests)
   - HTTPX client instrumentation (outgoing requests)
   - OTLP export for centralized trace collection

2. Metrics:
   - System and application metrics
   - OTLP export for metrics collection

3. Context Propagation:
   - Ensures trace context is propagated across service boundaries (CRITICAL for Langfuse integration)
   - Integrates with Langfuse for LLM/agent tracing

The module follows OpenTelemetry best practices and provides sensible defaults
while remaining configurable for different deployment environments.
"""

from typing import Optional, Union, Tuple, Any

# Imports for resilient HTTP session configuration
import requests
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter
)
from guardianhub.config.settings import settings
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from guardianhub import get_logger

logger = get_logger(__name__)

def configure_instrumentation(
    app,
    enable_console_export: bool = False,
    excluded_urls: str = "/health,/metrics",
    httpx_excluded_urls: Union[str, Tuple[str, ...]] = "/health,/metrics",
) -> None:
    """Configure OpenTelemetry instrumentation for the application.

    Args:
        app: The FastAPI application instance to instrument
        service_name: Name of the service for resource identification
        environment: Deployment environment (defaults to ENV var or 'development')
        service_version: Service version string (defaults to ENV var or '0.1.0')
        otlp_endpoint: Base URL for OTLP collector (defaults to OTEL_EXPORTER_OTLP_ENDPOINT)
        enable_console_export: If True, export traces/metrics to console
        excluded_urls: Comma-separated URLs to exclude from tracing
    """
    # 1. Resolve configuration variables
    environment = settings.endpoints.ENVIRONMENT
    otlp_endpoint = settings.endpoints.OTEL_OTLP_EXPORTER_ENDPOINT
    service_version = settings.service.version

    # Default to the known Kubernetes OTLP Collector service if the environment variable is missing.
    # We use the service-name.namespace:port format for cross-namespace communication.
    # default_otlp_endpoint = "http://otel-collector-service.monitoring.svc.cluster.local:4318"
    # otlp_endpoint = otlp_endpoint or os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    #
    # # Ensure the endpoint doesn't have a trailing slash, as the exporter needs the clean base URL
    # if otlp_endpoint:
    #     otlp_endpoint = otlp_endpoint.rstrip('/')

    logger.info(
        "Configuring OpenTelemetry instrumentation",
        extra={
            "service_name": settings.service.version,
            "environment": environment,
            "version": service_version,
            "otlp_endpoint": otlp_endpoint
        }
    )

    try:
        # # 2.5. Configure global context propagation using W3C Trace Context
        # set_global_textmap(TraceContextTextMapPropagator())
        # logger.info("Configured W3C Trace Context Propagator for context propagation")

        # 4. Configure metrics
        # _setup_metrics(resource, otlp_endpoint, enable_console_export)

        # 5. Instrument libraries
        # Preferred path: pass request/response hooks if supported
        FastAPIInstrumentor.instrument_app(
            app=app,
            tracer_provider=trace.get_tracer_provider(),
            excluded_urls=excluded_urls,
            exclude_spans=["receive", "send"],
            # server_request_hook=server_request_hook,
            # server_response_hook=server_response_hook,
            http_capture_headers_server_request = ["user-agent", "content-type"],  # Capture these request headers
            http_capture_headers_server_response = ["content-type", "content-length"]  # Capture these response header
        )
        logger.info("Instrumented FastAPI application", extra={"excluded_urls": excluded_urls})

        # Convert tuple of URLs to comma-separated string if needed
        excluded_urls_param = (
            ",".join(httpx_excluded_urls)
            if isinstance(httpx_excluded_urls, tuple)
            else httpx_excluded_urls
        )
        HTTPXClientInstrumentor().instrument(
            excluded_urls=excluded_urls_param,
            # request_hook=client_request_hook,
            # response_hook=client_response_hook,
        )

        logger.info("Instrumented HTTPX clients for outbound requests")
        logger.info("OpenTelemetry instrumentation configured successfully")

    except Exception as e:
        logger.error(
            "Failed to configure OpenTelemetry instrumentation. Continuing without full tracing/metrics.",
            exc_info=True,
            extra={"error": str(e)}
        )
        # Note: We catch the error but don't re-raise, allowing the application to start
        # but with reduced observability. This is typically safer than failing startup.

def _setup_metrics(resource: Resource, otlp_endpoint: Optional[str], console_export: bool) -> None:
    """Configure and initialize OpenTelemetry metrics."""
    logger.debug("Configuring metrics subsystem")

    metric_readers = []

    # 1. Console Exporter
    if console_export:
        # Wrap the ConsoleMetricExporter in a PeriodicExportingMetricReader
        metric_readers.append(
            PeriodicExportingMetricReader(
                ConsoleMetricExporter()
            )
        )
        logger.debug("Enabled console metrics export")

    # 2. OTLP Exporter
    if otlp_endpoint:
        try:
            # Create a resilient HTTP session for the exporter
            otlp_session = _create_otlp_session()
            full_otlp_metrics_endpoint = f"{otlp_endpoint}/v1/metrics"

            # FIX for 404 error: Revert the explicit path addition.
            # The Python SDK must be trusted to append '/v1/metrics' internally.
            otlp_exporter = OTLPMetricExporter(
                endpoint=full_otlp_metrics_endpoint,
                session=otlp_session
            )
            # Wrap the OTLPMetricExporter in a PeriodicExportingMetricReader
            metric_readers.append(
                PeriodicExportingMetricReader(otlp_exporter)
            )
            logger.info("Configured OTLP metrics exporter", extra={"endpoint": f"{otlp_endpoint}/v1/metrics (internal path)"})
        except Exception as e:
            # Only log the error, don't crash startup if the collector is unreachable
            logger.warning(
                "Failed to configure OTLP metrics exporter. Check endpoint and network access.",
                extra={"endpoint": otlp_endpoint, "error": str(e)}
            )

    if metric_readers:
        # Set the MeterProvider only if at least one reader is successfully configured
        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=metric_readers
            )
        )
    else:
        logger.info("No OTLP endpoint or console export enabled. Metrics will not be exported.")

def _create_otlp_session() -> requests.Session:
    """
    Creates a requests session configured for robust OTLP export retries.

    This helps handle transient network failures (like 'Connection refused'
    during service startup) in Kubernetes environments.
    """
    # Configure retry strategy: 5 total retries with 1 second backoff factor
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        # Includes connection errors and typical server errors
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(['POST']),
        # We allow the underlying connection errors to trigger retries
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    # Apply the resilient adapter to both HTTP and HTTPS protocols
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance with the given name."""
    return metrics.get_meter(name)
