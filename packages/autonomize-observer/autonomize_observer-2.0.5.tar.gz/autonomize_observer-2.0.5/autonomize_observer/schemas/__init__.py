"""Schema definitions for Autonomize Observer.

Provides audit event schemas and enums.
For OTEL spans, Logfire handles the schema internally.
"""

from autonomize_observer.schemas.audit import AuditEvent, ChangeRecord
from autonomize_observer.schemas.base import BaseEvent
from autonomize_observer.schemas.enums import (
    AuditAction,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    ComplianceFramework,
    EventCategory,
    ResourceType,
)

__all__ = [
    # Base
    "BaseEvent",
    # Enums
    "EventCategory",
    "AuditEventType",
    "AuditAction",
    "AuditSeverity",
    "AuditOutcome",
    "ComplianceFramework",
    "ResourceType",
    # Audit
    "AuditEvent",
    "ChangeRecord",
]
