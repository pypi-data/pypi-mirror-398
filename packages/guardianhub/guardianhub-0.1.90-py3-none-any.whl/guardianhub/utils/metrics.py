"""Prometheus metrics utilities for Guardian Hub services."""
from typing import Any, Dict, Optional
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Global registry instance
_METRICS_REGISTRY = None
_METRICS_INITIALIZED = False


def setup_metrics(service_name: str) -> Dict[str, Any]:
    """Set up Prometheus metrics for the application.

    Args:
        service_name: Name of the service for metrics namespace
        
    Returns:
        Dict containing the metric objects
    """
    global _METRICS_REGISTRY, _METRICS_INITIALIZED

    # Initialize registry if not already done
    if _METRICS_REGISTRY is None:
        _METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

    namespace = service_name.replace('-', '_')
    metrics = {}

    # Only register metrics if not already initialized
    if not _METRICS_INITIALIZED:
        metrics.update({
            'request_count': Counter(
                f'{namespace}_requests_total',
                'Total number of requests received',
                ['method', 'endpoint', 'status_code'],
                registry=_METRICS_REGISTRY
            ),
            'request_latency': Histogram(
                f'{namespace}_request_latency_seconds',
                'Request latency in seconds',
                ['method', 'endpoint'],
                registry=_METRICS_REGISTRY
            ),
            'active_requests': Gauge(
                f'{namespace}_active_requests',
                'Number of active requests',
                registry=_METRICS_REGISTRY
            )
        })
        _METRICS_INITIALIZED = True
    
    return metrics


def get_metrics_registry() -> Optional[CollectorRegistry]:
    """Get the global metrics registry.
    
    Returns:
        The global metrics registry if initialized, None otherwise
    """
    return _METRICS_REGISTRY
