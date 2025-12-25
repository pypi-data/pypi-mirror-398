"""GuardianHub SDK - Unified SDK for Local AI Guardian

This package provides core functionality for the GuardianHub platform,
including logging, metrics, and FastAPI utilities.
"""

# Version
from ._version import __version__  # version exported for users
# Core functionality
from .logging import get_logger, setup_logging
from .observability.instrumentation import configure_instrumentation
from .utils.app_state import AppState
from .utils.fastapi_utils import initialize_guardian_app
from .utils.metrics import setup_metrics, get_metrics_registry

# Public API
__all__ = [
    # Version
    "__version__",
    
    # Logging
    "get_logger",
    "setup_logging",

    "AppState",
    "setup_metrics","get_metrics_registry",
    "setup_middleware","setup_health_endpoint","setup_metrics_endpoint",
    "configure_instrumentation",
    "initialize_guardian_app"
]