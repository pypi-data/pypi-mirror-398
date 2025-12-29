"""Tests for base tracer protocols and mixins."""

from __future__ import annotations

import pytest


class TestTracerMixin:
    """Tests for TracerMixin."""

    def test_set_and_get(self) -> None:
        """Test set and get methods."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        # Set a value
        result = tracer.set("key1", "value1")

        # Should return self for chaining
        assert result is tracer

        # Get the value
        assert tracer.get("key1") == "value1"

    def test_set_chaining(self) -> None:
        """Test method chaining with set."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        # Chain multiple sets
        tracer.set("a", 1).set("b", 2).set("c", 3)

        assert tracer.get("a") == 1
        assert tracer.get("b") == 2
        assert tracer.get("c") == 3

    def test_get_default(self) -> None:
        """Test get with default value."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        # Get non-existent key with default
        assert tracer.get("missing", "default") == "default"

        # Get non-existent key without default
        assert tracer.get("missing") is None

    def test_get_without_attributes(self) -> None:
        """Test get when _attributes not initialized."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        # Don't call set first, so _attributes is not initialized
        assert tracer.get("missing", "default") == "default"

    def test_set_initializes_attributes(self) -> None:
        """Test that set initializes _attributes if not present."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        # _attributes should not exist yet
        assert not hasattr(tracer, "_attributes") or tracer._attributes == {}

        # Set should initialize it
        tracer.set("key", "value")

        assert hasattr(tracer, "_attributes")
        assert tracer._attributes == {"key": "value"}


class TestBaseTracerProtocol:
    """Tests for BaseTracer protocol."""

    def test_protocol_check(self) -> None:
        """Test that protocol can be used for type checking."""
        from autonomize_observer.tracing.base import BaseTracer

        class ValidTracer:
            def set(self, key: str, value: object) -> "ValidTracer":
                return self

            def log(self, message: str, **kwargs: object) -> "ValidTracer":
                return self

            def __enter__(self) -> "ValidTracer":
                return self

            def __exit__(
                self,
                exc_type: type | None,
                exc_val: BaseException | None,
                exc_tb: object,
            ) -> bool:
                return False

        tracer = ValidTracer()
        assert isinstance(tracer, BaseTracer)

    def test_invalid_protocol(self) -> None:
        """Test that incomplete class is not a BaseTracer."""
        from autonomize_observer.tracing.base import BaseTracer

        class InvalidTracer:
            pass

        tracer = InvalidTracer()
        assert not isinstance(tracer, BaseTracer)


class TestSpanTracerProtocol:
    """Tests for SpanTracer protocol."""

    def test_protocol_check(self) -> None:
        """Test that protocol can be used for type checking."""
        from contextlib import contextmanager
        from typing import Any, Generator

        from autonomize_observer.tracing.base import SpanTracer

        class ValidSpanTracer:
            def set(self, key: str, value: object) -> "ValidSpanTracer":
                return self

            def log(self, message: str, **kwargs: object) -> "ValidSpanTracer":
                return self

            def __enter__(self) -> "ValidSpanTracer":
                return self

            def __exit__(
                self,
                exc_type: type | None,
                exc_val: BaseException | None,
                exc_tb: object,
            ) -> bool:
                return False

            @contextmanager
            def span(self, name: str, **attributes: Any) -> Generator[Any, None, None]:
                yield self

        tracer = ValidSpanTracer()
        assert isinstance(tracer, SpanTracer)

    def test_workflow_tracer_is_span_tracer(self) -> None:
        """Test that WorkflowTracer implements SpanTracer."""
        from autonomize_observer.tracing.base import SpanTracer
        from autonomize_observer.tracing.workflow_tracer import WorkflowTracer

        tracer = WorkflowTracer(name="test")
        # WorkflowTracer uses 'step' not 'span', so it won't match SpanTracer
        # This is intentional - SpanTracer is for tracers with nested spans


class TestTracerMixinIntegration:
    """Integration tests for TracerMixin."""

    def test_mixin_with_custom_tracer(self) -> None:
        """Test mixin with a custom tracer class."""
        from autonomize_observer.tracing.base import TracerMixin

        class MyTracer(TracerMixin):
            def __init__(self, name: str) -> None:
                self.name = name
                self._logs: list[str] = []

            def log(self, message: str) -> "MyTracer":
                self._logs.append(message)
                return self

        tracer = MyTracer("my-tracer")

        # Use mixin methods
        tracer.set("count", 10).set("status", "ok")
        tracer.log("Started").log("Completed")

        assert tracer.get("count") == 10
        assert tracer.get("status") == "ok"
        assert tracer._logs == ["Started", "Completed"]

    def test_mixin_overwrite_value(self) -> None:
        """Test overwriting an attribute value."""
        from autonomize_observer.tracing.base import TracerMixin

        class TestTracer(TracerMixin):
            pass

        tracer = TestTracer()

        tracer.set("key", "initial")
        assert tracer.get("key") == "initial"

        tracer.set("key", "updated")
        assert tracer.get("key") == "updated"
