"""Tests for schema definitions."""

from datetime import datetime, timezone

import pytest

from autonomize_observer.schemas.audit import AuditEvent, ChangeRecord
from autonomize_observer.schemas.base import (
    BaseEvent,
    generate_event_id,
    generate_span_id,
    generate_trace_id,
)
from autonomize_observer.schemas.enums import (
    AuditAction,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    ComplianceFramework,
    EventCategory,
    ResourceType,
)


class TestGenerators:
    """Tests for ID generators."""

    def test_generate_event_id(self):
        """Test event ID generation."""
        event_id = generate_event_id()
        assert isinstance(event_id, str)
        assert len(event_id) == 16  # 16 hex chars (8 bytes)

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = generate_trace_id()
        assert isinstance(trace_id, str)
        assert len(trace_id) == 32  # 32 hex chars

    def test_generate_span_id(self):
        """Test span ID generation."""
        span_id = generate_span_id()
        assert isinstance(span_id, str)
        assert len(span_id) == 16  # 16 hex chars

    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = [generate_event_id() for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestBaseEvent:
    """Tests for BaseEvent model."""

    def test_default_values(self):
        """Test default values."""
        event = BaseEvent()
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.event_category == EventCategory.TRACE
        assert event.attributes == {}
        assert event.metadata == {}

    def test_custom_values(self):
        """Test custom values."""
        timestamp_str = datetime.now(timezone.utc).isoformat()
        event = BaseEvent(
            event_id="custom-id",
            timestamp=timestamp_str,
            event_category=EventCategory.AUDIT,
            user_id="user-123",
            session_id="session-456",
            project_name="test-project",
            attributes={"key": "value"},
            metadata={"meta": "data"},
        )
        assert event.event_id == "custom-id"
        assert event.timestamp == timestamp_str
        assert event.event_category == EventCategory.AUDIT
        assert event.user_id == "user-123"
        assert event.session_id == "session-456"
        assert event.project_name == "test-project"
        assert event.attributes["key"] == "value"
        assert event.metadata["meta"] == "data"


class TestChangeRecord:
    """Tests for ChangeRecord model."""

    def test_basic_creation(self):
        """Test basic change record."""
        change = ChangeRecord(
            field="name",
            old_value="Old Name",
            new_value="New Name",
        )
        assert change.field == "name"
        assert change.old_value == "Old Name"
        assert change.new_value == "New Name"

    def test_none_values(self):
        """Test change record with None values."""
        change = ChangeRecord(field="status")
        assert change.field == "status"
        assert change.old_value is None
        assert change.new_value is None


class TestAuditEvent:
    """Tests for AuditEvent model."""

    def test_default_values(self):
        """Test default values."""
        event = AuditEvent()
        assert event.event_category == EventCategory.AUDIT
        assert event.audit_type == AuditEventType.RESOURCE_READ
        assert event.action == AuditAction.READ
        assert event.severity == AuditSeverity.INFO
        assert event.outcome == AuditOutcome.SUCCESS
        assert event.actor_id == ""
        assert event.actor_type == "user"
        assert event.resource_type == ResourceType.RESOURCE
        assert event.resource_id == ""
        assert event.changes == []
        assert event.compliance_frameworks == []
        assert event.retention_days == 365
        assert event.immutable is True

    def test_custom_values(self):
        """Test custom values."""
        event = AuditEvent(
            audit_type=AuditEventType.DATA_MODIFICATION,
            action=AuditAction.UPDATE,
            severity=AuditSeverity.MEDIUM,
            outcome=AuditOutcome.SUCCESS,
            actor_id="user-123",
            actor_type="service",
            actor_email="user@example.com",
            actor_name="Test User",
            ip_address="192.168.1.1",
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-456",
            resource_name="Important Doc",
            description="Updated document",
            compliance_frameworks=[ComplianceFramework.HIPAA],
            retention_days=730,
            service_name="my-service",
        )
        assert event.audit_type == AuditEventType.DATA_MODIFICATION
        assert event.action == AuditAction.UPDATE
        assert event.severity == AuditSeverity.MEDIUM
        assert event.actor_id == "user-123"
        assert event.actor_email == "user@example.com"
        assert event.ip_address == "192.168.1.1"
        assert event.resource_type == ResourceType.DOCUMENT
        assert ComplianceFramework.HIPAA in event.compliance_frameworks

    def test_add_change(self):
        """Test adding change records."""
        event = AuditEvent()
        event.add_change("name", "Old", "New")
        event.add_change("status", "draft", "published")

        assert len(event.changes) == 2
        assert event.changes[0].field == "name"
        assert event.changes[0].old_value == "Old"
        assert event.changes[0].new_value == "New"

    def test_enum_values_serialization(self):
        """Test that enum values serialize correctly."""
        event = AuditEvent(
            audit_type=AuditEventType.DATA_ACCESS,
            action=AuditAction.READ,
            resource_type=ResourceType.DOCUMENT,
        )
        data = event.model_dump()

        # Values should be strings due to use_enum_values
        assert data["audit_type"] == "data_access"
        assert data["action"] == "read"
        assert data["resource_type"] == "document"


class TestAuditEnums:
    """Tests for audit-related enums."""

    def test_audit_event_type_values(self):
        """Test AuditEventType values."""
        assert AuditEventType.RESOURCE_CREATED.value == "resource_created"
        assert AuditEventType.DATA_ACCESS.value == "data_access"
        assert AuditEventType.AI_INTERACTION.value == "ai_interaction"

    def test_audit_action_values(self):
        """Test AuditAction values."""
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.READ.value == "read"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.EXECUTE.value == "execute"

    def test_audit_severity_values(self):
        """Test AuditSeverity values."""
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.LOW.value == "low"
        assert AuditSeverity.MEDIUM.value == "medium"
        assert AuditSeverity.HIGH.value == "high"
        assert AuditSeverity.CRITICAL.value == "critical"

    def test_audit_outcome_values(self):
        """Test AuditOutcome values."""
        assert AuditOutcome.SUCCESS.value == "success"
        assert AuditOutcome.FAILURE.value == "failure"
        assert AuditOutcome.PARTIAL.value == "partial"
        assert AuditOutcome.DENIED.value == "denied"

    def test_compliance_framework_values(self):
        """Test ComplianceFramework values."""
        assert ComplianceFramework.HIPAA.value == "hipaa"
        assert ComplianceFramework.GDPR.value == "gdpr"
        assert ComplianceFramework.SOC2.value == "soc2"
        assert ComplianceFramework.PCI_DSS.value == "pci_dss"

    def test_resource_type_values(self):
        """Test ResourceType values."""
        assert ResourceType.DOCUMENT.value == "document"
        assert ResourceType.USER.value == "user"
        assert ResourceType.FLOW.value == "flow"
        assert ResourceType.LLM_MODEL.value == "llm_model"


class TestBaseEventMethods:
    """Tests for BaseEvent methods."""

    def test_to_dict(self):
        """Test to_dict method."""
        event = BaseEvent(
            event_id="test-id",
            user_id="user-123",
            attributes={"key": "value"},
        )
        data = event.to_dict()

        assert isinstance(data, dict)
        assert data["event_id"] == "test-id"
        assert data["user_id"] == "user-123"
        assert data["attributes"]["key"] == "value"

    def test_to_json(self):
        """Test to_json method."""
        event = BaseEvent(
            event_id="test-id",
            user_id="user-123",
        )
        json_str = event.to_json()

        assert isinstance(json_str, str)
        assert "test-id" in json_str
        assert "user-123" in json_str

    def test_from_dict(self):
        """Test from_dict method."""
        data = {
            "event_id": "from-dict-id",
            "user_id": "user-456",
            "project_name": "test-project",
        }
        event = BaseEvent.from_dict(data)

        assert event.event_id == "from-dict-id"
        assert event.user_id == "user-456"
        assert event.project_name == "test-project"
