"""Tests for tracing logfire integration module."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.tracing.logfire_integration import (
    _logfire_instance,
    configure_logfire,
    get_logfire,
    instrument_database,
    instrument_llms,
    instrument_web_framework,
)


class TestConfigureLogfire:
    """Tests for configure_logfire function."""

    def test_basic_configure(self):
        """Test basic logfire configuration."""
        with patch("logfire.configure") as mock_configure:
            import logfire

            with patch.dict(
                "autonomize_observer.tracing.logfire_integration.__dict__",
                {"_logfire_instance": None},
            ):
                result = configure_logfire(service_name="test-service")

                mock_configure.assert_called_once()
                call_kwargs = mock_configure.call_args[1]
                assert call_kwargs["service_name"] == "test-service"
                assert call_kwargs["send_to_logfire"] is False

    def test_configure_with_all_options(self):
        """Test configuration with all options."""
        with patch("logfire.configure") as mock_configure:
            configure_logfire(
                service_name="my-service",
                service_version="2.0.0",
                environment="staging",
                send_to_logfire=True,
                console=False,
                additional_span_processors=[MagicMock()],
            )

            call_kwargs = mock_configure.call_args[1]
            assert call_kwargs["service_name"] == "my-service"
            assert call_kwargs["service_version"] == "2.0.0"
            assert call_kwargs["environment"] == "staging"
            assert call_kwargs["send_to_logfire"] is True
            assert call_kwargs["console"] is False
            assert "additional_span_processors" in call_kwargs

    def test_configure_with_kwargs(self):
        """Test configuration with extra kwargs."""
        with patch("logfire.configure") as mock_configure:
            configure_logfire(
                service_name="test",
                custom_option="custom_value",
            )

            call_kwargs = mock_configure.call_args[1]
            assert call_kwargs["custom_option"] == "custom_value"


class TestGetLogfire:
    """Tests for get_logfire function."""

    def test_get_logfire_not_configured(self):
        """Test getting logfire when not configured."""
        import autonomize_observer.tracing.logfire_integration as module

        original = module._logfire_instance
        module._logfire_instance = None

        try:
            with pytest.raises(RuntimeError) as exc_info:
                get_logfire()
            assert "not configured" in str(exc_info.value).lower()
        finally:
            module._logfire_instance = original

    def test_get_logfire_configured(self):
        """Test getting logfire after configuration."""
        import autonomize_observer.tracing.logfire_integration as module

        mock_logfire = MagicMock()
        original = module._logfire_instance
        module._logfire_instance = mock_logfire

        try:
            result = get_logfire()
            assert result is mock_logfire
        finally:
            module._logfire_instance = original


class TestInstrumentLLMs:
    """Tests for instrument_llms function."""

    def test_instrument_openai(self):
        """Test instrumenting OpenAI."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_llms(openai=True, anthropic=False)

            mock_lf.instrument_openai.assert_called_once()
            mock_lf.instrument_anthropic.assert_not_called()

    def test_instrument_anthropic(self):
        """Test instrumenting Anthropic."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_llms(openai=False, anthropic=True)

            mock_lf.instrument_openai.assert_not_called()
            mock_lf.instrument_anthropic.assert_called_once()

    def test_instrument_both(self):
        """Test instrumenting both providers."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_llms(openai=True, anthropic=True)

            mock_lf.instrument_openai.assert_called_once()
            mock_lf.instrument_anthropic.assert_called_once()

    def test_instrument_with_options(self):
        """Test instrumenting with provider options."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_llms(
                openai=True,
                anthropic=False,
                openai_options={"capture_messages": True},
            )

            mock_lf.instrument_openai.assert_called_once_with(capture_messages=True)

    def test_instrument_openai_failure(self):
        """Test handling OpenAI instrumentation failure."""
        mock_lf = MagicMock()
        mock_lf.instrument_openai.side_effect = Exception("OpenAI not installed")

        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            # Should not raise
            instrument_llms(openai=True, anthropic=False)

    def test_instrument_anthropic_failure(self):
        """Test handling Anthropic instrumentation failure."""
        mock_lf = MagicMock()
        mock_lf.instrument_anthropic.side_effect = Exception("Anthropic not installed")

        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            # Should not raise
            instrument_llms(openai=False, anthropic=True)


class TestInstrumentWebFramework:
    """Tests for instrument_web_framework function."""

    def test_instrument_fastapi(self):
        """Test instrumenting FastAPI."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_web_framework("fastapi")
            mock_lf.instrument_fastapi.assert_called_once()

    def test_instrument_flask(self):
        """Test instrumenting Flask."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_web_framework("flask")
            mock_lf.instrument_flask.assert_called_once()

    def test_instrument_django(self):
        """Test instrumenting Django."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_web_framework("django")
            mock_lf.instrument_django.assert_called_once()

    def test_instrument_starlette(self):
        """Test instrumenting Starlette."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_web_framework("starlette")
            mock_lf.instrument_starlette.assert_called_once()

    def test_instrument_unknown_framework(self):
        """Test instrumenting unknown framework."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            with pytest.raises(ValueError) as exc_info:
                instrument_web_framework("unknown")
            assert "unknown framework" in str(exc_info.value).lower()

    def test_instrument_framework_with_kwargs(self):
        """Test instrumenting framework with options."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            mock_app = MagicMock()
            instrument_web_framework("fastapi", app=mock_app)
            mock_lf.instrument_fastapi.assert_called_once_with(app=mock_app)

    def test_instrument_framework_failure(self):
        """Test handling framework instrumentation failure."""
        mock_lf = MagicMock()
        mock_lf.instrument_fastapi.side_effect = Exception("FastAPI not installed")

        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            # Should not raise
            instrument_web_framework("fastapi")


class TestInstrumentDatabase:
    """Tests for instrument_database function."""

    def test_instrument_sqlalchemy(self):
        """Test instrumenting SQLAlchemy."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("sqlalchemy")
            mock_lf.instrument_sqlalchemy.assert_called_once()

    def test_instrument_psycopg(self):
        """Test instrumenting psycopg."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("psycopg")
            mock_lf.instrument_psycopg.assert_called_once()

    def test_instrument_asyncpg(self):
        """Test instrumenting asyncpg."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("asyncpg")
            mock_lf.instrument_asyncpg.assert_called_once()

    def test_instrument_pymongo(self):
        """Test instrumenting pymongo."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("pymongo")
            mock_lf.instrument_pymongo.assert_called_once()

    def test_instrument_redis(self):
        """Test instrumenting redis."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("redis")
            mock_lf.instrument_redis.assert_called_once()

    def test_instrument_unknown_database(self):
        """Test instrumenting unknown database."""
        mock_lf = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            with pytest.raises(ValueError) as exc_info:
                instrument_database("unknown")
            assert "unknown database" in str(exc_info.value).lower()

    def test_instrument_database_with_kwargs(self):
        """Test instrumenting database with options."""
        mock_lf = MagicMock()
        mock_engine = MagicMock()
        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            instrument_database("sqlalchemy", engine=mock_engine)
            mock_lf.instrument_sqlalchemy.assert_called_once_with(engine=mock_engine)

    def test_instrument_database_failure(self):
        """Test handling database instrumentation failure."""
        mock_lf = MagicMock()
        mock_lf.instrument_sqlalchemy.side_effect = Exception(
            "SQLAlchemy not installed"
        )

        with patch(
            "autonomize_observer.tracing.logfire_integration.get_logfire",
            return_value=mock_lf,
        ):
            # Should not raise
            instrument_database("sqlalchemy")
