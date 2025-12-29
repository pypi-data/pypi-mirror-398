"""Example: Agent Tracing for AI Studio (Langflow).

This example demonstrates how to use AgentTracer for tracing
AI Studio flows with Kafka streaming and optional OTEL export.

Run with:
    python examples/agent_tracing.py
"""

import time
from uuid import uuid4

from autonomize_observer.tracing import AgentTracer


def example_basic_agent_tracing() -> None:
    """Example: Basic agent tracing without Kafka."""
    print("\n=== Basic Agent Tracing ===")

    # Create tracer (Kafka disabled - will trace locally)
    tracer = AgentTracer(
        trace_name="Customer Support Agent",
        trace_id=uuid4(),
        flow_id="flow-customer-support",
        user_id="user-123",
        session_id="session-456",
        # No Kafka config - local tracing only
    )

    # Start the main trace
    tracer.start_trace()
    print(f"Trace started: {tracer._trace_id}")

    # Trace a component (e.g., Query Classifier)
    tracer.add_trace(
        trace_id="comp-classifier",
        trace_name="QueryClassifier",
        trace_type="llm",
        inputs={"query": "How do I reset my password?"},
    )
    time.sleep(0.01)  # Simulate processing

    tracer.end_trace(
        trace_id="comp-classifier",
        trace_name="QueryClassifier",
        outputs={
            "classification": "account",
            "confidence": 0.95,
            "model": "gpt-4o-mini",
            "input_tokens": 50,
            "output_tokens": 10,
        },
    )
    print("  QueryClassifier completed")

    # Trace another component (e.g., Knowledge Retrieval)
    tracer.add_trace(
        trace_id="comp-retrieval",
        trace_name="KnowledgeRetrieval",
        trace_type="retriever",
        inputs={"query": "password reset", "category": "account"},
    )
    time.sleep(0.01)

    tracer.end_trace(
        trace_id="comp-retrieval",
        trace_name="KnowledgeRetrieval",
        outputs={
            "documents": ["doc1", "doc2", "doc3"],
            "relevance_scores": [0.95, 0.87, 0.82],
        },
    )
    print("  KnowledgeRetrieval completed")

    # Trace the main LLM response
    tracer.add_trace(
        trace_id="comp-response",
        trace_name="ResponseGenerator",
        trace_type="llm",
        inputs={"context": "...", "query": "How do I reset my password?"},
    )
    time.sleep(0.02)

    tracer.end_trace(
        trace_id="comp-response",
        trace_name="ResponseGenerator",
        outputs={
            "response": "To reset your password, please follow these steps...",
            "model": "gpt-4o",
            "input_tokens": 500,
            "output_tokens": 150,
        },
    )
    print("  ResponseGenerator completed")

    # End the main trace
    tracer.end(
        inputs={"query": "How do I reset my password?"},
        outputs={"response": "To reset your password..."},
    )
    print(f"Trace ended: {tracer._trace_id}")


