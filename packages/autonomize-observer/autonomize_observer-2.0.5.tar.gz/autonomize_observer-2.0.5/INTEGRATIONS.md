# Integration Guides

This guide covers integrating Autonomize Observer with popular frameworks and tools.

## Table of Contents

1. [FastAPI Integration](#fastapi-integration)
2. [Langflow Integration](#langflow-integration)
3. [Logfire Integration](#logfire-integration)
4. [Standalone Agent Tracing](#standalone-agent-tracing)
5. [AI Studio Agent Tracing](#ai-studio-agent-tracing)
6. [OTEL Collector Integration](#otel-collector-integration)
7. [Flask Integration](#flask-integration)
8. [Django Integration](#django-integration)
9. [Database Instrumentation](#database-instrumentation)

---

## FastAPI Integration

The SDK provides first-class support for FastAPI with automatic JWT extraction and Logfire instrumentation.

### Quick Setup

```python
from fastapi import FastAPI
from autonomize_observer.integrations import setup_fastapi

app = FastAPI()

# One-line setup
setup_fastapi(
    app,
    service_name="my-api",
    keycloak_enabled=True,
)
```

This automatically:
- Configures Logfire for request tracing
- Instruments FastAPI with Logfire
- Adds middleware for Keycloak JWT extraction
- Sets actor context for audit logging

### Manual Setup

For more control over the setup:

```python
from fastapi import FastAPI
import logfire
from autonomize_observer import init
from autonomize_observer.integrations.fastapi import create_fastapi_middleware

app = FastAPI()

# Initialize Observer
init(service_name="my-api", kafka_enabled=False)

# Configure Logfire manually
logfire.configure(
    service_name="my-api",
    send_to_logfire=False,
)
logfire.instrument_fastapi(app)

# Add Keycloak middleware
middleware = create_fastapi_middleware(
    keycloak_claim_mappings={
        "actor_id": "sub",
        "email": "email",
        "roles": "realm_access.roles",
    }
)

@app.middleware("http")
async def keycloak_middleware(request, call_next):
    return await middleware(request, call_next)
```

### Custom Claim Mappings

If your Keycloak token uses non-standard claims:

```python
setup_fastapi(
    app,
    service_name="my-api",
    keycloak_enabled=True,
    keycloak_claim_mappings={
        "actor_id": "user_id",         # Default: "sub"
        "email": "user_email",          # Default: "email"
        "name": "full_name",            # Default: "name"
        "roles": "permissions",         # Default: "realm_access.roles"
        "groups": "team_memberships",   # Default: "groups"
    },
)
```

### Getting Actor in Route Handlers

```python
from fastapi import Request, HTTPException
from autonomize_observer import audit, ResourceType
from autonomize_observer.integrations.fastapi import get_request_actor

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, request: Request):
    # Get actor from request context
    actor = get_request_actor(request)

    if not actor:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Audit logging automatically includes actor context
    audit.log_read(
        resource_type=ResourceType.DOCUMENT,
        resource_id=doc_id,
        description=f"Document accessed by {actor.email}",
    )

    return {"id": doc_id, "content": "..."}
```

### Lifespan Events

For proper initialization and cleanup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from autonomize_observer import init
from autonomize_observer.integrations import setup_fastapi

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init(service_name="my-api", kafka_enabled=True)
    yield
    # Shutdown handled automatically

app = FastAPI(lifespan=lifespan)
setup_fastapi(app, service_name="my-api")
```

---

## Langflow Integration

First-class support for tracing Langflow flows and components.

### Using Decorators

```python
from autonomize_observer.integrations import trace_flow, trace_component

@trace_flow(
    flow_id="customer-support-flow",
    flow_name="Customer Support Bot",
    session_id="session-123",
    user_id="user-456",
)
def run_customer_support(query: str) -> str:
    """Main flow function."""

    # Step 1: Analyze the query
    analysis = analyze_query(query)

    # Step 2: Generate response
    response = generate_response(analysis)

    return response


@trace_component("LLMComponent", "Query Analyzer")
def analyze_query(query: str) -> dict:
    """Analyze customer query to understand intent."""
    # Component execution is automatically traced
    return {"intent": "billing", "entities": ["invoice"]}


@trace_component("LLMComponent", "Response Generator")
def generate_response(analysis: dict) -> str:
    """Generate response based on analysis."""
    # This is a child span under the flow
    return "Here's your billing information..."


# Run the flow
result = run_customer_support("What's my invoice status?")
```

### Using Context Managers

For more complex flows:

```python
from autonomize_observer.integrations.langflow import FlowTracer

tracer = FlowTracer()

def process_document(doc_id: str) -> dict:
    with tracer.flow(
        flow_id="doc-processing",
        flow_name="Document Processor",
        session_id="session-789",
    ) as flow:

        # Extract text
        with flow.component("TextExtractor", "PDF Extractor") as comp:
            text = extract_pdf(doc_id)
            comp.set_result(f"Extracted {len(text)} characters")

        # Analyze with LLM
        with flow.component("LLMComponent", "Content Analyzer") as comp:
            analysis = analyze_with_llm(text)
            comp.set_result(analysis)
            comp.set_attribute("model", "gpt-4o")
            comp.set_attribute("tokens", 1500)

        # Store results
        with flow.component("DatabaseComponent", "Result Store") as comp:
            store_results(doc_id, analysis)
            comp.set_result("Stored successfully")

        return analysis
```

### Flow Context

Access flow context within components:

```python
from autonomize_observer.integrations.langflow import (
    get_flow_context,
    set_flow_context,
    FlowContext,
)

def my_component():
    # Get current flow context
    ctx = get_flow_context()

    if ctx:
        print(f"Running in flow: {ctx.flow_name}")
        print(f"Flow ID: {ctx.flow_id}")
        print(f"Session: {ctx.session_id}")
        print(f"Component count: {ctx.component_count}")
```

### Async Support

The decorators work with async functions too:

```python
@trace_flow(
    flow_id="async-flow",
    flow_name="Async Data Pipeline",
)
async def async_pipeline(data: list) -> list:
    results = []
    for item in data:
        result = await process_item(item)
        results.append(result)
    return results


@trace_component("AsyncProcessor", "Item Processor")
async def process_item(item: dict) -> dict:
    # Async component execution
    await asyncio.sleep(0.1)
    return {"processed": item}
```

### Langflow-Specific Attributes

All spans include these attributes:

| Attribute | Description |
|-----------|-------------|
| `langflow.flow.id` | Unique flow identifier |
| `langflow.flow.name` | Human-readable flow name |
| `langflow.flow.status` | "success" or "error" |
| `langflow.flow.component_count` | Number of components executed |
| `langflow.session.id` | Session identifier (optional) |
| `langflow.user.id` | User identifier (optional) |
| `langflow.project.name` | Project name (optional) |
| `langflow.component.type` | Component type |
| `langflow.component.name` | Component name |
| `langflow.component.index` | Component execution order |
| `langflow.component.status` | "success" or "error" |

---

## Logfire Integration

We provide a thin wrapper around Logfire for convenience. For advanced usage, use Logfire directly.

### Using Our Wrapper

```python
from autonomize_observer.tracing import (
    configure_logfire,
    get_logfire,
    instrument_llms,
    instrument_web_framework,
    instrument_database,
)

# Configure Logfire
configure_logfire(
    service_name="my-service",
    service_version="1.0.0",
    environment="production",
    send_to_logfire=False,  # Keep data local
)

# Instrument LLMs
instrument_llms(
    openai=True,
    anthropic=True,
    openai_options={"capture_messages": True},
)

# Instrument web framework
from fastapi import FastAPI
app = FastAPI()
instrument_web_framework("fastapi", app=app)

# Instrument database
instrument_database("sqlalchemy", engine=engine)
```

### Using Logfire Directly

For full control:

```python
import logfire
from openai import OpenAI
from anthropic import Anthropic

# Configure
logfire.configure(
    service_name="my-service",
    send_to_logfire=False,
)

# Instrument OpenAI
logfire.instrument_openai()

# Instrument Anthropic
logfire.instrument_anthropic()

# Use normally - all calls are traced
openai_client = OpenAI()
anthropic_client = Anthropic()

# Custom spans
with logfire.span("process-request", request_id="req-123"):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    logfire.info("LLM response received", tokens=response.usage.total_tokens)
```

### Supported Instrumentations

| Framework/Library | Method |
|-------------------|--------|
| OpenAI | `logfire.instrument_openai()` |
| Anthropic | `logfire.instrument_anthropic()` |
| FastAPI | `logfire.instrument_fastapi(app)` |
| Flask | `logfire.instrument_flask(app)` |
| Django | `logfire.instrument_django()` |
| Starlette | `logfire.instrument_starlette(app)` |
| SQLAlchemy | `logfire.instrument_sqlalchemy(engine)` |
| psycopg | `logfire.instrument_psycopg()` |
| asyncpg | `logfire.instrument_asyncpg()` |
| pymongo | `logfire.instrument_pymongo()` |
| Redis | `logfire.instrument_redis()` |
| httpx | `logfire.instrument_httpx()` |
| requests | `logfire.instrument_requests()` |

See [Logfire documentation](https://logfire.pydantic.dev/docs/integrations/) for the full list.

---

## Standalone Agent Tracing

For tracing custom agents or LLM workflows outside of AI Studio, use Logfire directly.

### Basic Setup

```python
import logfire
from openai import OpenAI
from anthropic import Anthropic
from autonomize_observer import calculate_cost

# Configure Logfire (one-time)
logfire.configure(
    service_name="my-agent",
    send_to_logfire=False,  # Keep data local
)

# Auto-instrument LLM clients
logfire.instrument_openai()
logfire.instrument_anthropic()

# All LLM calls are now automatically traced with tokens/cost
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Custom Agent with Manual Spans

```python
import logfire
from openai import OpenAI
from autonomize_observer import calculate_cost

logfire.configure(service_name="custom-agent")
logfire.instrument_openai()

client = OpenAI()


def analyze_query(query: str) -> dict:
    """Analyze user query with LLM."""
    with logfire.span("analyze-query", query=query, _tags=["agent"]):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Classify: {query}"}],
        )

        # Log cost
        cost = calculate_cost(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
        logfire.info("Analysis complete", cost=cost.total_cost)

        return {"classification": response.choices[0].message.content}


def generate_response(analysis: dict, query: str) -> str:
    """Generate response based on analysis."""
    with logfire.span("generate-response", _tags=["agent"]):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Classification: {analysis}"},
                {"role": "user", "content": query},
            ],
        )
        return response.choices[0].message.content


def agent_workflow(query: str) -> str:
    """Complete agent workflow."""
    with logfire.span("agent-workflow", query=query, _tags=["workflow"]):
        analysis = analyze_query(query)
        response = generate_response(analysis, query)
        logfire.info("Workflow complete")
        return response
```

### Multi-Provider Agent

```python
import logfire
from openai import OpenAI
from anthropic import Anthropic

logfire.configure(service_name="multi-provider-agent")
logfire.instrument_openai()
logfire.instrument_anthropic()

openai_client = OpenAI()
anthropic_client = Anthropic()


async def research_with_gpt(topic: str) -> str:
    """Research phase using GPT-4o."""
    with logfire.span("research", provider="openai", topic=topic):
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Research: {topic}"}],
        )
        return response.choices[0].message.content


async def analyze_with_claude(research: str) -> str:
    """Analysis phase using Claude."""
    with logfire.span("analyze", provider="anthropic"):
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"Analyze: {research}"}],
        )
        return response.content[0].text


async def multi_provider_agent(topic: str) -> str:
    """Agent using multiple LLM providers."""
    with logfire.span("multi-provider-agent", topic=topic):
        research = await research_with_gpt(topic)
        analysis = await analyze_with_claude(research)
        return analysis
```

---

## AI Studio Agent Tracing

For AI Studio (Langflow) integration, use the `AgentTracer` class. It supports:

- **Legacy streaming format**: Real-time events to Kafka (`genesis-traces-streaming`)
- **Dual export**: Optional OTEL tracing alongside Kafka streaming
- **Automatic token extraction**: From OpenAI, LangChain, Anthropic output formats
- **Cost calculation**: Using genai-prices library

### Basic Usage

```python
from uuid import uuid4
from autonomize_observer.tracing import AgentTracer

tracer = AgentTracer(
    trace_name="Customer Support Flow",
    trace_id=uuid4(),
    flow_id="flow-123",
    user_id="user-456",
    session_id="session-789",
    kafka_bootstrap_servers="kafka:9092",
    kafka_topic="genesis-traces-streaming",
)

tracer.start_trace()

# Trace component execution
tracer.add_trace(
    trace_id="comp-1",
    trace_name="QueryClassifier",
    trace_type="llm",
    inputs={"query": "How do I reset my password?"},
)

# End with outputs (tokens extracted automatically)
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

tracer.end(inputs={}, outputs={})
```

### With Dual Export (Kafka + OTEL)

```python
from uuid import uuid4
from autonomize_observer.tracing import AgentTracer

tracer = AgentTracer(
    trace_name="RAG Pipeline",
    trace_id=uuid4(),
    flow_id="rag-flow",
    kafka_bootstrap_servers="kafka:9092",
    # Enable OTEL for observability tools
    enable_otel=True,
    otel_service_name="ai-studio-rag",
    send_to_logfire=False,  # Keep local
)
```

### With SASL Authentication

```python
tracer = AgentTracer(
    trace_name="Secure Flow",
    trace_id=uuid4(),
    flow_id="secure-flow",
    kafka_bootstrap_servers="kafka.example.com:9092",
    kafka_username="your-username",
    kafka_password="your-password",
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
)
```

### Token Extraction Formats

The `AgentTracer` automatically extracts tokens from various output formats:

```python
# OpenAI format
outputs = {
    "model": "gpt-4o",
    "input_tokens": 100,
    "output_tokens": 50,
}

# Alternative OpenAI format
outputs = {
    "model": "gpt-4o",
    "prompt_tokens": 100,
    "completion_tokens": 50,
}

# LangChain format
outputs = {
    "response_metadata": {
        "token_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        },
        "model_name": "gpt-4o",
    }
}

# LangChain llm_output format
outputs = {
    "llm_output": {
        "token_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
        },
        "model_name": "gpt-4o",
    }
}
```

---

## OTEL Collector Integration

For advanced setups, export traces to Kafka via an OpenTelemetry Collector.

### Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  # Export to Kafka
  kafka:
    brokers:
      - kafka:9092
    topic: genesis-otel
    encoding: otlp_json

  # Also export to Jaeger for visualization
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [kafka, otlp/jaeger]
```

### Docker Compose Setup

```yaml
version: '3.8'
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml
    command: ["--config=/etc/otel/config.yaml"]
    ports:
      - "4317:4317"  # gRPC
      - "4318:4318"  # HTTP

  kafka:
    image: confluentinc/cp-kafka:latest
    # ... kafka config

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
```

### Application Configuration

```python
import logfire
import os

# Configure Logfire to send to OTEL collector
logfire.configure(
    service_name="my-agent",
    send_to_logfire=False,
)

# Set OTEL endpoint (Logfire uses OTLP under the hood)
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://otel-collector:4317"
```

---

## Flask Integration

```python
from flask import Flask, g, request
import logfire
from autonomize_observer import init, audit, ResourceType
from autonomize_observer.audit.context import ActorContext, set_actor_context

app = Flask(__name__)

# Initialize
init(service_name="flask-app", kafka_enabled=False)

# Configure Logfire
logfire.configure(service_name="flask-app", send_to_logfire=False)
logfire.instrument_flask(app)


@app.before_request
def extract_user_context():
    """Extract user context from JWT."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            actor = ActorContext.from_jwt(token, verify=False)
            actor.ip_address = request.remote_addr
            actor.user_agent = request.user_agent.string
            set_actor_context(actor)
            g.actor = actor
        except Exception:
            pass


@app.after_request
def clear_user_context(response):
    """Clear user context after request."""
    set_actor_context(None)
    return response


@app.route("/documents/<doc_id>")
def get_document(doc_id):
    actor = getattr(g, "actor", None)

    audit.log_read(
        resource_type=ResourceType.DOCUMENT,
        resource_id=doc_id,
    )

    return {"id": doc_id, "accessed_by": actor.email if actor else "anonymous"}
```

---

## Django Integration

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "autonomize_observer.django",  # If we add Django support
]

AUTONOMIZE_OBSERVER = {
    "service_name": "django-app",
    "kafka_enabled": True,
    "kafka_config": {
        "bootstrap_servers": "kafka:9092",
        "audit_topic": "audit-events",
    },
}

# For now, manual setup in wsgi.py or asgi.py:
import logfire
from autonomize_observer import init

init(service_name="django-app", kafka_enabled=False)
logfire.configure(service_name="django-app", send_to_logfire=False)
logfire.instrument_django()
```

### Django Middleware

```python
# middleware.py
from autonomize_observer.audit.context import ActorContext, set_actor_context


class KeycloakMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract JWT
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                actor = ActorContext.from_jwt(token, verify=False)
                actor.ip_address = self._get_client_ip(request)
                set_actor_context(actor)
                request.actor = actor
            except Exception:
                pass

        response = self.get_response(request)

        set_actor_context(None)
        return response

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


# settings.py
MIDDLEWARE = [
    # ...
    "myapp.middleware.KeycloakMiddleware",
]
```

---

## Database Instrumentation

### SQLAlchemy

```python
from sqlalchemy import create_engine
import logfire

engine = create_engine("postgresql://user:pass@localhost/db")

# Instrument SQLAlchemy
logfire.instrument_sqlalchemy(engine=engine)

# All database queries are now traced
```

### Async Databases

```python
import logfire

# asyncpg
logfire.instrument_asyncpg()

# psycopg (async mode)
logfire.instrument_psycopg()

# Your async database code is now traced
```

### MongoDB

```python
import logfire
from pymongo import MongoClient

logfire.instrument_pymongo()

client = MongoClient("mongodb://localhost:27017")
# All MongoDB operations are traced
```

### Redis

```python
import logfire
import redis

logfire.instrument_redis()

r = redis.Redis(host="localhost", port=6379)
# All Redis operations are traced
```

---

## Complete Example: FastAPI with Full Instrumentation

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
import logfire
from openai import OpenAI

from autonomize_observer import (
    init,
    audit,
    calculate_cost,
    KafkaConfig,
    ResourceType,
)
from autonomize_observer.integrations import setup_fastapi
from autonomize_observer.integrations.fastapi import get_request_actor
from autonomize_observer.integrations.langflow import trace_flow, trace_component


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Observer with Kafka
    init(
        service_name="full-example-api",
        kafka_config=KafkaConfig(
            bootstrap_servers="kafka:9092",
            audit_topic="audit-events",
        ),
        kafka_enabled=True,
    )
    yield


app = FastAPI(lifespan=lifespan)

# Setup FastAPI with Keycloak
setup_fastapi(
    app,
    service_name="full-example-api",
    keycloak_enabled=True,
)

# Instrument OpenAI
logfire.instrument_openai()
client = OpenAI()


@trace_flow(flow_id="chat-flow", flow_name="Chat Handler")
def handle_chat(user_message: str, user_id: str) -> str:
    """Handle a chat message using LLM."""

    @trace_component("LLMComponent", "GPT-4 Responder")
    def generate_response():
        return client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}],
        )

    response = generate_response()

    # Calculate and log cost
    cost_result = calculate_cost(
        provider="openai",
        model="gpt-4o",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )

    # Log LLM interaction for compliance
    audit.log_llm_interaction(
        flow_id="chat-flow",
        model="gpt-4o",
        provider="openai",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        cost=cost_result.total_cost,
    )

    return response.choices[0].message.content


@app.post("/chat")
async def chat(request: Request, message: str):
    actor = get_request_actor(request)
    if not actor:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Log data access
    audit.log_read(
        resource_type=ResourceType.CONVERSATION,
        resource_id=f"chat-{actor.actor_id}",
        description="User started chat session",
    )

    response = handle_chat(message, actor.actor_id)

    return {"response": response}


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, request: Request):
    actor = get_request_actor(request)

    audit.log_read(
        resource_type=ResourceType.DOCUMENT,
        resource_id=doc_id,
    )

    return {"id": doc_id, "content": "Document content here..."}
```

---

## Next Steps

- See [GUIDE.md](GUIDE.md) for detailed usage guide
- Check [INSTALL.md](INSTALL.md) for installation options
- Review [README.md](README.md) for API reference
