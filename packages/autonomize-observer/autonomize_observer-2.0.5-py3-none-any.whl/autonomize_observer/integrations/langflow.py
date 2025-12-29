"""Langflow integration for tracing flows and components.

Leverages Logfire for the actual tracing, adding Langflow-specific
context and attributes.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

# Type variables for decorators
P = ParamSpec("P")
R = TypeVar("R")

# Context variable for flow execution
_flow_context: ContextVar[FlowContext | None] = ContextVar("flow_context", default=None)


@dataclass
class FlowContext:
    """Context for a Langflow flow execution.

    Tracks flow-level metadata that gets attached to all spans
    within the flow.
    """

    flow_id: str
    flow_name: str
    session_id: str | None = None
    user_id: str | None = None
    project_name: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    component_count: int = 0

    def to_attributes(self) -> dict[str, Any]:
        """Convert to span attributes."""
        attrs = {
            "langflow.flow.id": self.flow_id,
            "langflow.flow.name": self.flow_name,
        }
        if self.session_id:
            attrs["langflow.session.id"] = self.session_id
        if self.user_id:
            attrs["langflow.user.id"] = self.user_id
        if self.project_name:
            attrs["langflow.project.name"] = self.project_name
        return attrs


def get_flow_context() -> FlowContext | None:
    """Get the current flow context."""
    return _flow_context.get()


def set_flow_context(ctx: FlowContext | None) -> None:
    """Set the current flow context."""
    _flow_context.set(ctx)


def trace_flow(
    flow_id: str,
    flow_name: str,
    session_id: str | None = None,
    user_id: str | None = None,
    project_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace a Langflow flow execution.

    Creates a root span for the flow and sets up flow context
    for child component spans.

    Args:
        flow_id: Unique identifier for the flow
        flow_name: Human-readable flow name
        session_id: Optional session identifier
        user_id: Optional user identifier
        project_name: Optional project name
        metadata: Additional flow metadata

    Example:
        @trace_flow(
            flow_id="flow-123",
            flow_name="Customer Support Bot",
            session_id="session-456",
        )
        def run_flow(input_text: str) -> str:
            # Flow execution logic
            return result
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            import logfire

            # Create flow context
            ctx = FlowContext(
                flow_id=flow_id,
                flow_name=flow_name,
                session_id=session_id,
                user_id=user_id,
                project_name=project_name,
                metadata=metadata or {},
            )

            # Set flow context for child spans
            token = _flow_context.set(ctx)

            try:
                with logfire.span(
                    f"flow:{flow_name}",
                    **ctx.to_attributes(),
                ) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("langflow.flow.status", "success")
                        span.set_attribute(
                            "langflow.flow.component_count", ctx.component_count
                        )
                        return result
                    except Exception as e:
                        span.set_attribute("langflow.flow.status", "error")
                        span.set_attribute("langflow.flow.error", str(e))
                        raise
            finally:
                _flow_context.reset(token)

        return wrapper

    return decorator


def trace_component(
    component_type: str,
    component_name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace a Langflow component execution.

    Creates a child span under the current flow.

    Args:
        component_type: Type of component (e.g., "LLMComponent", "PromptComponent")
        component_name: Optional specific component name

    Example:
        @trace_component("LLMComponent", "GPT-4 Processor")
        def process_with_llm(input_text: str) -> str:
            # Component logic
            return result
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            import logfire

            # Get flow context
            flow_ctx = get_flow_context()

            # Build component attributes
            attrs: dict[str, Any] = {
                "langflow.component.type": component_type,
            }
            if component_name:
                attrs["langflow.component.name"] = component_name

            # Add flow context if available
            if flow_ctx:
                flow_ctx.component_count += 1
                attrs["langflow.component.index"] = flow_ctx.component_count
                attrs.update(flow_ctx.to_attributes())

            span_name = component_name or component_type

            with logfire.span(f"component:{span_name}", **attrs) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("langflow.component.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("langflow.component.status", "error")
                    span.set_attribute("langflow.component.error", str(e))
                    raise

        return wrapper

    return decorator


class FlowTracer:
    """Helper class for manually tracing flow execution.

    Use this when decorators aren't practical.

    Example:
        tracer = FlowTracer()

        with tracer.flow("flow-123", "My Flow") as flow:
            with flow.component("LLMComponent", "Processor") as comp:
                result = call_llm()
                comp.set_result(result)
    """

    def flow(
        self,
        flow_id: str,
        flow_name: str,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> FlowSpan:
        """Start tracing a flow."""
        return FlowSpan(
            flow_id=flow_id,
            flow_name=flow_name,
            session_id=session_id,
            user_id=user_id,
            **kwargs,
        )


class FlowSpan:
    """Context manager for flow spans."""

    def __init__(
        self,
        flow_id: str,
        flow_name: str,
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.ctx = FlowContext(
            flow_id=flow_id,
            flow_name=flow_name,
            session_id=session_id,
            user_id=user_id,
            metadata=kwargs,
        )
        self._span: Any = None
        self._token: Any = None

    def __enter__(self) -> FlowSpan:
        import logfire

        self._token = _flow_context.set(self.ctx)
        self._span = logfire.span(
            f"flow:{self.ctx.flow_name}",
            **self.ctx.to_attributes(),
        ).__enter__()
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any
    ) -> None:
        if self._span:
            if exc_val:
                self._span.set_attribute("langflow.flow.status", "error")
                self._span.set_attribute("langflow.flow.error", str(exc_val))
            else:
                self._span.set_attribute("langflow.flow.status", "success")
            self._span.set_attribute(
                "langflow.flow.component_count", self.ctx.component_count
            )
            self._span.__exit__(exc_type, exc_val, exc_tb)

        if self._token:
            _flow_context.reset(self._token)

    def component(
        self,
        component_type: str,
        component_name: str | None = None,
    ) -> ComponentSpan:
        """Start a component span within this flow."""
        return ComponentSpan(
            component_type=component_type,
            component_name=component_name,
            flow_ctx=self.ctx,
        )


class ComponentSpan:
    """Context manager for component spans."""

    def __init__(
        self,
        component_type: str,
        component_name: str | None = None,
        flow_ctx: FlowContext | None = None,
    ) -> None:
        self.component_type = component_type
        self.component_name = component_name
        self.flow_ctx = flow_ctx or get_flow_context()
        self._span: Any = None
        self._result: Any = None

    def __enter__(self) -> ComponentSpan:
        import logfire

        attrs: dict[str, Any] = {
            "langflow.component.type": self.component_type,
        }
        if self.component_name:
            attrs["langflow.component.name"] = self.component_name

        if self.flow_ctx:
            self.flow_ctx.component_count += 1
            attrs["langflow.component.index"] = self.flow_ctx.component_count
            attrs.update(self.flow_ctx.to_attributes())

        span_name = self.component_name or self.component_type
        self._span = logfire.span(f"component:{span_name}", **attrs).__enter__()
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any
    ) -> None:
        if self._span:
            if exc_val:
                self._span.set_attribute("langflow.component.status", "error")
                self._span.set_attribute("langflow.component.error", str(exc_val))
            else:
                self._span.set_attribute("langflow.component.status", "success")
            self._span.__exit__(exc_type, exc_val, exc_tb)

    def set_result(self, result: Any) -> None:
        """Set the component result."""
        self._result = result
        if self._span:
            # Truncate large results
            result_str = str(result)[:1000]
            self._span.set_attribute("langflow.component.result", result_str)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a custom attribute on the span."""
        if self._span:
            self._span.set_attribute(key, value)
