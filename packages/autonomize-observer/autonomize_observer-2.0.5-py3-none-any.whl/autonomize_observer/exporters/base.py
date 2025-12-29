"""Base exporter interface for audit events.

For OTEL trace/span export, use Logfire's built-in exporters.
These exporters focus on audit events and custom events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autonomize_observer.schemas.audit import AuditEvent


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    message: str = ""
    events_exported: int = 0
    events_failed: int = 0
    errors: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls, events_exported: int = 1, message: str = "") -> ExportResult:
        """Create a successful result."""
        return cls(
            success=True,
            message=message,
            events_exported=events_exported,
        )

    @classmethod
    def error(cls, message: str, events_failed: int = 1) -> ExportResult:
        """Create a failed result."""
        return cls(
            success=False,
            message=message,
            events_failed=events_failed,
            errors=[message],
        )

    def merge(self, other: ExportResult) -> ExportResult:
        """Merge two results together."""
        return ExportResult(
            success=self.success and other.success,
            message=f"{self.message}; {other.message}".strip("; "),
            events_exported=self.events_exported + other.events_exported,
            events_failed=self.events_failed + other.events_failed,
            errors=self.errors + other.errors,
        )


class BaseExporter(ABC):
    """Base class for audit event exporters.

    For OTEL span export, configure Logfire with an OTLP exporter.
    These exporters are for audit events and custom Kafka events.
    """

    def __init__(self, name: str = "base") -> None:
        """Initialize the exporter.

        Args:
            name: Name of the exporter for logging
        """
        self._name = name
        self._initialized = False

    @property
    def name(self) -> str:
        """Get the exporter name."""
        return self._name

    @property
    def is_initialized(self) -> bool:
        """Check if exporter is initialized."""
        return self._initialized

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the exporter.

        Called once during setup. Should establish connections,
        validate configuration, etc.
        """
        ...

    @abstractmethod
    def export_audit(self, audit_event: AuditEvent) -> ExportResult:
        """Export an audit event.

        Args:
            audit_event: The audit event to export

        Returns:
            ExportResult indicating success or failure
        """
        ...

    @abstractmethod
    def flush(self, timeout: float = 5.0) -> int:
        """Flush pending exports.

        Args:
            timeout: Maximum time to wait for flush

        Returns:
            Number of events still pending after flush
        """
        ...

    def shutdown(self) -> None:
        """Shutdown the exporter.

        Should flush pending events and close connections.
        """
        self._initialized = False