def example_with_kafka() -> None:
    """Example: Agent tracing with Kafka streaming."""
    print("\n=== Agent Tracing with Kafka ===")
    print("(Kafka connection will fail if not running - that's expected)")

    try:
        tracer = AgentTracer(
            trace_name="Data Analysis Agent",
            trace_id=uuid4(),
            flow_id="flow-data-analysis",
            user_id="user-789",
            session_id="session-abc",
            # Kafka configuration
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="genesis-traces-streaming",
        )

        tracer.start_trace()
        print(f"Trace started with Kafka: {tracer._trace_id}")

        # Trace components
        tracer.add_trace(
            trace_id="comp-parser",
            trace_name="DataParser",
            trace_type="tool",
            inputs={"file": "sales_data.csv"},
        )
        time.sleep(0.01)

        tracer.end_trace(
            trace_id="comp-parser",
            trace_name="DataParser",
            outputs={"rows": 10000, "columns": 15},
        )

        tracer.add_trace(
            trace_id="comp-analyzer",
            trace_name="DataAnalyzer",
            trace_type="llm",
            inputs={"data_summary": "..."},
        )
        time.sleep(0.02)

        tracer.end_trace(
            trace_id="comp-analyzer",
            trace_name="DataAnalyzer",
            outputs={
                "insights": ["insight1", "insight2"],
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )

        tracer.end(
            inputs={"file": "sales_data.csv"},
            outputs={"insights": ["insight1", "insight2"]},
        )
        print("Trace would be sent to Kafka topic: genesis-traces-streaming")

    except Exception as e:
        print(f"Expected error (no Kafka): {e}")


def example_with_otel() -> None:
    """Example: Agent tracing with OTEL export."""
    print("\n=== Agent Tracing with OTEL ===")

    tracer = AgentTracer(
        trace_name="Code Review Agent",
        trace_id=uuid4(),
        flow_id="flow-code-review",
        user_id="user-dev",
        session_id="session-review",
        # OTEL configuration
        enable_otel=True,
        otel_service_name="code-review-agent",
        send_to_logfire=False,  # Keep traces local
    )

    tracer.start_trace()
    print(f"Trace started with OTEL: {tracer._trace_id}")

    # Trace components
    tracer.add_trace(
        trace_id="comp-diff",
        trace_name="DiffAnalyzer",
        trace_type="tool",
        inputs={"pr_number": 123},
    )
    time.sleep(0.01)

    tracer.end_trace(
        trace_id="comp-diff",
        trace_name="DiffAnalyzer",
        outputs={"files_changed": 5, "lines_added": 100, "lines_removed": 50},
    )

    tracer.add_trace(
        trace_id="comp-reviewer",
        trace_name="CodeReviewer",
        trace_type="llm",
        inputs={"diff": "..."},
    )
    time.sleep(0.02)

    tracer.end_trace(
        trace_id="comp-reviewer",
        trace_name="CodeReviewer",
        outputs={
            "review": "Code looks good with minor suggestions...",
            "issues": 2,
            "model": "claude-3-5-sonnet-20241022",
            "input_tokens": 2000,
            "output_tokens": 500,
        },
    )

    tracer.end(
        inputs={"pr_number": 123},
        outputs={"review": "...", "issues": 2},
    )
    print("OTEL spans created (visible in Logfire/Jaeger)")


def example_dual_export() -> None:
    """Example: Agent tracing with both Kafka and OTEL."""
    print("\n=== Dual Export (Kafka + OTEL) ===")
    print("(Kafka connection will fail if not running)")

    try:
        tracer = AgentTracer(
            trace_name="Healthcare Agent",
            trace_id=uuid4(),
            flow_id="flow-clinical",
            user_id="user-clinician",
            session_id="session-patient",
            # Kafka configuration
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="genesis-traces-streaming",
            # OTEL configuration
            enable_otel=True,
            otel_service_name="clinical-agent",
            send_to_logfire=False,
        )

        tracer.start_trace()

        tracer.add_trace(
            trace_id="comp-extractor",
            trace_name="ClinicalExtractor",
            trace_type="llm",
            inputs={"note": "Patient presents with..."},
        )
        time.sleep(0.01)

        tracer.end_trace(
            trace_id="comp-extractor",
            trace_name="ClinicalExtractor",
            outputs={
                "entities": ["diabetes", "hypertension"],
                "model": "gpt-4o",
                "input_tokens": 300,
                "output_tokens": 100,
            },
        )

        tracer.end(
            inputs={"note": "Patient presents with..."},
            outputs={"entities": ["diabetes", "hypertension"]},
        )

        print("Events sent to both Kafka and OTEL")

    except Exception as e:
        print(f"Expected error (no Kafka): {e}")


def example_error_handling() -> None:
    """Example: Agent tracing with error handling."""
    print("\n=== Error Handling ===")

    tracer = AgentTracer(
        trace_name="Error Demo Agent",
        trace_id=uuid4(),
        flow_id="flow-error-demo",
        user_id="user-test",
        session_id="session-test",
    )

    tracer.start_trace()

    # Component succeeds
    tracer.add_trace(
        trace_id="comp-1",
        trace_name="Component1",
        trace_type="tool",
        inputs={"data": "..."},
    )
    tracer.end_trace(
        trace_id="comp-1",
        trace_name="Component1",
        outputs={"result": "success"},
    )
    print("  Component1: success")

    # Component fails
    tracer.add_trace(
        trace_id="comp-2",
        trace_name="Component2",
        trace_type="llm",
        inputs={"data": "..."},
    )
    tracer.end_trace(
        trace_id="comp-2",
        trace_name="Component2",
        outputs={"error": "Rate limit exceeded"},
        error="Rate limit exceeded",
    )
    print("  Component2: failed (rate limit)")

    # End with error
    tracer.end(
        inputs={"data": "..."},
        outputs={"error": "Flow failed at Component2"},
        error="Rate limit exceeded",
    )
    print("Trace ended with error recorded")


if __name__ == "__main__":
    print("Autonomize Observer - Agent Tracing Examples")
    print("=" * 50)

    example_basic_agent_tracing()
    example_with_kafka()
    example_with_otel()
    example_dual_export()
    example_error_handling()

    print("\n" + "=" * 50)
    print("All examples completed!")
