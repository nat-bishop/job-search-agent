"""Structured logging with Langfuse trace correlation.

Uses structlog for structured key-value logging. All logs automatically
include trace_id when bound, enabling correlation with Langfuse traces.

Usage:
    from src.core.logging import get_logger, bind_trace_id

    logger = get_logger(__name__)
    bind_trace_id(trace_id)  # All subsequent logs include trace_id

    logger.info("operation_start", key="value")
    logger.warning("something_failed", error=str(e))
"""

import logging
import sys
from pathlib import Path

import structlog


def setup_logging(json_logs: bool = False, log_file: str | None = None) -> None:
    """Configure structlog for the application.

    Args:
        json_logs: If True, output JSON format (for machine parsing)
        log_file: Optional file path to write logs (creates parent dirs)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Add file handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        logging.getLogger().addHandler(file_handler)

    # Build processor chain
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # Merges trace_id from context
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Bound logger with context support
    """
    logger: structlog.BoundLogger = structlog.get_logger(name)
    return logger


def bind_trace_id(trace_id: str) -> None:
    """Bind trace_id to all subsequent logs in this async context.

    Call this at the start of an agent run to correlate all logs
    with the Langfuse trace. Uses contextvars so it's async-safe.

    Args:
        trace_id: The Langfuse trace ID (32-char hex string)
    """
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_trace_context() -> None:
    """Clear trace context variables.

    Call at the end of an agent run to clean up context.
    """
    structlog.contextvars.clear_contextvars()
