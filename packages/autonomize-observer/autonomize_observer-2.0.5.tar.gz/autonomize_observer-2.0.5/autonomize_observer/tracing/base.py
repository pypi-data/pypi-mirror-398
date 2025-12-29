"""Base tracer protocols and abstractions.

This module defines the common interfaces for all tracers,
enabling consistent behavior and better testability.

Usage:
    from autonomize_observer.tracing.base import BaseTracer, SpanTracer

    def process_with_tracer(tracer: BaseTracer) -> None:
        tracer.set("key", "value")
        # ... do work ...
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass


@runtime_checkable
class BaseTracer(Protocol):
    """Protocol for all tracers.

    Defines the minimal interface that all tracers must implement.
    This allows functions to accept any tracer type and provides
    a consistent API for tracing operations.

    Example:
        ```python
        def process_with_tracer(tracer: BaseTracer) -> None:
            tracer.set("key", "value")
            tracer.log("Processing started")
        ```
    """

    def set(self, key: str, value: Any) -> BaseTracer:
        """Set an attribute on the tracer.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        ...

    def log(self, message: str, **kwargs: Any) -> BaseTracer:
        """Log a message within the tracer context.

        Args:
            message: Log message
            **kwargs: Additional attributes

        Returns:
            Self for chaining
        """
        ...

    def __enter__(self) -> BaseTracer:
        """Context manager entry."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """Context manager exit."""
        ...


@runtime_checkable
class SpanTracer(BaseTracer, Protocol):
    """Protocol for tracers that support nested spans.

    Extends BaseTracer with the ability to create nested spans
    for step-based or component-based tracing.

    Example:
        ```python
        def process_with_spans(tracer: SpanTracer) -> None:
            with tracer.span("step1") as span:
                span.set("items", 5)
                do_step1()
            with tracer.span("step2"):
                do_step2()
        ```
    """

    @contextmanager
    def span(
        self,
        name: str,
        **attributes: Any,
    ) -> Generator[Any, None, None]:
        """Create a nested span.

        Args:
            name: Span name
            **attributes: Initial attributes for the span

        Yields:
            Span context for setting attributes
        """
        ...


class TracerMixin:
    """Mixin providing common tracer functionality.

    Subclasses can inherit from this to get default implementations
    of common methods.
    """

    _attributes: dict[str, Any]

    def set(self, key: str, value: Any) -> TracerMixin:
        """Set an attribute.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Self for chaining
        """
        if not hasattr(self, "_attributes"):
            self._attributes = {}
        self._attributes[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Get an attribute value.

        Args:
            key: Attribute name
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        if not hasattr(self, "_attributes"):
            return default
        return self._attributes.get(key, default)


__all__ = [
    "BaseTracer",
    "SpanTracer",
    "TracerMixin",
]
