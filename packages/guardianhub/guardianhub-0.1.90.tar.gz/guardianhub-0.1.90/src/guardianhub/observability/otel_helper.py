from typing import Dict, Any, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import (
    Resource,
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_NAMESPACE,
    DEPLOYMENT_ENVIRONMENT
)
from opentelemetry.sdk.trace import TracerProvider

def configure_resource(
    service_name: str,
    service_namespace: str = "guardianhub",
    service_version: str = "0.1.0",
    service_language: str = "python",
    environment: str = "development",
    resource_attributes: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Configure the global tracer provider with the given service details.

    This should be called once at application startup.

    Args:
        service_name: Name of the service (e.g., 'aura-llm-service')
        service_namespace: Namespace for the service (default: 'guardianhub')
        service_version: Version of the service (default: '0.1.0')
        environment: Deployment environment (e.g., 'development', 'staging', 'production')
        resource_attributes: Additional attributes to add to the resource
        service_language: Always set to 'python'
    """
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({
                SERVICE_NAME: service_name,
                SERVICE_NAMESPACE: service_namespace,
                SERVICE_VERSION: service_version,
                DEPLOYMENT_ENVIRONMENT: environment,
                # OTEL ignores custom resource attributes, keeping it for future reference
                "service.language": service_language,
                **(resource_attributes or {})
            })
        )
    )

