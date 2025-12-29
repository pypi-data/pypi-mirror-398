"""Autonomize Observer - Unified LLM Observability & Audit SDK.

A thin wrapper around Pydantic Logfire that adds:
- Audit logging with Keycloak JWT user context
- Kafka export for audit events
- Langflow/Flow integration

For LLM tracing, use Logfire directly:
    import logfire
    logfire.configure(send_to_logfire=False)
    logfire.instrument_openai()
    logfire.instrument_anthropic()

For audit logging:
    from autonomize_observer import init, audit
    init(service_name="my-service")
    audit.log_create(resource_type=ResourceType.DOCUMENT, resource_id="doc-123")

For Langflow flows:
    from autonomize_observer.integrations import trace_flow, trace_component

    @trace_flow(flow_id="flow-1", flow_name="My Flow")
    def run_flow():
        ...
"""

from autonomize_observer.audit import (
    ActorContext,
    AuditLogger,
    get_actor_context,
    set_actor_context,
    set_actor_from_keycloak_token,
)
from autonomize_observer.core.config import KafkaConfig, ObserverConfig
from autonomize_observer.cost import calculate_cost, get_price
from autonomize_observer.exporters import KafkaExporter
from autonomize_observer.schemas.audit import AuditEvent, ChangeRecord
from autonomize_observer.schemas.enums import (
    AuditAction,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    ComplianceFramework,
    ResourceType,
)

__version__ = "2.0.0"
__all__ = [
    # Version
    "__version__",
    # Initialization
    "init",
    "configure",
    # Configuration
    "ObserverConfig",
    "KafkaConfig",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "ChangeRecord",
    "ActorContext",
    "get_actor_context",
    "set_actor_context",
    "set_actor_from_keycloak_token",
    # Audit enums
    "AuditAction",
    "AuditEventType",
    "AuditOutcome",
    "AuditSeverity",
    "ComplianceFramework",
    "ResourceType",
    # Cost
    "calculate_cost",
    "get_price",
    # Exporters
    "KafkaExporter",
]

# Global instances
_audit_logger: AuditLogger | None = None
_kafka_exporter: KafkaExporter | None = None
_initialized: bool = False


def init(
    service_name: str = "autonomize-service",
    service_version: str = "1.0.0",
    environment: str = "production",
    send_to_logfire: bool = False,
    kafka_config: KafkaConfig | None = None,
    kafka_enabled: bool = True,
    keycloak_claim_mappings: dict[str, str] | None = None,
    instrument_openai: bool = True,
    instrument_anthropic: bool = True,
) -> None:
    """Initialize Autonomize Observer.

    This sets up:
    1. Logfire for tracing (with optional LLM instrumentation)
    2. Kafka exporter for audit events
    3. Audit logger

    Args:
        service_name: Name of your service
        service_version: Version of your service
        environment: Deployment environment
        send_to_logfire: Whether to send data to Pydantic Logfire cloud
        kafka_config: Kafka configuration for audit export
        kafka_enabled: Whether to enable Kafka export
        keycloak_claim_mappings: Custom JWT claim mappings
        instrument_openai: Whether to instrument OpenAI client
        instrument_anthropic: Whether to instrument Anthropic client

    Example:
        from autonomize_observer import init

        init(
            service_name="my-service",
            kafka_config=KafkaConfig(
                bootstrap_servers="kafka:9092",
                audit_topic="audit-events",
            ),
        )
    """
    global _audit_logger, _kafka_exporter, _initialized

    if _initialized:
        return

    # Configure Logfire
    import logfire

    logfire.configure(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        send_to_logfire=send_to_logfire,
    )

    # Instrument LLM clients
    if instrument_openai:
        try:
            logfire.instrument_openai()
        except Exception:
            pass  # OpenAI not installed

    if instrument_anthropic:
        try:
            logfire.instrument_anthropic()
        except Exception:
            pass  # Anthropic not installed

    # Set up Kafka exporter
    if kafka_enabled and kafka_config:
        _kafka_exporter = KafkaExporter(kafka_config)
        _kafka_exporter.initialize()

    # Set up audit logger
    _audit_logger = AuditLogger(
        exporter=_kafka_exporter,
        service_name=service_name,
    )

    # Register Keycloak claim mappings if provided
    if keycloak_claim_mappings:
        from autonomize_observer.audit.context import register_actor_provider

        # This could be used for custom extraction logic
        pass

    _initialized = True


def configure(config: ObserverConfig) -> None:
    """Initialize from an ObserverConfig object.

    Args:
        config: ObserverConfig with all settings

    Example:
        from autonomize_observer import configure, ObserverConfig, KafkaConfig

        config = ObserverConfig(
            service_name="my-service",
            kafka=KafkaConfig(bootstrap_servers="kafka:9092"),
        )
        configure(config)
    """
    kafka_config = config.kafka if config.kafka_enabled else None

    init(
        service_name=config.service_name,
        service_version=config.service_version,
        environment=config.environment,
        send_to_logfire=config.send_to_logfire,
        kafka_config=kafka_config,
        kafka_enabled=config.kafka_enabled,
        keycloak_claim_mappings=config.keycloak_claim_mappings or None,
    )


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger.

    Returns:
        AuditLogger instance

    Raises:
        RuntimeError: If not initialized
    """
    if _audit_logger is None:
        raise RuntimeError("Not initialized. Call init() first.")
    return _audit_logger


# Convenience aliases for audit logging
def log_audit(
    event_type: AuditEventType,
    action: AuditAction,
    resource_type: ResourceType,
    resource_id: str,
    **kwargs,
) -> AuditEvent:
    """Log an audit event.

    Convenience function that uses the global audit logger.
    """
    return get_audit_logger().log(
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        **kwargs,
    )


# Module-level audit shortcuts
class audit:
    """Module-level audit logging shortcuts."""

    @staticmethod
    def log_create(
        resource_type: ResourceType,
        resource_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log a resource creation."""
        return get_audit_logger().log_create(
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    @staticmethod
    def log_read(
        resource_type: ResourceType,
        resource_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log a resource read/access."""
        return get_audit_logger().log_read(
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    @staticmethod
    def log_update(
        resource_type: ResourceType,
        resource_id: str,
        changes: list[ChangeRecord],
        **kwargs,
    ) -> AuditEvent:
        """Log a resource update."""
        return get_audit_logger().log_update(
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            **kwargs,
        )

    @staticmethod
    def log_delete(
        resource_type: ResourceType,
        resource_id: str,
        **kwargs,
    ) -> AuditEvent:
        """Log a resource deletion."""
        return get_audit_logger().log_delete(
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    @staticmethod
    def log_login(
        user_id: str,
        success: bool = True,
        **kwargs,
    ) -> AuditEvent:
        """Log a login event."""
        return get_audit_logger().log_login(
            user_id=user_id,
            success=success,
            **kwargs,
        )

    @staticmethod
    def log_llm_interaction(
        flow_id: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        **kwargs,
    ) -> AuditEvent:
        """Log an LLM interaction for audit purposes."""
        return get_audit_logger().log_llm_interaction(
            flow_id=flow_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            **kwargs,
        )
