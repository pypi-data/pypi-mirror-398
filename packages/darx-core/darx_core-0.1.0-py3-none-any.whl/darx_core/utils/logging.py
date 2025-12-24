"""
Structured logging utility for DARX services

This module provides consistent JSON-formatted logging with correlation IDs
across all DARX services.
"""
import logging
import sys
from typing import Optional
import structlog
from structlog.types import EventDict, Processor


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add correlation_id to log entries if available in context.

    This processor looks for 'correlation_id' in the event_dict and ensures it's always present.
    """
    # Check if correlation_id is already in the event dict
    if 'correlation_id' not in event_dict:
        # Try to get from thread-local context (if set elsewhere)
        event_dict['correlation_id'] = None

    return event_dict


def setup_logging(
    service_name: str,
    log_level: str = 'INFO',
    json_format: bool = True
) -> structlog.BoundLogger:
    """
    Configure structured JSON logging for a DARX service.

    Args:
        service_name: Name of the service (e.g., 'darx-reasoning')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to output JSON logs (True) or human-readable (False)

    Returns:
        BoundLogger: Configured structlog logger for the service

    Example:
        >>> logger = setup_logging('darx-reasoning')
        >>> logger.info("Server started", port=8080)
        {"event": "Server started", "level": "info", "logger": "darx-reasoning",
         "timestamp": "2025-12-21T10:30:45.123Z", "port": 8080}
    """
    # Convert log_level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format='%(message)s',
        stream=sys.stdout,
        level=numeric_level,
    )

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_correlation_id,  # Add correlation_id to all logs
    ]

    # Add JSON renderer for production, console renderer for development
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    # Create logger for this service
    logger = structlog.get_logger(service_name)
    logger.info("Logging configured", service=service_name, level=log_level)

    return logger


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Optional logger name. If not provided, returns root logger.

    Returns:
        BoundLogger: Configured structlog logger

    Example:
        >>> logger = get_logger('my_module')
        >>> logger.info("Processing request", user_id=123)
    """
    return structlog.get_logger(name)


# Example usage and documentation
if __name__ == "__main__":
    # Example 1: Setup logging for a service
    logger = setup_logging('darx-example', log_level='INFO', json_format=False)
    logger.info("Service started", port=8080, version='1.0.0')

    # Example 2: Log with correlation ID
    logger = logger.bind(correlation_id='req-abc123')
    logger.info("Processing request", user_id=42, action='create_site')

    # Example 3: Log an error with exception info
    try:
        result = 1 / 0
    except ZeroDivisionError:
        logger.error("Division error occurred", exc_info=True)

    # Example 4: Structured context
    logger.info(
        "Database query completed",
        query_type='SELECT',
        table='clients',
        duration_ms=45,
        rows_returned=100
    )
