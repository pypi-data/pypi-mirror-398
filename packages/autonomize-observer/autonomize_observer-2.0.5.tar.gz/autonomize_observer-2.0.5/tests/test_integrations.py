"""Tests for integration modules (Langflow and FastAPI)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autonomize_observer.integrations.fastapi import (
    _get_client_ip,
    create_fastapi_middleware,
    get_request_actor,
    setup_fastapi,
)
from autonomize_observer.integrations.langflow import (
    ComponentSpan,
    FlowContext,
    FlowSpan,
    FlowTracer,
    get_flow_context,
    set_flow_context,
    trace_component,
    trace_flow,
)


class TestFlowContext:
    """Tests for FlowContext."""

    def test_basic_creation(self):
        """Test basic flow context creation."""
        ctx = FlowContext(
            flow_id="flow-123",
            flow_name="Test Flow",
        )
        assert ctx.flow_id == "flow-123"
        assert ctx.flow_name == "Test Flow"
        assert ctx.session_id is None
        assert ctx.user_id is None
        assert ctx.component_count == 0
        assert isinstance(ctx.started_at, datetime)

    def test_full_creation(self):
        """Test flow context with all fields."""
        now = datetime.now(timezone.utc)
        ctx = FlowContext(
            flow_id="flow-123",
            flow_name="Test Flow",
            session_id="session-456",
            user_id="user-789",
            project_name="my-project",
            started_at=now,
            metadata={"key": "value"},
        )
        assert ctx.session_id == "session-456"
        assert ctx.user_id == "user-789"
        assert ctx.project_name == "my-project"
        assert ctx.started_at == now
        assert ctx.metadata["key"] == "value"

    def test_to_attributes(self):
        """Test converting to span attributes."""
        ctx = FlowContext(
            flow_id="flow-123",
            flow_name="Test Flow",
            session_id="session-456",
            user_id="user-789",
            project_name="my-project",
        )
        attrs = ctx.to_attributes()

        assert attrs["langflow.flow.id"] == "flow-123"
        assert attrs["langflow.flow.name"] == "Test Flow"
        assert attrs["langflow.session.id"] == "session-456"
        assert attrs["langflow.user.id"] == "user-789"
        assert attrs["langflow.project.name"] == "my-project"

    def test_to_attributes_minimal(self):
        """Test attributes with minimal context."""
        ctx = FlowContext(flow_id="flow-1", flow_name="Flow")
        attrs = ctx.to_attributes()

        assert "langflow.flow.id" in attrs
        assert "langflow.flow.name" in attrs
        assert "langflow.session.id" not in attrs
        assert "langflow.user.id" not in attrs


class TestFlowContextGlobal:
    """Tests for global flow context management."""

    def setup_method(self):
        """Reset context before each test."""
        set_flow_context(None)

    def test_get_set_context(self):
        """Test getting and setting flow context."""
        assert get_flow_context() is None

        ctx = FlowContext(flow_id="flow-1", flow_name="Test")
        set_flow_context(ctx)

        result = get_flow_context()
        assert result is not None
        assert result.flow_id == "flow-1"

    def test_clear_context(self):
        """Test clearing flow context."""
        ctx = FlowContext(flow_id="flow-1", flow_name="Test")
        set_flow_context(ctx)
        assert get_flow_context() is not None

        set_flow_context(None)
        assert get_flow_context() is None


class TestTraceFlowDecorator:
    """Tests for trace_flow decorator."""

    def setup_method(self):
        """Reset context before each test."""
        set_flow_context(None)

    def test_trace_flow_basic(self):
        """Test basic flow tracing."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_flow(flow_id="flow-1", flow_name="Test Flow")
            def my_flow():
                return "result"

            result = my_flow()

            assert result == "result"
            mock_span.set_attribute.assert_any_call("langflow.flow.status", "success")

    def test_trace_flow_with_metadata(self):
        """Test flow tracing with all metadata."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_flow(
                flow_id="flow-1",
                flow_name="Test Flow",
                session_id="session-1",
                user_id="user-1",
                project_name="project-1",
                metadata={"key": "value"},
            )
            def my_flow():
                # Check context is set during execution
                ctx = get_flow_context()
                assert ctx is not None
                assert ctx.flow_id == "flow-1"
                return "result"

            my_flow()

    def test_trace_flow_exception(self):
        """Test flow tracing with exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_flow(flow_id="flow-1", flow_name="Test Flow")
            def failing_flow():
                raise ValueError("Flow error")

            with pytest.raises(ValueError):
                failing_flow()

            mock_span.set_attribute.assert_any_call("langflow.flow.status", "error")

    def test_trace_flow_context_cleanup(self):
        """Test that context is cleaned up after flow."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_flow(flow_id="flow-1", flow_name="Test Flow")
            def my_flow():
                return "result"

            my_flow()

            # Context should be None after flow completes
            assert get_flow_context() is None


class TestTraceComponentDecorator:
    """Tests for trace_component decorator."""

    def setup_method(self):
        """Reset context before each test."""
        set_flow_context(None)

    def test_trace_component_basic(self):
        """Test basic component tracing."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_component("LLMComponent")
            def my_component():
                return "result"

            result = my_component()

            assert result == "result"
            mock_span.set_attribute.assert_any_call(
                "langflow.component.status", "success"
            )

    def test_trace_component_with_name(self):
        """Test component tracing with custom name."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span) as mock_span_fn:

            @trace_component("LLMComponent", "GPT-4 Processor")
            def my_component():
                return "result"

            my_component()

            # Verify span name uses component_name
            mock_span_fn.assert_called_once()
            call_args = mock_span_fn.call_args
            assert "GPT-4 Processor" in call_args[0][0]

    def test_trace_component_with_flow_context(self):
        """Test component tracing within flow context."""
        ctx = FlowContext(flow_id="flow-1", flow_name="Test Flow")
        set_flow_context(ctx)

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_component("LLMComponent")
            def my_component():
                return "result"

            my_component()

            # Component count should be incremented
            assert ctx.component_count == 1

    def test_trace_component_exception(self):
        """Test component tracing with exception."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):

            @trace_component("LLMComponent")
            def failing_component():
                raise ValueError("Component error")

            with pytest.raises(ValueError):
                failing_component()

            mock_span.set_attribute.assert_any_call(
                "langflow.component.status", "error"
            )


