"""Tests for exception classes."""

import pytest

from autonomize_observer.core.exceptions import (
    AuditError,
    ConfigurationError,
    ExporterError,
    ObserverError,
)


class TestObserverError:
    """Tests for ObserverError base class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = ObserverError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.cause is None

    def test_error_with_cause(self):
        """Test error with cause."""
        cause = ValueError("Original error")
        error = ObserverError("Wrapper error", cause=cause)
        assert str(error) == "Wrapper error: Original error"
        assert error.cause is cause

    def test_inheritance(self):
        """Test that ObserverError is an Exception."""
        error = ObserverError("Test")
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_is_observer_error(self):
        """Test inheritance from ObserverError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, ObserverError)
        assert isinstance(error, Exception)

    def test_error_message(self):
        """Test error message."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"


class TestAuditError:
    """Tests for AuditError."""

    def test_is_observer_error(self):
        """Test inheritance from ObserverError."""
        error = AuditError("Audit failed")
        assert isinstance(error, ObserverError)
        assert isinstance(error, Exception)

    def test_error_with_cause(self):
        """Test error with cause."""
        cause = IOError("Disk full")
        error = AuditError("Audit failed", cause=cause)
        assert str(error) == "Audit failed: Disk full"
        assert error.cause is cause


class TestExporterError:
    """Tests for ExporterError."""

    def test_is_observer_error(self):
        """Test inheritance from ObserverError."""
        error = ExporterError("Export failed")
        assert isinstance(error, ObserverError)
        assert isinstance(error, Exception)

    def test_error_message(self):
        """Test error message."""
        error = ExporterError("Connection refused")
        assert str(error) == "Connection refused"
