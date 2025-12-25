import logging
import sys
from typing import Optional, Dict, Any, Type, List, Union
from guardianhub.config import settings

# Lazy import to avoid circular imports
HealthCheckFilter = None


class LoggerFactory:
    """Factory class for creating and managing logger instances with consistent configuration."""
    _initialized = False
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def initialize(cls) -> None:
        """Initialize the logging configuration if not already done."""
        if not cls._initialized:
            setup_logging()
            cls._initialized = True

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
        filters: Optional[List[Union[logging.Filter, Type[logging.Filter], dict]]] = None
    ) -> logging.Logger:
        """
        Get or create a logger with the given name and optional configuration.

        Args:
            name: Logger name (usually __name__ of the calling module)
            level: Optional log level (e.g., logging.INFO, logging.DEBUG)
            extra: Optional dictionary with additional context to add to log records
            filters: Optional list of filter instances, filter classes, or filter config dicts
                    (for filters that require initialization)

        Returns:
            Configured logger instance
        """
        cls.initialize()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            if level is not None:
                logger.setLevel(level)
            
            # Apply filters if any
            if filters:
                for f in filters:
                    if isinstance(f, logging.Filter):
                        logger.addFilter(f)
                    elif isinstance(f, type) and issubclass(f, logging.Filter):
                        logger.addFilter(f())
                    elif isinstance(f, dict):
                        # For filters that need initialization with parameters
                        filter_class = f.pop('class')
                        if isinstance(filter_class, type) and issubclass(filter_class, logging.Filter):
                            logger.addFilter(filter_class(**f))
            
            if extra:
                logger = logging.LoggerAdapter(logger, extra)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """
    Returns a pre-configured logger instance for a given name.
    
    This is a convenience wrapper around LoggerFactory.get_logger()
    """
    return LoggerFactory.get_logger(name)


def setup_logging():
    """
    Configures the root logger and the uvicorn.access logger using a standard format.
    Applies filters to reduce log noise.
    """
    # Lazy import to avoid circular imports
    global HealthCheckFilter
    if HealthCheckFilter is None:
        from .logging_filters import HealthCheckFilter as _HealthCheckFilter
        HealthCheckFilter = _HealthCheckFilter
    
    # Get log level from settings, default to INFO if not found
    try:
        log_level = settings.logging.level
    except AttributeError:
        log_level = 'INFO'
    numeric_level = logging.getLevelName(log_level.upper())
    
    # Configure health check filter for uvicorn access logs
    health_check_filters = []
    health_check_path = getattr(settings, 'excluded_urls', '')
    if health_check_path and HealthCheckFilter is not None:
        health_check_filters.append({
            'class': HealthCheckFilter,
            'path': health_check_path
        })

    # 1. Define a standard Python Formatter
    service_name = getattr(getattr(settings, 'service', None), 'name', 'guardianhub')
    standard_formatter = logging.Formatter(
        # Format: [2025-10-12 00:50:20] INFO: service_name.module_name - message
        fmt=f"[%(asctime)s] %(levelname)s: {service_name}.%(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 2. Setup the Root Logger (for ALL application logs, including lifespan)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers (critical for clean reconfiguration)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add the main application handler
    app_handler = logging.StreamHandler(sys.stdout)
    app_handler.setFormatter(standard_formatter)
    app_handler.setLevel(numeric_level)
    root_logger.addHandler(app_handler)

    # 3. Setup the Uvicorn Access Logger (for HTTP request logs)
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(numeric_level)
    # This prevents uvicorn logs from being duplicated by propagating to the root_logger
    uvicorn_access_logger.propagate = False

    # Clear existing uvicorn handlers
    for handler in uvicorn_access_logger.handlers[:]:
        uvicorn_access_logger.removeHandler(handler)
    
    # Apply health check filters
    for f in health_check_filters:
        if isinstance(f, dict):
            filter_class = f.pop('class')
            uvicorn_access_logger.addFilter(filter_class(**f))
        else:
            uvicorn_access_logger.addFilter(f)

    # Add the dedicated uvicorn handler
    uvicorn_handler = logging.StreamHandler(sys.stdout)
    uvicorn_handler.setFormatter(standard_formatter)

    # Assuming HealthCheckFilter is defined and available
    try:
        from .logging_filters import HealthCheckFilter
        uvicorn_handler.addFilter(HealthCheckFilter(path="/health"))
    except ImportError:
        # Fallback if the filter cannot be imported
        pass

    uvicorn_handler.setLevel(numeric_level)
    uvicorn_access_logger.addHandler(uvicorn_handler)

    # Get service name safely with fallback
    service_name = getattr(getattr(settings, 'service', None), 'name', 'guardianhub')
    
    # Final log message
    root_logger.info(
        f"Logging for '{service_name}' configured at level {logging.getLevelName(numeric_level)} with standard format."
    )