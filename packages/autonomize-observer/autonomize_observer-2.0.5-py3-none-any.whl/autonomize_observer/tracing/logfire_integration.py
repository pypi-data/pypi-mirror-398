"""Logfire integration - thin wrapper to configure and use Pydantic Logfire.

Logfire provides:
- Full OTEL tracing (spans, traces, context propagation)
- OpenAI instrumentation via logfire.instrument_openai()
- Anthropic instrumentation via logfire.instrument_anthropic()
- LLM cost tracking built-in
- FastAPI, Django, Flask instrumentation
- Database instrumentation (SQLAlchemy, Psycopg, etc.)

We use Logfire as the core tracing engine and only add:
- Kafka export for downstream consumers
- Audit logging with Keycloak support
- Flow/Langflow-specific context
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import logfire as logfire_module

logger = logging.getLogger(__name__)

_logfire_instance: logfire_module.Logfire | None = None


def configure_logfire(
    service_name: str = "autonomize-observer",
    service_version: str = "2.0.0",
    environment: str | None = None,
    send_to_logfire: bool = False,
    console: bool | dict[str, Any] | None = None,
    additional_span_processors: list[Any] | None = None,
    **kwargs: Any,
) -> logfire_module.Logfire:
    """Configure and return a Logfire instance.

    This wraps logfire.configure() with sensible defaults for our use case.
    By default, send_to_logfire=False so data is NOT sent to Pydantic cloud.

    Args:
        service_name: Name of the service (maps to OTEL service.name)
        service_version: Version of the service
        environment: Deployment environment (production, staging, dev)
        send_to_logfire: Whether to send data to Pydantic Logfire cloud.
            Default False - data stays local or goes to your exporters.
        console: Console output settings. Set to False to disable,
            True for default, or dict for custom settings.
        additional_span_processors: Custom OTEL span processors to add
            (e.g., for Kafka export)
        **kwargs: Additional arguments passed to logfire.configure()

    Returns:
        Configured Logfire instance
    """
    global _logfire_instance

    import logfire

    # Build configuration
    config: dict[str, Any] = {
        "service_name": service_name,
        "service_version": service_version,
        "send_to_logfire": send_to_logfire,
    }

    if environment:
        config["environment"] = environment

    if console is not None:
        config["console"] = console

    if additional_span_processors:
        config["additional_span_processors"] = additional_span_processors

    # Merge with any additional kwargs
    config.update(kwargs)

    # Configure logfire
    logfire.configure(**config)

    _logfire_instance = logfire
    logger.info(
        "Logfire configured",
        extra={
            "service_name": service_name,
            "send_to_logfire": send_to_logfire,
        },
    )

    return logfire


def get_logfire() -> logfire_module.Logfire:
    """Get the configured Logfire instance.

    Returns:
        The Logfire instance

    Raises:
        RuntimeError: If Logfire has not been configured
    """
    if _logfire_instance is None:
        raise RuntimeError("Logfire not configured. Call configure_logfire() first.")
    return _logfire_instance


def instrument_llms(
    openai: bool = True,
    anthropic: bool = True,
    **kwargs: Any,
) -> None:
    """Instrument LLM clients for automatic tracing.

    Logfire provides one-line instrumentation that automatically captures:
    - Request/response details
    - Token usage counts
    - Streaming metrics
    - Errors and exceptions

    Args:
        openai: Whether to instrument OpenAI clients
        anthropic: Whether to instrument Anthropic clients
        **kwargs: Additional provider-specific options
    """
    lf = get_logfire()

    if openai:
        try:
            lf.instrument_openai(**kwargs.get("openai_options", {}))
            logger.info("OpenAI instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument OpenAI: {e}")

    if anthropic:
        try:
            lf.instrument_anthropic(**kwargs.get("anthropic_options", {}))
            logger.info("Anthropic instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument Anthropic: {e}")


def instrument_web_framework(
    framework: str,
    **kwargs: Any,
) -> None:
    """Instrument a web framework.

    Args:
        framework: One of 'fastapi', 'flask', 'django', 'starlette'
        **kwargs: Framework-specific options
    """
    lf = get_logfire()

    instrumenters = {
        "fastapi": "instrument_fastapi",
        "flask": "instrument_flask",
        "django": "instrument_django",
        "starlette": "instrument_starlette",
    }

    method_name = instrumenters.get(framework.lower())
    if not method_name:
        raise ValueError(
            f"Unknown framework: {framework}. "
            f"Supported: {list(instrumenters.keys())}"
        )

    try:
        method = getattr(lf, method_name)
        method(**kwargs)
        logger.info(f"{framework} instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument {framework}: {e}")


def instrument_database(
    database: str,
    **kwargs: Any,
) -> None:
    """Instrument a database client.

    Args:
        database: One of 'sqlalchemy', 'psycopg', 'asyncpg', 'pymongo', etc.
        **kwargs: Database-specific options
    """
    lf = get_logfire()

    instrumenters = {
        "sqlalchemy": "instrument_sqlalchemy",
        "psycopg": "instrument_psycopg",
        "asyncpg": "instrument_asyncpg",
        "pymongo": "instrument_pymongo",
        "redis": "instrument_redis",
    }

    method_name = instrumenters.get(database.lower())
    if not method_name:
        raise ValueError(
            f"Unknown database: {database}. " f"Supported: {list(instrumenters.keys())}"
        )

    try:
        method = getattr(lf, method_name)
        method(**kwargs)
        logger.info(f"{database} instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument {database}: {e}")
