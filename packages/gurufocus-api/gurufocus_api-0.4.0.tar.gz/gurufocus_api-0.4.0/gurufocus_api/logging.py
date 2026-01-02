"""Structured logging configuration for the GuruFocus API client.

Provides environment-aware logging with JSON output for production
and pretty console output for development. Supports OpenTelemetry
trace context injection when available.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any, Literal

import structlog

if TYPE_CHECKING:
    from .config import GuruFocusSettings

# Check if OpenTelemetry is available
_OTEL_AVAILABLE = False
try:
    from opentelemetry import trace

    _OTEL_AVAILABLE = True
except ImportError:
    trace = None  # type: ignore[assignment]


def _add_otel_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add OpenTelemetry trace context to log events.

    Injects trace_id and span_id from the current OpenTelemetry context
    if available. This enables log correlation with distributed traces.
    """
    if not _OTEL_AVAILABLE or trace is None:
        return event_dict

    span = trace.get_current_span()
    if span is None:
        return event_dict

    ctx = span.get_span_context()
    if ctx is None or not ctx.is_valid:
        return event_dict

    # Format as hex strings (standard OpenTelemetry format)
    event_dict["trace_id"] = format(ctx.trace_id, "032x")
    event_dict["span_id"] = format(ctx.span_id, "016x")

    # Include trace flags if sampling decision is recorded
    if ctx.trace_flags:
        event_dict["trace_flags"] = ctx.trace_flags

    return event_dict


def configure_logging(
    log_level: str = "INFO",
    log_format: Literal["json", "console"] = "console",
    *,
    force_reconfigure: bool = False,
) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - 'json' for production, 'console' for development
        force_reconfigure: If True, reconfigure even if already configured
    """
    if structlog.is_configured() and not force_reconfigure:
        return

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_otel_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        renderer: Any = structlog.processors.JSONRenderer()
        processors: list[Any] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ]
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        processors = [*shared_processors, renderer]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,  # MCP uses stdout for JSON-RPC, so logs must go to stderr
        level=getattr(logging, log_level.upper()),
        force=force_reconfigure,
    )

    for handler in logging.root.handlers:
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=renderer,
                foreign_pre_chain=shared_processors[:-1],
            )
        )


def configure_from_settings(settings: GuruFocusSettings) -> None:
    """Configure logging from GuruFocusSettings.

    Args:
        settings: Configuration settings object
    """
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.

    This is a convenience wrapper that can be used as a drop-in replacement
    for logging.getLogger().

    Args:
        name: Logger name (typically __name__)

    Returns:
        Bound structlog logger
    """
    return structlog.stdlib.get_logger(name)


def is_otel_available() -> bool:
    """Check if OpenTelemetry is available.

    Returns:
        True if OpenTelemetry is installed and can be used for tracing
    """
    return _OTEL_AVAILABLE
