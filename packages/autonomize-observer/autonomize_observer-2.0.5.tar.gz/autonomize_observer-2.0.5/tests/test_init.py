"""Tests for main autonomize_observer module."""

from unittest.mock import MagicMock, patch

import pytest

import autonomize_observer
from autonomize_observer import (
    AuditAction,
    AuditEventType,
    KafkaConfig,
    ObserverConfig,
    ResourceType,
    audit,
    configure,
    get_audit_logger,
    init,
    log_audit,
)
from autonomize_observer.schemas.audit import ChangeRecord


class TestInit:
    """Tests for init function."""

    def setup_method(self):
        """Reset module state before each test."""
        autonomize_observer._initialized = False
        autonomize_observer._audit_logger = None
        autonomize_observer._kafka_exporter = None

    def test_init_basic(self):
        """Test basic initialization."""
        with patch("logfire.configure") as mock_configure:
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(
                        service_name="test-service",
                        kafka_enabled=False,
                    )

                    assert autonomize_observer._initialized is True
                    mock_configure.assert_called_once()

    def test_init_idempotent(self):
        """Test that init is idempotent."""
        with patch("logfire.configure") as mock_configure:
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(service_name="test-1", kafka_enabled=False)
                    init(service_name="test-2", kafka_enabled=False)

                    # Should only be called once
                    mock_configure.assert_called_once()

    def test_init_with_kafka(self, mock_kafka_producer):
        """Test initialization with Kafka."""
        kafka_config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            audit_topic="test-audit",
        )

        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(
                        service_name="test-service",
                        kafka_config=kafka_config,
                        kafka_enabled=True,
                    )

                    assert autonomize_observer._kafka_exporter is not None
                    assert autonomize_observer._audit_logger is not None

    def test_init_without_openai_instrumentation(self):
        """Test initialization without OpenAI instrumentation."""
        with patch("logfire.configure"):
            with patch(
                "logfire.instrument_openai", side_effect=Exception("Not installed")
            ):
                with patch("logfire.instrument_anthropic"):
                    # Should not raise
                    init(
                        service_name="test-service",
                        kafka_enabled=False,
                        instrument_openai=True,
                    )

    def test_init_without_anthropic_instrumentation(self):
        """Test initialization without Anthropic instrumentation."""
        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch(
                    "logfire.instrument_anthropic",
                    side_effect=Exception("Not installed"),
                ):
                    # Should not raise
                    init(
                        service_name="test-service",
                        kafka_enabled=False,
                        instrument_anthropic=True,
                    )

    def test_init_all_options(self, mock_kafka_producer):
        """Test initialization with all options."""
        kafka_config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            audit_topic="test-audit",
        )

        with patch("logfire.configure") as mock_configure:
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(
                        service_name="test-service",
                        service_version="2.0.0",
                        environment="staging",
                        send_to_logfire=True,
                        kafka_config=kafka_config,
                        kafka_enabled=True,
                        keycloak_claim_mappings={"email": "custom_email"},
                        instrument_openai=True,
                        instrument_anthropic=True,
                    )

                    call_kwargs = mock_configure.call_args[1]
                    assert call_kwargs["service_name"] == "test-service"
                    assert call_kwargs["service_version"] == "2.0.0"
                    assert call_kwargs["environment"] == "staging"
                    assert call_kwargs["send_to_logfire"] is True


class TestConfigure:
    """Tests for configure function."""

    def setup_method(self):
        """Reset module state before each test."""
        autonomize_observer._initialized = False
        autonomize_observer._audit_logger = None
        autonomize_observer._kafka_exporter = None

    def test_configure_basic(self):
        """Test basic configuration."""
        config = ObserverConfig(
            service_name="test-service",
            kafka_enabled=False,
        )

        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    configure(config)

                    assert autonomize_observer._initialized is True

    def test_configure_with_kafka(self, mock_kafka_producer):
        """Test configuration with Kafka."""
        config = ObserverConfig(
            service_name="test-service",
            kafka=KafkaConfig(
                bootstrap_servers="localhost:9092",
                audit_topic="test-audit",
            ),
            kafka_enabled=True,
        )

        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    configure(config)

                    assert autonomize_observer._kafka_exporter is not None


