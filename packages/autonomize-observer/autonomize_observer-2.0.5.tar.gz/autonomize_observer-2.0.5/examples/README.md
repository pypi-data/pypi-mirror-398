# Autonomize Observer Examples

This directory contains example scripts demonstrating key features of the Autonomize Observer SDK.

## Examples

### 1. Audit Logging (`audit_logging.py`)

Demonstrates compliance-focused audit logging with Keycloak JWT context:

- Basic CRUD operations (create, read, update, delete)
- Keycloak JWT integration for actor context
- LLM interaction logging
- Custom audit events
- System and service actors

```bash
python examples/audit_logging.py
```

### 2. Workflow Tracing (`workflow_tracing.py`)

Demonstrates step-based workflow tracing with timing:

- Basic workflow with step timing
- Kafka export for workflow events
- OTEL/Logfire integration
- Error handling in workflows
- Batch processing patterns

```bash
python examples/workflow_tracing.py
```

### 3. LLM Tracing (`llm_tracing.py`)

Demonstrates LLM tracing with automatic instrumentation:

- OpenAI chat completions
- Anthropic messages
- RAG pipeline tracing
- Multi-model routing
- Cost tracking

```bash
# Set API keys first
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key

python examples/llm_tracing.py
```

### 4. Agent Tracing (`agent_tracing.py`)

Demonstrates agent tracing for AI Studio (Langflow):

- Basic agent tracing
- Kafka streaming export
- OTEL export
- Dual export (Kafka + OTEL)
- Error handling

```bash
python examples/agent_tracing.py
```

## Requirements

All examples work without external dependencies, but for full functionality:

```bash
# For LLM examples
pip install openai anthropic

# For Kafka export (optional)
pip install kafka-python
```

## Running Examples

```bash
# From the project root
cd autonomize-observer

# Run any example
python examples/audit_logging.py
python examples/workflow_tracing.py
python examples/llm_tracing.py
python examples/agent_tracing.py
```

## Export Destinations

| Tracer | Kafka | OTEL/Logfire |
|--------|-------|--------------|
| AuditLogger | ✅ Direct | ❌ |
| WorkflowTracer | ✅ Direct | ✅ Via Logfire |
| AgentTracer | ✅ Streaming | ✅ Optional |
| LLM Tracing | Via OTEL Collector | ✅ Via Logfire |
