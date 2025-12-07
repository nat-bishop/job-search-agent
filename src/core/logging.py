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
    # Build shared processor chain for pre-processing
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,  # Merges trace_id from context
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Choose renderer based on json_logs setting
    renderer: structlog.types.Processor
    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog to use stdlib
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create formatter that renders structlog events
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Configure root logger with our formatter
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Bound logger with context support
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
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
