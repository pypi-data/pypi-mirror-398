"""Tests for OTEL utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestOTELManager:
    """Tests for OTELManager class."""

    def test_init_without_logfire(self) -> None:
        """Test initialization when logfire is not available."""
        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test-service")
            assert manager.service_name == "test-service"
            assert not manager.is_available
            assert not manager._configured

    def test_init_with_logfire(self) -> None:
        """Test initialization when logfire is available."""
        mock_logfire = MagicMock()

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                # Reset configured services for test isolation
                OTELManager._configured_services.clear()

                manager = OTELManager(
                    service_name="test-service",
                    send_to_logfire=False,
                )
                assert manager.service_name == "test-service"
                assert manager.is_available
                mock_logfire.configure.assert_called_once_with(
                    service_name="test-service",
                    send_to_logfire=False,
                )

    def test_span_when_unavailable(self) -> None:
        """Test span creation when OTEL is unavailable."""
        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")

            with manager.span("test-span") as span:
                assert span is None

    def test_span_when_available(self) -> None:
        """Test span creation when OTEL is available."""
        mock_logfire = MagicMock()
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_logfire.span.return_value.__exit__ = MagicMock(return_value=False)

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                with manager.span("test-span", key="value") as span:
                    assert span is mock_span

    def test_start_end_span(self) -> None:
        """Test manual span start/end."""
        mock_logfire = MagicMock()
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                span = manager.start_span("manual-span", tags=["test"])
                assert span is mock_span

                manager.end_span(span)
                mock_span.__exit__.assert_called_once()

    def test_end_span_with_error(self) -> None:
        """Test ending span with error."""
        mock_logfire = MagicMock()
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                span = manager.start_span("error-span")
                error = ValueError("test error")
                manager.end_span(span, error=error)

                # Check error was passed to __exit__
                mock_span.__exit__.assert_called_once()
                call_args = mock_span.__exit__.call_args[0]
                assert call_args[0] is ValueError
                assert call_args[1] is error

    def test_end_span_none(self) -> None:
        """Test ending None span does nothing."""
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.clear()
        manager = OTELManager(service_name="test")
        manager.end_span(None)  # Should not raise

    def test_set_span_attribute(self) -> None:
        """Test setting span attribute."""
        mock_span = MagicMock()

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")
            manager.set_span_attribute(mock_span, "key", "value")
            mock_span.set_attribute.assert_called_once_with("key", "value")

    def test_set_span_attribute_none_span(self) -> None:
        """Test setting attribute on None span does nothing."""
        from autonomize_observer.tracing.otel_utils import OTELManager

        manager = OTELManager(service_name="test")
        manager.set_span_attribute(None, "key", "value")  # Should not raise

    def test_reset_configuration(self) -> None:
        """Test resetting configuration tracking."""
        from autonomize_observer.tracing.otel_utils import OTELManager

        OTELManager._configured_services.add("test-service")
        assert "test-service" in OTELManager._configured_services

        OTELManager.reset_configuration()
        assert len(OTELManager._configured_services) == 0

    def test_log_methods_when_unavailable(self) -> None:
        """Test log methods when OTEL is unavailable."""
        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")

            # These should not raise
            manager.log_info("info message")
            manager.log_warning("warning message")
            manager.log_error("error message")

    def test_log_methods_when_available(self) -> None:
        """Test log methods when OTEL is available."""
        mock_logfire = MagicMock()

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                manager.log_info("info message", key="value")
                mock_logfire.info.assert_called_once_with("info message", key="value")

                manager.log_warning("warning message")
                mock_logfire.warn.assert_called_once_with("warning message")

                manager.log_error("error message")
                mock_logfire.error.assert_called_once_with("error message")

    def test_start_span_when_unavailable(self) -> None:
        """Test start_span returns None when OTEL is unavailable."""
        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")
            span = manager.start_span("test-span")
            assert span is None

    def test_configure_exception(self) -> None:
        """Test configuration handles exceptions gracefully."""
        mock_logfire = MagicMock()
        mock_logfire.configure.side_effect = Exception("Config failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should handle exception gracefully
                assert manager._configured is False

    def test_span_exception_handling(self) -> None:
        """Test span context manager handles exceptions."""
        mock_logfire = MagicMock()
        mock_logfire.span.side_effect = Exception("Span creation failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should not raise, returns None
                with manager.span("test-span") as span:
                    assert span is None

    def test_duplicate_service_configuration(self) -> None:
        """Test that same service is not configured twice."""
        mock_logfire = MagicMock()

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()

                # First manager should configure
                manager1 = OTELManager(service_name="same-service")
                assert mock_logfire.configure.call_count == 1

                # Second manager should not configure again
                manager2 = OTELManager(service_name="same-service")
                assert mock_logfire.configure.call_count == 1

                # Both should be available
                assert manager1.is_available
                assert manager2.is_available

    def test_span_with_tags(self) -> None:
        """Test span creation with tags."""
        mock_logfire = MagicMock()
        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_logfire.span.return_value.__exit__ = MagicMock(return_value=False)

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                with manager.span("test-span", tags=["tag1", "tag2"], custom="attr"):
                    pass

                mock_logfire.span.assert_called()
                call_kwargs = mock_logfire.span.call_args.kwargs
                assert call_kwargs.get("_tags") == ["tag1", "tag2"]
                assert call_kwargs.get("custom") == "attr"

    def test_start_span_exception(self) -> None:
        """Test start_span handles exceptions."""
        mock_logfire = MagicMock()
        mock_logfire.span.side_effect = Exception("Span failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should not raise, returns None
                span = manager.start_span("test-span")
                assert span is None

    def test_end_span_exception(self) -> None:
        """Test end_span handles exceptions."""
        mock_span = MagicMock()
        mock_span.__exit__.side_effect = Exception("Exit failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")

            # Should not raise
            manager.end_span(mock_span)

    def test_set_span_attribute_exception(self) -> None:
        """Test set_span_attribute handles exceptions gracefully."""
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = Exception("Set attribute failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", False):
            from autonomize_observer.tracing.otel_utils import OTELManager

            manager = OTELManager(service_name="test")

            # Should not raise
            manager.set_span_attribute(mock_span, "key", "value")

    def test_log_info_exception(self) -> None:
        """Test log_info handles exceptions gracefully."""
        mock_logfire = MagicMock()
        mock_logfire.info.side_effect = Exception("Log failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should not raise
                manager.log_info("test message")

    def test_log_warning_exception(self) -> None:
        """Test log_warning handles exceptions gracefully."""
        mock_logfire = MagicMock()
        mock_logfire.warn.side_effect = Exception("Log failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should not raise
                manager.log_warning("test warning")

    def test_log_error_exception(self) -> None:
        """Test log_error handles exceptions gracefully."""
        mock_logfire = MagicMock()
        mock_logfire.error.side_effect = Exception("Log failed")

        with patch("autonomize_observer.tracing.otel_utils.LOGFIRE_AVAILABLE", True):
            with patch("autonomize_observer.tracing.otel_utils.logfire", mock_logfire):
                from autonomize_observer.tracing.otel_utils import OTELManager

                OTELManager._configured_services.clear()
                manager = OTELManager(service_name="test")

                # Should not raise
                manager.log_error("test error")