class TestFlowSpan:
    """Tests for FlowSpan context manager."""

    def setup_method(self):
        """Reset context before each test."""
        set_flow_context(None)

    def test_flow_span_basic(self):
        """Test basic FlowSpan usage."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            span = FlowSpan(flow_id="flow-1", flow_name="Test Flow")

            with span:
                ctx = get_flow_context()
                assert ctx is not None
                assert ctx.flow_id == "flow-1"

    def test_flow_span_exit_success(self):
        """Test FlowSpan exit on success."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            with FlowSpan(flow_id="flow-1", flow_name="Test Flow"):
                pass

            mock_span.set_attribute.assert_any_call("langflow.flow.status", "success")

    def test_flow_span_exit_error(self):
        """Test FlowSpan exit on error."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            with pytest.raises(ValueError):
                with FlowSpan(flow_id="flow-1", flow_name="Test Flow"):
                    raise ValueError("Test error")

            mock_span.set_attribute.assert_any_call("langflow.flow.status", "error")

    def test_flow_span_component_method(self):
        """Test FlowSpan.component() method creates ComponentSpan."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            flow_span = FlowSpan(flow_id="flow-1", flow_name="Test Flow")

            with flow_span:
                # Use the component method
                comp_span = flow_span.component("LLMComponent", "Processor")
                assert isinstance(comp_span, ComponentSpan)

                # Use the component span
                with comp_span:
                    pass


class TestComponentSpan:
    """Tests for ComponentSpan context manager."""

    def test_component_span_basic(self):
        """Test basic ComponentSpan usage."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            comp = ComponentSpan("LLMComponent", "Processor")

            with comp:
                pass

            mock_span.set_attribute.assert_any_call(
                "langflow.component.status", "success"
            )

    def test_component_span_set_result(self):
        """Test setting component result."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            with ComponentSpan("LLMComponent") as comp:
                comp.set_result("my result")

            mock_span.set_attribute.assert_any_call(
                "langflow.component.result", "my result"
            )

    def test_component_span_set_attribute(self):
        """Test setting custom attribute."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            with ComponentSpan("LLMComponent") as comp:
                comp.set_attribute("custom.key", "custom_value")

            mock_span.set_attribute.assert_any_call("custom.key", "custom_value")

    def test_component_span_with_flow_context(self):
        """Test ComponentSpan with flow context."""
        ctx = FlowContext(flow_id="flow-1", flow_name="Test")
        set_flow_context(ctx)

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            with ComponentSpan("LLMComponent"):
                pass

            assert ctx.component_count == 1

    def test_component_span_with_exception(self):
        """Test ComponentSpan when exception is raised."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)

        with patch("logfire.span", return_value=mock_span):
            try:
                with ComponentSpan("LLMComponent", "Processor") as comp:
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Should set error status
            mock_span.set_attribute.assert_any_call(
                "langflow.component.status", "error"
            )
            mock_span.set_attribute.assert_any_call(
                "langflow.component.error", "Test error"
            )


