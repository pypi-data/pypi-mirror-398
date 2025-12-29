"""Example: Audit Logging with Keycloak JWT Context.

This example demonstrates how to use the Autonomize Observer SDK for
compliance-focused audit logging with actor context from Keycloak JWTs.

Run with:
    python examples/audit_logging.py
"""

from autonomize_observer import (
    ActorContext,
    AuditAction,
    AuditEventType,
    ResourceType,
    audit,
    get_audit_logger,
    init,
    set_actor_context,
)
from autonomize_observer.schemas.audit import ChangeRecord

# Initialize the SDK (Kafka disabled for this example)
init(
    service_name="audit-example",
    kafka_enabled=False,
)


def example_basic_crud() -> None:
    """Example: Basic CRUD audit logging."""
    print("\n=== Basic CRUD Operations ===")

    # Set actor context (simulating a logged-in user)
    actor = ActorContext(
        actor_id="user-123",
        actor_type="user",
        email="john.doe@example.com",
        name="John Doe",
        roles=["admin", "analyst"],
    )
    set_actor_context(actor)

    # Log a CREATE event
    event = audit.log_create(
        resource_type=ResourceType.DOCUMENT,
        resource_id="doc-456",
        resource_name="Q4 Financial Report",
        description="Created new financial report document",
    )
    print(f"CREATE: {event.event_id} - {event.description}")

    # Log a READ event
    event = audit.log_read(
        resource_type=ResourceType.DOCUMENT,
        resource_id="doc-456",
        description="User viewed document",
    )
    print(f"READ: {event.event_id} - {event.description}")

    # Log an UPDATE event with changes
    event = audit.log_update(
        resource_type=ResourceType.DOCUMENT,
        resource_id="doc-456",
        changes=[
            ChangeRecord(
                field="title", old_value="Draft Report", new_value="Q4 Financial Report"
            ),
            ChangeRecord(field="status", old_value="draft", new_value="published"),
        ],
        description="Document published",
    )
    print(f"UPDATE: {event.event_id} - {event.description}")

    # Log a DELETE event
    event = audit.log_delete(
        resource_type=ResourceType.DOCUMENT,
        resource_id="doc-456",
        description="Document archived and deleted",
    )
    print(f"DELETE: {event.event_id} - {event.description}")


def example_keycloak_jwt() -> None:
    """Example: Using Keycloak JWT for actor context."""
    print("\n=== Keycloak JWT Context ===")

    # Simulate a Keycloak JWT payload
    jwt_payload = {
        "sub": "user-789",
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "preferred_username": "janesmith",
        "realm_access": {"roles": ["user", "data-analyst"]},
        "groups": ["/org/analytics", "/org/finance"],
    }

    # Create actor from JWT
    actor = ActorContext.from_keycloak_token(jwt_payload)
    set_actor_context(actor)

    print(f"Actor: {actor.name} ({actor.email})")
    print(f"Roles: {actor.roles}")

    # All subsequent audit events will include this actor context
    event = audit.log_read(
        resource_type=ResourceType.DATABASE,
        resource_id="customers-table",
        description="Queried customer analytics data",
    )
    print(f"Event actor: {event.actor_id}")


def example_llm_interaction() -> None:
    """Example: Logging LLM interactions for compliance."""
    print("\n=== LLM Interaction Logging ===")

    # Log an LLM call
    event = audit.log_llm_interaction(
        flow_id="customer-support-flow",
        model="gpt-4o",
        provider="openai",
        input_tokens=150,
        output_tokens=75,
        cost=0.025,
        metadata={
            "prompt_summary": "Customer inquiry about billing",
            "response_summary": "Provided billing information",
            "session_id": "session-abc",
        },
    )
    print(f"LLM Event: {event.event_id}")
    print(f"  Model: {event.metadata['model']}")
    print(f"  Tokens: {event.metadata['total_tokens']}")
    print(f"  Cost: ${event.metadata['cost_usd']:.4f}")


def example_custom_audit() -> None:
    """Example: Custom audit events with full control."""
    print("\n=== Custom Audit Events ===")

    logger = get_audit_logger()

    # Log a security event
    event = logger.log(
        event_type=AuditEventType.SECURITY_EVENT,
        action=AuditAction.EXECUTE,
        resource_type=ResourceType.API,
        resource_id="api/v1/admin/reset-password",
        description="Admin password reset executed",
        severity="HIGH",
        metadata={
            "target_user": "user-456",
            "requested_by": "admin-123",
            "reason": "User locked out",
        },
    )
    print(f"Security Event: {event.event_id}")
    print(f"  Severity: {event.severity}")


def example_system_actor() -> None:
    """Example: Using system and service actors."""
    print("\n=== System/Service Actors ===")

    # System actor for automated processes
    system = ActorContext.system()
    set_actor_context(system)
    print(f"System actor: {system.actor_id} (type: {system.actor_type})")

    event = audit.log_create(
        resource_type=ResourceType.FILE,
        resource_id="backup-2024-01-15.tar.gz",
        description="Automated daily backup created",
    )
    print(f"System event: {event.event_id}")

    # Service actor for service-to-service calls
    service = ActorContext.service("payment-service")
    set_actor_context(service)
    print(f"Service actor: {service.actor_id} (type: {service.actor_type})")

    event = audit.log_read(
        resource_type=ResourceType.API,
        resource_id="api/v1/transactions",
        description="Payment service fetched transactions",
    )
    print(f"Service event: {event.event_id}")


if __name__ == "__main__":
    print("Autonomize Observer - Audit Logging Examples")
    print("=" * 50)

    example_basic_crud()
    example_keycloak_jwt()
    example_llm_interaction()
    example_custom_audit()
    example_system_actor()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")