class TestGetAuditLogger:
    """Tests for get_audit_logger function."""

    def setup_method(self):
        """Reset module state before each test."""
        autonomize_observer._initialized = False
        autonomize_observer._audit_logger = None
        autonomize_observer._kafka_exporter = None

    def test_get_audit_logger_not_initialized(self):
        """Test getting logger when not initialized."""
        with pytest.raises(RuntimeError) as exc_info:
            get_audit_logger()
        assert "not initialized" in str(exc_info.value).lower()

    def test_get_audit_logger_initialized(self):
        """Test getting logger after initialization."""
        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(service_name="test-service", kafka_enabled=False)

                    logger = get_audit_logger()
                    assert logger is not None


class TestLogAudit:
    """Tests for log_audit function."""

    def setup_method(self):
        """Reset module state before each test."""
        autonomize_observer._initialized = False
        autonomize_observer._audit_logger = None
        autonomize_observer._kafka_exporter = None

    def test_log_audit(self):
        """Test log_audit convenience function."""
        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(service_name="test-service", kafka_enabled=False)

                    event = log_audit(
                        event_type=AuditEventType.DATA_ACCESS,
                        action=AuditAction.READ,
                        resource_type=ResourceType.DOCUMENT,
                        resource_id="doc-123",
                    )

                    assert event is not None
                    assert event.resource_id == "doc-123"


class TestAuditShortcuts:
    """Tests for audit module shortcuts."""

    def setup_method(self):
        """Reset module state before each test."""
        autonomize_observer._initialized = False
        autonomize_observer._audit_logger = None
        autonomize_observer._kafka_exporter = None

        with patch("logfire.configure"):
            with patch("logfire.instrument_openai"):
                with patch("logfire.instrument_anthropic"):
                    init(service_name="test-service", kafka_enabled=False)

    def test_log_create(self):
        """Test audit.log_create shortcut."""
        event = audit.log_create(
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-new",
            resource_name="New Doc",
        )

        assert event.action == AuditAction.CREATE
        assert event.resource_id == "doc-new"

    def test_log_read(self):
        """Test audit.log_read shortcut."""
        event = audit.log_read(
            resource_type=ResourceType.FILE,
            resource_id="file-123",
        )

        assert event.action == AuditAction.READ
        assert event.resource_id == "file-123"

    def test_log_update(self):
        """Test audit.log_update shortcut."""
        changes = [
            ChangeRecord(field="name", old_value="Old", new_value="New"),
        ]

        event = audit.log_update(
            resource_type=ResourceType.USER,
            resource_id="user-123",
            changes=changes,
        )

        assert event.action == AuditAction.UPDATE
        assert len(event.changes) == 1

    def test_log_delete(self):
        """Test audit.log_delete shortcut."""
        event = audit.log_delete(
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc-to-delete",
        )

        assert event.action == AuditAction.DELETE
        assert event.resource_id == "doc-to-delete"

    def test_log_login(self):
        """Test audit.log_login shortcut."""
        event = audit.log_login(user_id="user-123", success=True)

        assert event.action == AuditAction.LOGIN
        assert event.audit_type == AuditEventType.AUTHENTICATION

    def test_log_llm_interaction(self):
        """Test audit.log_llm_interaction shortcut."""
        event = audit.log_llm_interaction(
            flow_id="flow-123",
            model="gpt-4o",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost=0.005,
        )

        assert event.audit_type == AuditEventType.AI_INTERACTION
        assert event.action == AuditAction.EXECUTE


class TestModuleExports:
    """Tests for module exports."""

    def test_version(self):
        """Test version is exported."""
        assert autonomize_observer.__version__ == "2.0.0"

    def test_all_exports(self):
        """Test all exports are available."""
        expected = [
            "__version__",
            "init",
            "configure",
            "ObserverConfig",
            "KafkaConfig",
            "AuditLogger",
            "AuditEvent",
            "ChangeRecord",
            "ActorContext",
            "get_actor_context",
            "set_actor_context",
            "set_actor_from_keycloak_token",
            "AuditAction",
            "AuditEventType",
            "AuditOutcome",
            "AuditSeverity",
            "ComplianceFramework",
            "ResourceType",
            "calculate_cost",
            "get_price",
            "KafkaExporter",
        ]

        for name in expected:
            assert name in autonomize_observer.__all__, f"Missing export: {name}"
