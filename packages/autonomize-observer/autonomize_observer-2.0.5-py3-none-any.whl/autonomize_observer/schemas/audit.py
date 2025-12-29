"""Audit event schema for compliance and tracking."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

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


class ChangeRecord(BaseModel):
    """Record of a single field change."""

    field: str
    old_value: Any = None
    new_value: Any = None

    model_config = {"extra": "allow"}


class AuditEvent(BaseEvent):
    """Audit event for compliance and tracking.

    Captures who did what, to what, when, and how.
    Designed for immutable audit trail storage.
    """

    # Override base defaults
    event_category: EventCategory = EventCategory.AUDIT

    # === Audit Type ===
    audit_type: AuditEventType = AuditEventType.RESOURCE_READ
    action: AuditAction = AuditAction.READ
    severity: AuditSeverity = AuditSeverity.INFO
    outcome: AuditOutcome = AuditOutcome.SUCCESS

    # === Actor (Who) ===
    actor_id: str = ""
    actor_type: str = "user"  # user, service, system
    actor_email: str | None = None
    actor_name: str | None = None
    ip_address: str | None = None

    # === Resource (What) ===
    resource_type: ResourceType = ResourceType.RESOURCE
    resource_id: str = ""
    resource_name: str | None = None

    # === Description ===
    description: str | None = None

    # === Changes (What changed) ===
    changes: list[ChangeRecord] = Field(default_factory=list)

    # === Compliance ===
    compliance_frameworks: list[ComplianceFramework] = Field(default_factory=list)

    # === Retention ===
    retention_days: int = 365
    immutable: bool = True

    # === Service ===
    service_name: str | None = None

    model_config = {
        "use_enum_values": True,
        "extra": "allow",
    }

    def add_change(
        self,
        field: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Add a field change record."""
        self.changes.append(
            ChangeRecord(
                field=field,
                old_value=old_value,
                new_value=new_value,
            )
        )
