"""Custom exceptions for Autonomize Observer."""


class ObserverError(Exception):
    """Base exception for all Autonomize Observer errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message}: {self.cause}"
        return self.message


class ConfigurationError(ObserverError):
    """Raised when there's a configuration error."""


class TracingError(ObserverError):
    """Raised when there's a tracing error."""


class AuditError(ObserverError):
    """Raised when there's an audit logging error."""


class ExporterError(ObserverError):
    """Raised when there's an exporter error."""


class InstrumentationError(ObserverError):
    """Raised when there's an instrumentation error."""


class KeycloakError(ObserverError):
    """Raised when there's a Keycloak token parsing error."""


class KafkaExporterError(ExporterError):
    """Raised when there's a Kafka-specific exporter error."""