class TestFlowTracer:
    """Tests for FlowTracer helper class."""

    def test_flow_tracer_flow(self):
        """Test FlowTracer.flow method."""
        tracer = FlowTracer()
        span = tracer.flow("flow-1", "Test Flow", session_id="session-1")

        assert isinstance(span, FlowSpan)
        assert span.ctx.flow_id == "flow-1"
        assert span.ctx.flow_name == "Test Flow"
        assert span.ctx.session_id == "session-1"


# FastAPI Integration Tests


class TestSetupFastAPI:
    """Tests for setup_fastapi function."""

    def test_setup_with_logfire(self):
        """Test setup with Logfire instrumentation."""
        mock_app = MagicMock()
        mock_middleware = MagicMock()

        with patch("logfire.configure") as mock_configure:
            with patch("logfire.instrument_fastapi") as mock_instrument:
                setup_fastapi(
                    mock_app,
                    service_name="test-service",
                    keycloak_enabled=False,
                    instrument_with_logfire=True,
                )

                mock_configure.assert_called_once()
                mock_instrument.assert_called_once_with(mock_app)

    def test_setup_without_logfire(self):
        """Test setup without Logfire instrumentation."""
        mock_app = MagicMock()

        setup_fastapi(
            mock_app,
            keycloak_enabled=False,
            instrument_with_logfire=False,
        )

        # App.middleware should not be called for keycloak
        # and logfire should not be imported

    def test_setup_with_keycloak(self):
        """Test setup with Keycloak middleware."""
        mock_app = MagicMock()

        with patch("logfire.configure"):
            with patch("logfire.instrument_fastapi"):
                setup_fastapi(
                    mock_app,
                    keycloak_enabled=True,
                    instrument_with_logfire=True,
                )

                mock_app.middleware.assert_called_once_with("http")

    def test_setup_logfire_failure(self):
        """Test handling Logfire instrumentation failure."""
        mock_app = MagicMock()

        with patch("logfire.configure", side_effect=Exception("Logfire error")):
            # Should not raise
            setup_fastapi(
                mock_app,
                keycloak_enabled=False,
                instrument_with_logfire=True,
            )


class TestFastAPIMiddleware:
    """Tests for FastAPI middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_middleware_no_token(self, mock_request):
        """Test middleware without auth token."""
        middleware = create_fastapi_middleware()
        call_next = AsyncMock(return_value=MagicMock())

        await middleware(mock_request, call_next)

        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_middleware_with_valid_token(self, mock_request):
        """Test middleware with valid JWT token."""
        import jwt

        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User",
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        mock_request.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Test Agent",
        }

        middleware = create_fastapi_middleware()
        call_next = AsyncMock(return_value=MagicMock())

        with patch("logfire.info"):
            await middleware(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_invalid_token(self, mock_request):
        """Test middleware with invalid token."""
        mock_request.headers = {"Authorization": "Bearer invalid_token"}

        middleware = create_fastapi_middleware()
        call_next = AsyncMock(return_value=MagicMock())

        # Should not raise, just continue without actor
        await middleware(mock_request, call_next)
        call_next.assert_called_once()


class TestGetClientIP:
    """Tests for _get_client_ip function."""

    def test_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For."""
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}

        ip = _get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_x_real_ip(self):
        """Test extracting IP from X-Real-IP."""
        request = MagicMock()
        request.headers = {"X-Real-IP": "192.168.1.2"}

        ip = _get_client_ip(request)
        assert ip == "192.168.1.2"

    def test_client_host(self):
        """Test extracting IP from client.host."""
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.3"

        ip = _get_client_ip(request)
        assert ip == "192.168.1.3"

    def test_no_client(self):
        """Test when no client info available."""
        request = MagicMock()
        request.headers = {}
        request.client = None

        ip = _get_client_ip(request)
        assert ip is None


class TestGetRequestActor:
    """Tests for get_request_actor function."""

    def test_get_actor_from_context(self):
        """Test getting actor from context."""
        from autonomize_observer.audit.context import (
            ActorContext,
            clear_actor_providers,
            set_actor_context,
        )

        clear_actor_providers()
        actor = ActorContext(actor_id="user-123")
        set_actor_context(actor)

        request = MagicMock()
        result = get_request_actor(request)

        assert result is not None
        assert result.actor_id == "user-123"

        set_actor_context(None)

    def test_get_actor_none(self):
        """Test getting actor when not set."""
        from autonomize_observer.audit.context import (
            clear_actor_providers,
            set_actor_context,
        )

        clear_actor_providers()
        set_actor_context(None)

        request = MagicMock()
        result = get_request_actor(request)

        assert result is None
