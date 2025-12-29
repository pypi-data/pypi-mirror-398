# Autonomize Observer Usage Guide

This comprehensive guide covers all features of the Autonomize Observer SDK with detailed examples.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Initialization](#initialization)
3. [Audit Logging](#audit-logging)
4. [Actor Context](#actor-context)
5. [Cost Calculation](#cost-calculation)
6. [Kafka Export](#kafka-export)
7. [LLM Tracing with Logfire](#llm-tracing-with-logfire)
8. [Standalone Agent Tracing](#standalone-agent-tracing)
9. [Workflow Tracing](#workflow-tracing)
10. [AI Studio Agent Tracing](#ai-studio-agent-tracing)
11. [Error Handling](#error-handling)
12. [Best Practices](#best-practices)

---

## Core Concepts

### Philosophy

The Autonomize Observer SDK follows a **thin wrapper** philosophy:

- **Don't reinvent the wheel**: We use Pydantic Logfire for OTEL tracing and genai-prices for cost calculation
- **Focus on what's unique**: Audit logging, Keycloak integration, Kafka export, and Langflow support
- **Stay lightweight**: Minimal overhead, simple API, easy to understand

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Application                             │
├─────────────────────────────────────────────────────────────────┤
│                  Autonomize Observer SDK                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Audit Logger │  │ Actor Context│  │ Kafka Exporter       │  │
│  │              │  │ (Keycloak)   │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  External Libraries                                              │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Logfire      │  │ genai-prices │                             │
│  │ (Tracing)    │  │ (Costs)      │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Initialization

### Basic Initialization

```python
from autonomize_observer import init

# Minimal initialization (Kafka disabled)
init(
    service_name="my-service",
    kafka_enabled=False,
)
```

### Full Initialization

```python
from autonomize_observer import init, KafkaConfig

init(
    service_name="my-service",
    service_version="1.0.0",
    environment="production",

    # Logfire settings
    send_to_logfire=False,  # Keep data local

    # LLM instrumentation
    instrument_openai=True,
    instrument_anthropic=True,

    # Kafka settings
    kafka_config=KafkaConfig(
        bootstrap_servers="kafka:9092",
        audit_topic="audit-events",
    ),
    kafka_enabled=True,

    # Keycloak JWT claim mappings
    keycloak_claim_mappings={
        "actor_id": "sub",
        "email": "email",
        "name": "name",
        "roles": "realm_access.roles",
    },
)
```

### Configuration Object

```python
from autonomize_observer import configure, ObserverConfig, KafkaConfig

config = ObserverConfig(
    service_name="my-service",
    service_version="1.0.0",
    environment="production",
    send_to_logfire=False,
    kafka=KafkaConfig(
        bootstrap_servers="kafka:9092",
        audit_topic="audit-events",
    ),
    kafka_enabled=True,
)

configure(config)
```

### Initialization is Idempotent

```python
# Safe to call multiple times - only first call takes effect
init(service_name="service-1")
init(service_name="service-2")  # Ignored, already initialized
```

---

## Audit Logging

### Audit Event Types

```python
from autonomize_observer import AuditEventType

# Available event types
AuditEventType.DATA_ACCESS        # Reading data
AuditEventType.DATA_MODIFICATION  # Creating, updating, deleting data
AuditEventType.AUTHENTICATION     # Login, logout
AuditEventType.AUTHORIZATION      # Permission changes
AuditEventType.AI_INTERACTION     # LLM calls
AuditEventType.SYSTEM_EVENT       # System operations
AuditEventType.SECURITY_EVENT     # Security-related events
AuditEventType.COMPLIANCE_EVENT   # Compliance-related events
```

### Resource Types

```python
from autonomize_observer import ResourceType

# Available resource types
ResourceType.USER
ResourceType.DOCUMENT
ResourceType.FILE
ResourceType.API
ResourceType.DATABASE
ResourceType.MODEL
ResourceType.FLOW
ResourceType.COMPONENT
ResourceType.SESSION
ResourceType.CONVERSATION
ResourceType.MESSAGE
ResourceType.AGENT
ResourceType.LLM_MODEL
```

### CRUD Operations

```python
from autonomize_observer import audit, ResourceType
from autonomize_observer.schemas.audit import ChangeRecord

# Create
event = audit.log_create(
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    resource_name="Project Proposal",
    description="Created new project proposal document",
)

# Read
event = audit.log_read(
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    description="User viewed document",
)

# Update
event = audit.log_update(
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    changes=[
        ChangeRecord(field="title", old_value="Draft", new_value="Final"),
        ChangeRecord(field="status", old_value="pending", new_value="approved"),
    ],
    description="Document approved and finalized",
)

# Delete
event = audit.log_delete(
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    description="Document deleted by user",
)
```

### Authentication Events

```python
from autonomize_observer import audit

# Successful login
audit.log_login(
    user_id="user-123",
    success=True,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
)

# Failed login
audit.log_login(
    user_id="user-123",
    success=False,
    reason="Invalid password",
    ip_address="192.168.1.100",
)

# Logout
audit.log_logout(
    user_id="user-123",
)
```

### LLM Interaction Logging

```python
from autonomize_observer import audit

# Log an LLM call for compliance
audit.log_llm_interaction(
    flow_id="customer-support-flow",
    model="gpt-4o",
    provider="openai",
    input_tokens=150,
    output_tokens=75,
    cost=0.025,
    prompt_summary="Customer inquiry about billing",
    response_summary="Provided billing information",
)
```

### Data Export Logging

```python
from autonomize_observer import audit, ResourceType

# Log data export for compliance
audit.log_data_export(
    resource_type=ResourceType.DATABASE,
    resource_id="customers-table",
    export_format="CSV",
    record_count=1500,
    destination="s3://exports/customers.csv",
    reason="Monthly analytics report",
)
```

### Custom Audit Events

```python
from autonomize_observer import (
    get_audit_logger,
    AuditEventType, AuditAction, ResourceType,
)

logger = get_audit_logger()

event = logger.log(
    event_type=AuditEventType.SECURITY_EVENT,
    action=AuditAction.EXECUTE,
    resource_type=ResourceType.API,
    resource_id="api/v1/admin/reset",
    description="Admin password reset executed",
    severity="HIGH",
    metadata={
        "target_user": "user-456",
        "requested_by": "admin-123",
    },
)
```

---

## Actor Context

### Setting Actor Context

```python
from autonomize_observer import ActorContext, set_actor_context

# Create actor context
actor = ActorContext(
    actor_id="user-123",
    actor_type="user",
    email="user@example.com",
    name="John Doe",
    roles=["admin", "analyst"],
    groups=["/org/engineering"],
    session_id="session-456",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
)

# Set as current context
set_actor_context(actor)

# All audit events now include this user context
```

### From Keycloak JWT

```python
from autonomize_observer import ActorContext, set_actor_context

# JWT payload from Keycloak
jwt_payload = {
    "sub": "user-123",
    "email": "user@example.com",
    "name": "John Doe",
    "preferred_username": "johndoe",
    "realm_access": {
        "roles": ["admin", "user"]
    },
    "groups": ["/org/engineering"],
}

# Create actor from JWT
actor = ActorContext.from_keycloak_token(jwt_payload)
set_actor_context(actor)
```

### Custom Claim Mappings

```python
from autonomize_observer import ActorContext

# Custom JWT structure
jwt_payload = {
    "user_id": "user-123",
    "user_email": "user@example.com",
    "permissions": ["read", "write"],
}

# Map custom claims
actor = ActorContext.from_keycloak_token(
    jwt_payload,
    claim_mappings={
        "actor_id": "user_id",
        "email": "user_email",
        "roles": "permissions",
    },
)
```

### From Raw JWT Token

```python
from autonomize_observer import set_actor_from_keycloak_token

# Decode and set actor from raw JWT string
jwt_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

set_actor_from_keycloak_token(
    jwt_token,
    verify=False,  # Skip signature verification (done by API gateway)
)
```

### Actor Providers

For automatic actor resolution:

```python
from autonomize_observer.audit.context import (
    register_actor_provider,
    get_actor_context,
)

def get_actor_from_request():
    """Custom actor provider."""
    # Get from thread-local request context
    from flask import g
    if hasattr(g, 'current_user'):
        return ActorContext(
            actor_id=g.current_user.id,
            email=g.current_user.email,
        )
    return None

# Register provider
register_actor_provider(get_actor_from_request)

# Now get_actor_context() will use provider if no explicit context set
actor = get_actor_context()
```

### System and Service Actors

```python
from autonomize_observer import ActorContext

# System actor for automated processes
system = ActorContext.system()
set_actor_context(system)

# Service actor for service-to-service calls
service = ActorContext.service("payment-service")
set_actor_context(service)
```

---

## Cost Calculation

### Calculate LLM Costs

```python
from autonomize_observer import calculate_cost

# Calculate cost for a completion
result = calculate_cost(
    provider="openai",
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=500,
)

print(f"Input cost: ${result.input_cost:.4f}")
print(f"Output cost: ${result.output_cost:.4f}")
print(f"Total cost: ${result.total_cost:.4f}")
```

### With Cached Tokens

```python
result = calculate_cost(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    input_tokens=2000,
    output_tokens=500,
    cached_tokens=1500,  # Cached portion of input tokens
)
```

### Get Model Pricing

```python
from autonomize_observer import get_price

price = get_price("openai", "gpt-4o")

if price:
    print(f"Provider: {price.provider}")
    print(f"Model: {price.model}")
    print(f"Input: ${price.input_price_per_1k:.4f}/1K tokens")
    print(f"Output: ${price.output_price_per_1k:.4f}/1K tokens")
else:
    print("Pricing not available for this model")
```

### Supported Providers

The SDK uses [genai-prices](https://github.com/jetify-com/genai-prices) which supports 28+ providers:

- OpenAI (GPT-4, GPT-4o, GPT-3.5, etc.)
- Anthropic (Claude 3.5, Claude 3, etc.)
- Google (Gemini Pro, Gemini Flash, etc.)
- Mistral
- Cohere
- AI21
- And many more...

---

## Kafka Export

### Configuration

```python
from autonomize_observer import init, KafkaConfig

init(
    service_name="my-service",
    kafka_config=KafkaConfig(
        bootstrap_servers="kafka:9092",
        audit_topic="audit-events",
        client_id="my-service-producer",

        # Security settings
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        sasl_username="user",
        sasl_password="password",

        # Performance settings
        acks="all",
        retries=3,
        batch_size=16384,
        linger_ms=5,
    ),
    kafka_enabled=True,
)
```

### Direct Exporter Usage

```python
from autonomize_observer.exporters import KafkaExporter
from autonomize_observer.core.config import KafkaConfig

# Create exporter
config = KafkaConfig(
    bootstrap_servers="kafka:9092",
    audit_topic="audit-events",
)
exporter = KafkaExporter(config)
exporter.initialize()

# Export audit event
from autonomize_observer.schemas.audit import AuditEvent

event = AuditEvent(
    service_name="my-service",
    resource_type="DOCUMENT",
    resource_id="doc-123",
    action="CREATE",
)

result = exporter.export_audit(event)
print(f"Export success: {result.success}")

# Export custom event
result = exporter.export_custom_event(
    topic="custom-events",
    key="my-key",
    data={"event_type": "custom", "data": {...}},
)

# Cleanup
exporter.flush()
exporter.shutdown()
```

### Event Format

Audit events are exported as JSON:

```json
{
    "event_id": "evt_abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "service_name": "my-service",
    "audit_type": "DATA_MODIFICATION",
    "action": "CREATE",
    "resource_type": "DOCUMENT",
    "resource_id": "doc-123",
    "resource_name": "Project Proposal",
    "actor": {
        "actor_id": "user-123",
        "email": "user@example.com",
        "roles": ["admin"]
    },
    "outcome": "SUCCESS",
    "severity": "INFO",
    "metadata": {}
}
```

---

## LLM Tracing with Logfire

### Basic Setup

```python
import logfire
from openai import OpenAI

# Configure Logfire
logfire.configure(
    service_name="my-service",
    send_to_logfire=False,  # Keep data local
)

# Instrument LLM clients
logfire.instrument_openai()

# Use normally - all calls are traced
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Using Observer's Logfire Wrapper

```python
from autonomize_observer.tracing import (
    configure_logfire,
    instrument_llms,
    instrument_web_framework,
)

# Configure with our wrapper
logfire_instance = configure_logfire(
    service_name="my-service",
    send_to_logfire=False,
)

# Instrument LLMs
instrument_llms(openai=True, anthropic=True)

# Instrument web framework
instrument_web_framework("fastapi", app=app)
```

### Custom Spans

```python
import logfire

# Create custom spans for business logic
with logfire.span("process-document", document_id="doc-123"):
    # Your logic here
    logfire.info("Document processed", pages=10)
```

---

## Standalone Agent Tracing

For tracing custom agents or LLM workflows outside of AI Studio, use Logfire directly with automatic LLM instrumentation.

### Complete Example: Custom RAG Agent

```python
import logfire
from openai import OpenAI
from autonomize_observer import calculate_cost

# One-time setup
logfire.configure(
    service_name="rag-agent",
    send_to_logfire=False,  # Keep data local or export to your OTEL collector
)

# Auto-instrument LLM clients
logfire.instrument_openai()

client = OpenAI()


def retrieve_documents(query: str) -> list[str]:
    """Retrieve relevant documents from vector store."""
    with logfire.span("retrieve", query=query):
        # Your retrieval logic
        docs = ["Doc 1 content...", "Doc 2 content..."]
        logfire.info("Retrieved documents", count=len(docs))
        return docs


def generate_response(query: str, context: list[str]) -> str:
    """Generate response using LLM."""
    with logfire.span("generate", query=query, context_size=len(context)):
        # LLM call is automatically traced with tokens/cost
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Context: {' '.join(context)}"},
                {"role": "user", "content": query},
            ],
        )

        # Calculate and log cost
        cost_result = calculate_cost(
            provider="openai",
            model="gpt-4o",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        logfire.info(
            "LLM response",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            cost=cost_result.total_cost,
        )

        return response.choices[0].message.content


def rag_query(query: str) -> str:
    """Main RAG pipeline."""
    with logfire.span("rag-query", query=query, _tags=["rag", "agent"]):
        docs = retrieve_documents(query)
        response = generate_response(query, docs)
        return response


# Use the agent
result = rag_query("What are the key findings?")
```

### Multi-Agent Workflow

Use `WorkflowTracer` for step-based timing combined with Logfire's LLM auto-instrumentation:

```python
import logfire
from openai import OpenAI
from anthropic import Anthropic
from autonomize_observer.tracing import WorkflowTracer

# Logfire auto-instruments LLM calls (tokens, latency, etc.)
logfire.configure(service_name="multi-agent", send_to_logfire=False)
logfire.instrument_openai()
logfire.instrument_anthropic()

openai_client = OpenAI()
anthropic_client = Anthropic()


def multi_agent_pipeline(topic: str) -> str:
    """Multi-agent workflow with step timing."""
    with WorkflowTracer("multi-agent-pipeline", topic=topic) as tracer:
        # Step 1: Research with GPT-4o
        with tracer.step("research-agent") as step:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Research: {topic}"}],
            )
            research = response.choices[0].message.content
            step.set("model", "gpt-4o")
            step.set("research_length", len(research))

        # Step 2: Analysis with Claude
        with tracer.step("analysis-agent") as step:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": f"Analyze: {research}"}],
            )
            analysis = response.content[0].text
            step.set("model", "claude-3-5-sonnet")
            step.set("analysis_length", len(analysis))

        tracer.set("status", "completed")
        return analysis

    # Access timing after workflow
    print(f"Total: {tracer.duration_ms:.2f}ms")
    for step in tracer.steps:
        print(f"  {step.name}: {step.duration_ms:.2f}ms")
```

This gives you:
- **WorkflowTracer**: Step-by-step timing and attributes
- **Logfire instrumentation**: Automatic token counts, costs, and LLM-specific spans

### Exporting Traces to Kafka with OTEL Collector

You can export OTEL traces to Kafka using the OpenTelemetry Collector:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  kafka:
    brokers:
      - kafka:9092
    topic: genesis-otel
    encoding: otlp_json

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [kafka]
```

Then configure Logfire to send to the collector:

```python
import logfire

logfire.configure(
    service_name="my-agent",
    send_to_logfire=False,
    # Traces are exported via OTLP to your collector
)
```

---

## Workflow Tracing

For tracing transactional workflows that are not LLM-specific, use `WorkflowTracer`. It provides automatic timing, step tracking, and OTEL integration for any multi-step process.

### Basic Usage

```python
from autonomize_observer.tracing import WorkflowTracer

with WorkflowTracer("process-order", order_id="123") as tracer:
    with tracer.step("validate") as step:
        validate_order()
        step.set("items_count", 5)

    with tracer.step("payment") as step:
        result = process_payment()
        step.set("amount", result.amount)
        step.set("provider", "stripe")

    with tracer.step("fulfillment"):
        send_to_warehouse()

    tracer.set("status", "completed")

# Access summary after completion
summary = tracer.get_summary()
print(f"Total duration: {summary['duration_ms']}ms")
print(f"Steps completed: {summary['step_count']}")
```

### Step-by-Step Timing

Each step is automatically timed:

```python
from autonomize_observer.tracing import WorkflowTracer

with WorkflowTracer("data-pipeline") as tracer:
    with tracer.step("extract") as step:
        data = extract_data()
        step.set("rows_extracted", len(data))

    with tracer.step("transform") as step:
        transformed = transform_data(data)
        step.set("rows_transformed", len(transformed))
        step.set("rows_filtered", len(data) - len(transformed))

    with tracer.step("load") as step:
        load_to_db(transformed)
        step.set("rows_loaded", len(transformed))

# Access individual step metrics
for step in tracer.steps:
    print(f"{step.name}: {step.duration_ms:.2f}ms")
```

### Convenience Function

For simpler usage, use the `trace_workflow` convenience function:

```python
from autonomize_observer.tracing import trace_workflow

with trace_workflow("my-task", task_id="123") as tracer:
    with tracer.step("step1"):
        do_step1()
    with tracer.step("step2"):
        do_step2()
```

### Chaining Attributes

Both workflows and steps support method chaining:

```python
with WorkflowTracer("order", order_id="123", customer="acme") as tracer:
    tracer.set("priority", "high").set("region", "us-west")

    with tracer.step("process") as step:
        step.set("result", "ok").set("items", 5).log("Processing complete")
```

### Error Handling

Exceptions in steps are captured but re-raised:

```python
from autonomize_observer.tracing import WorkflowTracer

try:
    with WorkflowTracer("order-workflow") as tracer:
        with tracer.step("validate"):
            validate()

        with tracer.step("payment"):
            raise PaymentError("Card declined")

except PaymentError:
    # The failed step's error is captured
    for step in tracer.steps:
        if step.error:
            print(f"Step {step.name} failed: {step.error}")
```

### OTEL Integration

WorkflowTracer automatically integrates with Logfire for OTEL tracing when available:

```python
from autonomize_observer.tracing import WorkflowTracer

# OTEL spans are created automatically when Logfire is configured
with WorkflowTracer("api-request", send_to_logfire=True) as tracer:
    with tracer.step("authenticate"):
        auth_user()

    with tracer.step("process"):
        process_request()

    with tracer.step("respond"):
        send_response()

# Traces are visible in your OTEL backend (Jaeger, Zipkin, etc.)
```

### Get Summary

Get a complete summary of the workflow execution:

```python
summary = tracer.get_summary()
# {
#     "name": "process-order",
#     "duration_ms": 150.5,
#     "step_count": 3,
#     "steps": [
#         {
#             "name": "validate",
#             "duration_ms": 20.1,
#             "error": None,
#             "attributes": {"valid": True}
#         },
#         {
#             "name": "payment",
#             "duration_ms": 100.2,
#             "error": None,
#             "attributes": {"amount": 99.99}
#         },
#         {
#             "name": "fulfillment",
#             "duration_ms": 30.2,
#             "error": None,
#             "attributes": {}
#         }
#     ],
#     "attributes": {"order_id": "123", "status": "completed"}
# }
```

### Real-World Examples

#### API Request Pipeline

```python
from autonomize_observer.tracing import WorkflowTracer

async def handle_request(request):
    with WorkflowTracer("api-request",
                        method=request.method,
                        path=request.path) as tracer:
        with tracer.step("auth") as step:
            user = await authenticate(request)
            step.set("user_id", user.id)

        with tracer.step("validate") as step:
            data = await validate_input(request)
            step.set("valid", True)

        with tracer.step("process") as step:
            result = await process_business_logic(data)
            step.set("result_size", len(result))

        with tracer.step("serialize"):
            response = serialize_response(result)

        tracer.set("status_code", 200)
        return response
```

#### Batch Processing

```python
from autonomize_observer.tracing import WorkflowTracer

def process_batch(items):
    with WorkflowTracer("batch-process", batch_size=len(items)) as tracer:
        with tracer.step("validate") as step:
            valid_items = [i for i in items if validate(i)]
            step.set("valid_count", len(valid_items))
            step.set("invalid_count", len(items) - len(valid_items))

        with tracer.step("transform") as step:
            transformed = [transform(i) for i in valid_items]
            step.set("transformed_count", len(transformed))

        with tracer.step("persist") as step:
            saved = save_all(transformed)
            step.set("saved_count", saved)

        tracer.set("success_rate", saved / len(items) * 100)
        return saved
```

---

## AI Studio Agent Tracing

For AI Studio (Langflow) integration, use the `AgentTracer` class which supports:
- Legacy streaming format to Kafka (`genesis-traces-streaming` topic)
- Optional dual export (Kafka + OTEL)
- Automatic token extraction and cost calculation

```python
from uuid import uuid4
from autonomize_observer.tracing import AgentTracer

# Create tracer
tracer = AgentTracer(
    trace_name="Customer Support Flow",
    trace_id=uuid4(),
    flow_id="flow-123",
    user_id="user-456",
    session_id="session-789",
    # Kafka streaming config
    kafka_bootstrap_servers="kafka:9092",
    kafka_topic="genesis-traces-streaming",
    kafka_username="user",
    kafka_password="pass",
    # Optional: Enable OTEL dual export
    enable_otel=True,
    otel_service_name="ai-studio-flow",
)

# Start trace
tracer.start_trace()

# Trace each component
tracer.add_trace(
    trace_id="comp-1",
    trace_name="QueryClassifier",
    trace_type="llm",
    inputs={"query": "How do I reset my password?"},
)

# End component (with token usage)
tracer.end_trace(
    trace_id="comp-1",
    trace_name="QueryClassifier",
    outputs={
        "classification": "account",
        "model": "gpt-4o",
        "input_tokens": 100,
        "output_tokens": 50,
    },
)

# End the trace
tracer.end(inputs={}, outputs={})
```

The AgentTracer automatically:
- Extracts token usage from various LLM output formats
- Calculates costs using genai-prices
- Sends streaming events to Kafka in real-time
- Optionally exports to OTEL for observability tools

### Using TracerFactory (Recommended)

For cleaner configuration, use `TracerFactory` with `KafkaConfig`:

```python
from uuid import uuid4
from autonomize_observer import ObserverConfig
from autonomize_observer.core.config import KafkaConfig
from autonomize_observer.tracing import TracerFactory

# Create shared configuration
config = ObserverConfig(
    service_name="ai-studio",
    kafka=KafkaConfig(
        bootstrap_servers="kafka:9092",
        trace_topic="genesis-traces-streaming",
        sasl_username="user",
        sasl_password="pass",
        security_protocol="SASL_SSL",
    ),
    kafka_enabled=True,
)

# Create factory (reuse across your application)
factory = TracerFactory(config)

# Create tracers with shared configuration
tracer = factory.create_agent_tracer(
    trace_id=uuid4(),
    flow_id="flow-123",
    trace_name="Customer Support Flow",
    user_id="user-456",
    session_id="session-789",
)

# Use the tracer
tracer.start_trace()
tracer.add_trace("comp-1", "QueryClassifier", "llm", {"query": "..."})
tracer.end_trace("comp-1", "QueryClassifier", {"classification": "account"})
tracer.end({}, {})
```

The factory pattern provides:
- **Centralized configuration**: Define Kafka settings once
- **Consistent OTEL setup**: Shared OTELManager across tracers
- **Easy testing**: Mock the factory for unit tests

---

## Error Handling

### Exception Hierarchy

```python
from autonomize_observer.core.exceptions import (
    ObserverError,        # Base exception
    ConfigurationError,   # Configuration issues
    AuditError,          # Audit logging failures
    ExporterError,       # Export failures
)
```

### Handling Errors

```python
from autonomize_observer import audit, ResourceType
from autonomize_observer.core.exceptions import AuditError, ExporterError

try:
    audit.log_create(
        resource_type=ResourceType.DOCUMENT,
        resource_id="doc-123",
    )
except ExporterError as e:
    # Kafka export failed, but event was created
    logger.warning(f"Audit export failed: {e}")
except AuditError as e:
    # Audit logging failed completely
    logger.error(f"Audit logging failed: {e}")
```

### Graceful Degradation

The SDK is designed for graceful degradation:

```python
from autonomize_observer import calculate_cost

# If genai-prices isn't available, returns zero costs
result = calculate_cost(
    provider="unknown-provider",
    model="unknown-model",
    input_tokens=100,
    output_tokens=50,
)

# result.total_cost will be 0.0 with a warning logged
```

---

## Best Practices

### 1. Initialize Early

```python
# In your application startup
from autonomize_observer import init

def create_app():
    init(service_name="my-service")
    # ... rest of app setup
```

### 2. Set Actor Context at Request Start

```python
# In middleware
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if token:
        set_actor_from_keycloak_token(token.replace("Bearer ", ""))

    try:
        response = await call_next(request)
    finally:
        set_actor_context(None)  # Clean up

    return response
```

### 3. Use Specific Resource Types

```python
# Good - specific
audit.log_read(resource_type=ResourceType.DOCUMENT, ...)

# Avoid - generic
audit.log_read(resource_type=ResourceType.FILE, ...)  # When it's actually a document
```

### 4. Include Meaningful Descriptions

```python
# Good
audit.log_delete(
    resource_type=ResourceType.USER,
    resource_id="user-123",
    description="User account deleted per GDPR request #456",
)

# Avoid
audit.log_delete(
    resource_type=ResourceType.USER,
    resource_id="user-123",
)
```

### 5. Log LLM Interactions for Compliance

```python
# Always log LLM calls when dealing with sensitive data
response = client.chat.completions.create(...)

audit.log_llm_interaction(
    model=response.model,
    provider="openai",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens,
    cost=calculate_cost(...).total_cost,
)
```

### 6. Handle Kafka Failures Gracefully

```python
from autonomize_observer import init, KafkaConfig

# Configure with retries
init(
    kafka_config=KafkaConfig(
        bootstrap_servers="kafka:9092",
        retries=3,
        retry_backoff_ms=100,
    ),
    kafka_enabled=True,
)

# Kafka failures are logged but don't crash your app
```

---

## Next Steps

- See [INTEGRATIONS.md](INTEGRATIONS.md) for FastAPI, Langflow, and other integrations
- Check [INSTALL.md](INSTALL.md) for deployment guides
- Review the [API Reference](README.md) for all available functions
