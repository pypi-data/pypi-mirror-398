"""Audit logger for compliance-focused event logging.

Provides immutable audit trails with:
- Actor context (who did what)
- Resource tracking (what was affected)
- Change recording (what changed)
- Compliance tagging (HIPAA, GDPR, SOC2)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from autonomize_observer.audit.context import ActorContext, get_actor_context
from autonomize_observer.schemas.audit import AuditEvent, ChangeRecord
from autonomize_observer.schemas.enums import (
    AuditAction,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    ComplianceFramework,
    ResourceType,
)

if TYPE_CHECKING:
    from autonomize_observer.exporters.kafka import KafkaExporter

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logger for audit events with compliance support.

    Creates immutable audit records that can be exported to Kafka
    for downstream processing and storage.

    Example:
        audit = AuditLogger(kafka_exporter)

        # Log a simple action
        audit.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-123",
            description="User viewed document",
        )

        # Log with changes
        audit.log_update(
            resource_type=ResourceType.USER,
            resource_id="user-456",
            changes=[
                ChangeRecord(field="email", old_value="old@ex.com", new_value="new@ex.com"),
            ],
            description="User updated email",
        )
    """

    def __init__(
        self,
        exporter: KafkaExporter | None = None,
        service_name: str = "autonomize-observer",
        default_retention_days: int = 365,
    ) -> None:
        """Initialize the audit logger.

        Args:
            exporter: Kafka exporter for sending audit events
            service_name: Name of the service for event attribution
            default_retention_days: Default retention period for events
        """
        self._exporter = exporter
        self._service_name = service_name
        self._default_retention_days = default_retention_days

    def log(
        self,
        event_type: AuditEventType,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: str,
        resource_name: str | None = None,
        description: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        changes: list[ChangeRecord] | None = None,
        compliance_frameworks: list[ComplianceFramework] | None = None,
        metadata: dict[str, Any] | None = None,
        actor: ActorContext | None = None,
        retention_days: int | None = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of audit event
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of the resource
            resource_name: Optional name of the resource
            description: Human-readable description
            severity: Event severity
            outcome: Outcome of the action
            changes: List of changes made (for updates)
            compliance_frameworks: Applicable compliance frameworks
            metadata: Additional metadata
            actor: Actor context (uses current context if not provided)
            retention_days: How long to retain the event

        Returns:
            The created AuditEvent
        """
        # Get actor from context if not provided
        if actor is None:
            actor = get_actor_context()

        # Build the event
        event = AuditEvent(
            audit_type=event_type,
            action=action,
            severity=severity,
            outcome=outcome,
            actor_id=actor.actor_id if actor else "unknown",
            actor_type=actor.actor_type if actor else "unknown",
            actor_email=actor.email if actor else None,
            actor_name=actor.name if actor else None,
            ip_address=actor.ip_address if actor else None,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            changes=changes or [],
            compliance_frameworks=compliance_frameworks or [],
            metadata=metadata or {},
            retention_days=retention_days or self._default_retention_days,
            service_name=self._service_name,
        )

        # Add actor context to metadata if present
        if actor:
            event.metadata["actor_context"] = {
                "roles": actor.roles,
                "groups": actor.groups,
                "tenant_id": actor.tenant_id,
                "organization_id": actor.organization_id,
                "session_id": actor.session_id,
            }

        # Export if exporter is configured
        if self._exporter:
            result = self._exporter.export_audit(event)
            if not result.success:
                logger.warning(
                    "Failed to export audit event",
                    extra={"event_id": event.event_id, "errors": result.errors},
                )
        else:
            logger.debug(
                "Audit event created (no exporter configured)",
                extra={"event_id": event.event_id},
            )

        return event

    def log_create(
        self,
        resource_type: ResourceType,
        resource_id: str,
        resource_name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a resource creation event.

        Convenience method for CREATE actions.
        """
        return self.log(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description or f"Created {resource_type.value} {resource_id}",
            metadata=metadata,
            **kwargs,
        )

    def log_read(
        self,
        resource_type: ResourceType,
        resource_id: str,
        resource_name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a resource read/access event.

        Convenience method for READ actions.
        """
        return self.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description or f"Accessed {resource_type.value} {resource_id}",
            metadata=metadata,
            **kwargs,
        )

    def log_update(
        self,
        resource_type: ResourceType,
        resource_id: str,
        changes: list[ChangeRecord],
        resource_name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a resource update event.

        Convenience method for UPDATE actions with changes.
        """
        return self.log(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description or f"Updated {resource_type.value} {resource_id}",
            changes=changes,
            metadata=metadata,
            **kwargs,
        )

    def log_delete(
        self,
        resource_type: ResourceType,
        resource_id: str,
        resource_name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a resource deletion event.

        Convenience method for DELETE actions.
        """
        return self.log(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description or f"Deleted {resource_type.value} {resource_id}",
            severity=AuditSeverity.MEDIUM,
            metadata=metadata,
            **kwargs,
        )

    def log_login(
        self,
        user_id: str,
        success: bool = True,
        method: str = "password",
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a login event.

        Convenience method for authentication events.
        """
        return self.log(
            event_type=AuditEventType.AUTHENTICATION,
            action=AuditAction.LOGIN,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            description=f"User login {'succeeded' if success else 'failed'}",
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            severity=AuditSeverity.INFO if success else AuditSeverity.MEDIUM,
            metadata={"method": method, **(metadata or {})},
            **kwargs,
        )

    def log_logout(
        self,
        user_id: str,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a logout event."""
        return self.log(
            event_type=AuditEventType.AUTHENTICATION,
            action=AuditAction.LOGOUT,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            description="User logged out",
            metadata=metadata,
            **kwargs,
        )

    def log_permission_change(
        self,
        resource_type: ResourceType,
        resource_id: str,
        changes: list[ChangeRecord],
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a permission change event.

        For RBAC/permission changes that are security-relevant.
        """
        return self.log(
            event_type=AuditEventType.AUTHORIZATION,
            action=AuditAction.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description or f"Permission changed on {resource_id}",
            severity=AuditSeverity.MEDIUM,
            changes=changes,
            compliance_frameworks=[ComplianceFramework.SOC2],
            metadata=metadata,
            **kwargs,
        )

    def log_llm_interaction(
        self,
        flow_id: str | None = None,
        session_id: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log an LLM interaction for audit purposes.

        Useful for tracking AI usage for compliance and cost allocation.
        """
        meta = {
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost,
            **(metadata or {}),
        }

        return self.log(
            event_type=AuditEventType.AI_INTERACTION,
            action=AuditAction.EXECUTE,
            resource_type=ResourceType.LLM_MODEL,
            resource_id=model or "unknown",
            resource_name=f"{provider}/{model}" if provider else model,
            description=description or f"LLM call to {model}",
            metadata=meta,
            **kwargs,
        )

    def log_data_export(
        self,
        resource_type: ResourceType,
        resource_id: str,
        export_format: str,
        record_count: int = 0,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log a data export event.

        Important for GDPR compliance tracking.
        """
        return self.log(
            event_type=AuditEventType.DATA_EXPORT,
            action=AuditAction.EXPORT,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description
            or f"Exported {record_count} records as {export_format}",
            severity=AuditSeverity.MEDIUM,
            compliance_frameworks=[ComplianceFramework.GDPR],
            metadata={
                "export_format": export_format,
                "record_count": record_count,
                **(metadata or {}),
            },
            **kwargs,
        )

    def flush(self, timeout: float = 5.0) -> int:
        """Flush any pending audit events.

        Args:
            timeout: Maximum time to wait

        Returns:
            Number of events still pending
        """
        if self._exporter:
            return self._exporter.flush(timeout)
        return 0
