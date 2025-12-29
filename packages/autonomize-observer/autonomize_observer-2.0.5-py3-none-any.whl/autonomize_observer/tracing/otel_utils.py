"""OTEL/Logfire utilities for tracing.

This module provides shared OTEL configuration and span management,
eliminating duplication across tracers.

Usage:
    from autonomize_observer.tracing.otel_utils import OTELManager

    otel = OTELManager(service_name="my-service", send_to_logfire=False)
    with otel.span("my-operation", key="value") as span:
        do_work()
        span.set_attribute("result", "success")
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

from autonomize_observer.core.imports import LOGFIRE_AVAILABLE, logfire

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class OTELManager:
    """Manages OTEL/Logfire configuration and span creation.

    This class provides a centralized way to:
    1. Configure Logfire once per service
    2. Create spans with consistent patterns
    3. Handle unavailable Logfire gracefully

    Example:
        ```python
        otel = OTELManager(service_name="my-service")

        # Create spans using context manager
        with otel.span("operation", attr1="value1") as span:
            result = do_work()
            if span:
                span.set_attribute("result", result)
        ```
    """

    # Class-level tracking of configuration
    _configured_services: set[str] = set()

    def __init__(
        self,
        service_name: str,
        send_to_logfire: bool = False,
    ) -> None:
        """Initialize OTEL manager.

        Args:
            service_name: Service name for OTEL spans
            send_to_logfire: Whether to send traces to Logfire cloud
        """
        self.service_name = service_name
        self.send_to_logfire = send_to_logfire
        self._configured = False
        self._available = LOGFIRE_AVAILABLE

        # Configure on initialization
        self._configure()

    def _configure(self) -> None:
        """Configure Logfire if available and not already configured."""
        if not self._available or not logfire:
            logger.debug(
                f"Logfire not available for {self.service_name} - "
                "tracing will be local only"
            )
            return

        # Only configure once per service name (Logfire global state)
        if self.service_name in OTELManager._configured_services:
            logger.debug(f"Logfire already configured for {self.service_name}")
            self._configured = True
            return

        try:
            logfire.configure(
                service_name=self.service_name,
                send_to_logfire=self.send_to_logfire,
            )
            OTELManager._configured_services.add(self.service_name)
            self._configured = True
            logger.debug(f"Logfire configured for {self.service_name}")
        except Exception as e:
            logger.warning(f"Failed to configure Logfire for {self.service_name}: {e}")
            self._configured = False

    @property
    def is_available(self) -> bool:
        """Check if OTEL tracing is available and configured."""
        return self._available and self._configured

    @contextmanager
    def span(
        self,
        name: str,
        tags: list[str] | None = None,
        **attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create an OTEL span.

        Args:
            name: Span name
            tags: Optional list of tags for the span
            **attributes: Span attributes

        Yields:
            The span object or None if OTEL is unavailable

        Example:
            ```python
            with otel.span("process-data", tags=["data"], size=100) as span:
                result = process()
                if span:
                    span.set_attribute("status", "success")
            ```
        """
        if not self.is_available or not logfire:
            yield None
            return

        try:
            # Build kwargs for logfire.span
            kwargs: dict[str, Any] = dict(attributes)
            if tags:
                kwargs["_tags"] = tags

            with logfire.span(name, **kwargs) as span:
                yield span
        except Exception as e:
            logger.warning(f"Error creating OTEL span '{name}': {e}")
            yield None

    def start_span(
        self,
        name: str,
        tags: list[str] | None = None,
        **attributes: Any,
    ) -> Any:
        """Start a span manually (for non-context-manager use).

        You must call __exit__ on the returned span when done.

        Args:
            name: Span name
            tags: Optional list of tags
            **attributes: Span attributes

        Returns:
            The span object or None if OTEL is unavailable

        Example:
            ```python
            span = otel.start_span("my-span", key="value")
            try:
                do_work()
            finally:
                otel.end_span(span)
            ```
        """
        if not self.is_available or not logfire:
            return None

        try:
            kwargs: dict[str, Any] = dict(attributes)
            if tags:
                kwargs["_tags"] = tags

            span = logfire.span(name, **kwargs).__enter__()
            return span
        except Exception as e:
            logger.warning(f"Error starting OTEL span '{name}': {e}")
            return None

    def end_span(
        self,
        span: Any,
        error: Exception | None = None,
    ) -> None:
        """End a manually started span.

        Args:
            span: The span to end
            error: Optional exception that occurred
        """
        if span is None:
            return

        try:
            span.__exit__(
                type(error) if error else None,
                error,
                error.__traceback__ if error else None,
            )
        except Exception as e:
            logger.warning(f"Error ending OTEL span: {e}")

    def set_span_attribute(
        self,
        span: Any,
        key: str,
        value: Any,
    ) -> None:
        """Set an attribute on a span.

        Args:
            span: The span to modify
            key: Attribute name
            value: Attribute value
        """
        if span is None:
            return

        try:
            if hasattr(span, "set_attribute"):
                span.set_attribute(key, value)
        except Exception as e:
            logger.warning(f"Error setting span attribute '{key}': {e}")

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message via Logfire.

        Args:
            message: Log message
            **kwargs: Additional attributes
        """
        if not self.is_available or not logfire:
            return

        try:
            logfire.info(message, **kwargs)
        except Exception:
            pass

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message via Logfire.

        Args:
            message: Log message
            **kwargs: Additional attributes
        """
        if not self.is_available or not logfire:
            return

        try:
            logfire.warn(message, **kwargs)
        except Exception:
            pass

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log an error message via Logfire.

        Args:
            message: Log message
            **kwargs: Additional attributes
        """
        if not self.is_available or not logfire:
            return

        try:
            logfire.error(message, **kwargs)
        except Exception:
            pass

    @classmethod
    def reset_configuration(cls) -> None:
        """Reset configuration tracking (mainly for testing)."""
        cls._configured_services.clear()


__all__ = ["OTELManager"]
