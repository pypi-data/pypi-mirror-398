# Installation Guide

This guide covers all installation options for the Autonomize Observer SDK.

## Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Optional**: Kafka cluster for event streaming

## Quick Install

### Using pip

```bash
pip install autonomize-observer
```

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager that we recommend for development:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to your project
uv add autonomize-observer
```

### Using Poetry

```bash
poetry add autonomize-observer
```

## Dependencies

The SDK has the following core dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `logfire` | >=4.0.0 | OTEL tracing and LLM instrumentation |
| `genai-prices` | >=0.0.40 | LLM cost calculation |
| `pydantic` | >=2.10.0 | Data validation and models |
| `pyjwt` | >=2.10.0 | JWT token parsing |
| `confluent-kafka` | >=2.10.0 | Kafka event streaming |

## Installation Options

### Minimal Install

For basic audit logging without Kafka:

```bash
pip install autonomize-observer
```

Then disable Kafka in your configuration:

```python
from autonomize_observer import init

init(
    service_name="my-service",
    kafka_enabled=False,
)
```

### Full Install with Kafka

For production use with Kafka event streaming:

```bash
pip install autonomize-observer
```

The `confluent-kafka` package requires `librdkafka`. Install it based on your OS:

**Ubuntu/Debian:**
```bash
sudo apt-get install librdkafka-dev
```

**macOS:**
```bash
brew install librdkafka
```

**CentOS/RHEL:**
```bash
sudo yum install librdkafka-devel
```

**Windows:**
The Python wheel includes the necessary binaries.

### Development Install

For contributing to the SDK:

```bash
# Clone the repository
git clone https://github.com/autonomize-ai/autonomize-observer.git
cd autonomize-observer

# Install with development dependencies
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Verification

Verify your installation:

```python
import autonomize_observer

# Check version
print(f"Version: {autonomize_observer.__version__}")

# Test basic functionality
from autonomize_observer import init, audit, ResourceType

init(service_name="test", kafka_enabled=False)

event = audit.log_create(
    resource_type=ResourceType.DOCUMENT,
    resource_id="test-doc",
)

print(f"Audit event created: {event.event_id}")
```

Expected output:
```
Version: 2.0.0
Audit event created: evt_...
```

## Configuration

### Environment Variables

Set these environment variables for production use:

```bash
# Service Identity
export SERVICE_NAME="my-service"
export SERVICE_VERSION="1.0.0"
export ENVIRONMENT="production"

# Kafka Configuration (if enabled)
export KAFKA_BOOTSTRAP_SERVERS="kafka:9092"
export KAFKA_AUDIT_TOPIC="audit-events"
export KAFKA_SECURITY_PROTOCOL="SASL_SSL"
export KAFKA_SASL_MECHANISM="PLAIN"
export KAFKA_SASL_USERNAME="your-username"
export KAFKA_SASL_PASSWORD="your-password"

# Optional: Logfire Cloud (default: disabled)
export LOGFIRE_SEND_TO_LOGFIRE="false"
```

### Programmatic Configuration

```python
from autonomize_observer import init, KafkaConfig

init(
    service_name="my-service",
    service_version="1.0.0",
    environment="production",
    send_to_logfire=False,
    kafka_config=KafkaConfig(
        bootstrap_servers="kafka:9092",
        audit_topic="audit-events",
        security_protocol="SASL_SSL",
        sasl_mechanism="PLAIN",
        sasl_username="your-username",
        sasl_password="your-password",
    ),
    kafka_enabled=True,
)
```

## Docker

### Dockerfile Example

```dockerfile
FROM python:3.12-slim

# Install librdkafka for Kafka support
RUN apt-get update && apt-get install -y librdkafka-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev

# Copy application
COPY . .

CMD ["python", "main.py"]
```

### Docker Compose with Kafka

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - SERVICE_NAME=my-service
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_AUDIT_TOPIC=audit-events
    depends_on:
      - kafka

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
```

## Kubernetes

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: observer-config
data:
  SERVICE_NAME: "my-service"
  KAFKA_BOOTSTRAP_SERVERS: "kafka.default.svc.cluster.local:9092"
  KAFKA_AUDIT_TOPIC: "audit-events"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: observer-secrets
type: Opaque
stringData:
  KAFKA_SASL_USERNAME: "your-username"
  KAFKA_SASL_PASSWORD: "your-password"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          image: my-app:latest
          envFrom:
            - configMapRef:
                name: observer-config
            - secretRef:
                name: observer-secrets
```

## Troubleshooting

### ImportError: librdkafka

If you see:
```
ImportError: librdkafka not found
```

Install the system library:
```bash
# Ubuntu/Debian
sudo apt-get install librdkafka-dev

# macOS
brew install librdkafka
```

### Kafka Connection Timeout

If Kafka connections time out:

1. Verify Kafka is accessible from your network
2. Check firewall rules
3. Verify bootstrap servers address
4. Check security protocol settings

```python
# Test Kafka connectivity
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'socket.timeout.ms': 5000,
})

try:
    producer.list_topics(timeout=5)
    print("Kafka connection successful!")
except Exception as e:
    print(f"Kafka connection failed: {e}")
```

### JWT Decode Errors

If you see JWT decode errors:

1. Verify the token format (should be `Bearer <token>`)
2. Check that the token is a valid JWT
3. Ensure claim mappings match your Keycloak configuration

```python
import jwt

token = "your.jwt.token"
try:
    payload = jwt.decode(token, options={"verify_signature": False})
    print(f"Token payload: {payload}")
except jwt.exceptions.DecodeError as e:
    print(f"Invalid token: {e}")
```

## Next Steps

- Read the [Usage Guide](GUIDE.md) for detailed examples
- See [Integrations](INTEGRATIONS.md) for FastAPI, Langflow, etc.
- Check the [API Reference](README.md) for all available functions
