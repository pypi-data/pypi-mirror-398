"""Tests for audit logger module."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.audit.context import (
    ActorContext,
    clear_actor_providers,
    set_actor_context,
)
from autonomize_observer.audit.logger import AuditLogger
from autonomize_observer.exporters.base import ExportResult
from autonomize_observer.schemas.audit import ChangeRecord
from autonomize_observer.schemas.enums import (
    AuditAction,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    ComplianceFramework,
    ResourceType,
)


class TestAuditLogger:
    """Tests for AuditLogger."""

    def setup_method(self):
        """Reset context before each test."""
        set_actor_context(None)
        clear_actor_providers()

    def test_create_without_exporter(self):
        """Test creating logger without exporter."""
        logger = AuditLogger()
        assert logger._exporter is None
        assert logger._service_name == "autonomize-observer"

    def test_create_with_exporter(self):
        """Test creating logger with exporter."""
        mock_exporter = MagicMock()
        logger = AuditLogger(
            exporter=mock_exporter,
            service_name="test-service",
            default_retention_days=90,
        )
        assert logger._exporter is mock_exporter
        assert logger._service_name == "test-service"
        assert logger._default_retention_days == 90

    def test_log_basic(self):
        """Test basic log call."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        actor = ActorContext(actor_id="user-123", email="test@example.com")
        set_actor_context(actor)

        event = logger.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-123",
            description="User read document",
        )

        assert event.audit_type == AuditEventType.DATA_ACCESS
        assert event.action == AuditAction.READ
        assert event.resource_type == ResourceType.DOCUMENT
        assert event.resource_id == "doc-123"
        assert event.actor_id == "user-123"
        assert event.actor_email == "test@example.com"

        mock_exporter.export_audit.assert_called_once_with(event)

    def test_log_with_explicit_actor(self):
        """Test log with explicit actor context."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        actor = ActorContext(actor_id="explicit-user", name="Explicit User")

        event = logger.log(
            event_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.UPDATE,
            resource_type=ResourceType.USER,
            resource_id="user-456",
            actor=actor,
        )

        assert event.actor_id == "explicit-user"
        assert event.actor_name == "Explicit User"

    def test_log_without_exporter(self):
        """Test log without exporter configured."""
        logger = AuditLogger()

        event = logger.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-123",
        )

        # Should not raise, just return the event
        assert event is not None
        assert event.resource_id == "doc-123"

    def test_log_create(self):
        """Test log_create convenience method."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_create(
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-new",
            resource_name="New Document",
        )

        assert event.action == AuditAction.CREATE
        assert event.audit_type == AuditEventType.DATA_MODIFICATION
        assert event.resource_id == "doc-new"
        assert event.resource_name == "New Document"

    def test_log_read(self):
        """Test log_read convenience method."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_read(
            resource_type=ResourceType.FILE,
            resource_id="file-123",
        )

        assert event.action == AuditAction.READ
        assert event.audit_type == AuditEventType.DATA_ACCESS

    def test_log_update_with_changes(self):
        """Test log_update with change records."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        changes = [
            ChangeRecord(field="name", old_value="Old Name", new_value="New Name"),
            ChangeRecord(field="email", old_value="old@ex.com", new_value="new@ex.com"),
        ]

        event = logger.log_update(
            resource_type=ResourceType.USER,
            resource_id="user-123",
            changes=changes,
        )

        assert event.action == AuditAction.UPDATE
        assert len(event.changes) == 2
        assert event.changes[0].field == "name"

    def test_log_delete(self):
        """Test log_delete convenience method."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_delete(
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-to-delete",
        )

        assert event.action == AuditAction.DELETE
        assert event.severity == AuditSeverity.MEDIUM

    def test_log_login_success(self):
        """Test log_login with success."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_login(user_id="user-123", success=True)

        assert event.action == AuditAction.LOGIN
        assert event.audit_type == AuditEventType.AUTHENTICATION
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.severity == AuditSeverity.INFO

    def test_log_login_failure(self):
        """Test log_login with failure."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_login(user_id="user-123", success=False)

        assert event.outcome == AuditOutcome.FAILURE
        assert event.severity == AuditSeverity.MEDIUM

    def test_log_logout(self):
        """Test log_logout convenience method."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_logout(user_id="user-123")

        assert event.action == AuditAction.LOGOUT
        assert event.audit_type == AuditEventType.AUTHENTICATION

    def test_log_permission_change(self):
        """Test log_permission_change."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        changes = [ChangeRecord(field="role", old_value="user", new_value="admin")]

        event = logger.log_permission_change(
            resource_type=ResourceType.USER,
            resource_id="user-123",
            changes=changes,
        )

        assert event.audit_type == AuditEventType.AUTHORIZATION
        assert event.severity == AuditSeverity.MEDIUM
        assert ComplianceFramework.SOC2 in event.compliance_frameworks

    def test_log_llm_interaction(self):
        """Test log_llm_interaction."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_llm_interaction(
            flow_id="flow-123",
            model="gpt-4o",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
        )

        assert event.audit_type == AuditEventType.AI_INTERACTION
        assert event.action == AuditAction.EXECUTE
        assert event.resource_type == ResourceType.LLM_MODEL
        assert event.metadata["model"] == "gpt-4o"
        assert event.metadata["cost_usd"] == 0.005

    def test_log_data_export(self):
        """Test log_data_export."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        event = logger.log_data_export(
            resource_type=ResourceType.DATASET,
            resource_id="dataset-123",
            export_format="csv",
            record_count=1000,
        )

        assert event.audit_type == AuditEventType.DATA_EXPORT
        assert event.action == AuditAction.EXPORT
        assert event.severity == AuditSeverity.MEDIUM
        assert ComplianceFramework.GDPR in event.compliance_frameworks

    def test_flush(self):
        """Test flush method."""
        mock_exporter = MagicMock()
        mock_exporter.flush.return_value = 0
        logger = AuditLogger(exporter=mock_exporter)

        result = logger.flush(timeout=10.0)

        assert result == 0
        mock_exporter.flush.assert_called_once_with(10.0)

    def test_flush_without_exporter(self):
        """Test flush without exporter."""
        logger = AuditLogger()
        result = logger.flush()
        assert result == 0

    def test_export_failure_logged(self):
        """Test that export failures are logged but don't raise."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.error(
            "Connection failed"
        )
        logger = AuditLogger(exporter=mock_exporter)

        # Should not raise
        event = logger.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-123",
        )

        assert event is not None

    def test_actor_context_in_metadata(self):
        """Test that actor context is added to metadata."""
        mock_exporter = MagicMock()
        mock_exporter.export_audit.return_value = ExportResult.ok()
        logger = AuditLogger(exporter=mock_exporter)

        actor = ActorContext(
            actor_id="user-123",
            roles=["admin"],
            groups=["team-a"],
            tenant_id="tenant-1",
            session_id="session-456",
        )
        set_actor_context(actor)

        event = logger.log(
            event_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-123",
        )

        assert "actor_context" in event.metadata
        assert event.metadata["actor_context"]["roles"] == ["admin"]
        assert event.metadata["actor_context"]["tenant_id"] == "tenant-1"
