"""Example: LLM Tracing with Logfire.

This example demonstrates how to trace LLM calls using Logfire
with automatic instrumentation for OpenAI and Anthropic.

Note: Requires openai and/or anthropic packages to be installed.

Run with:
    OPENAI_API_KEY=your-key python examples/llm_tracing.py
"""

import os

import logfire

from autonomize_observer import calculate_cost

# Configure Logfire for tracing
logfire.configure(
    service_name="llm-example",
    send_to_logfire=False,  # Keep traces local
)

# Auto-instrument LLM clients
try:
    logfire.instrument_openai()
    print("OpenAI instrumentation enabled")
except Exception:
    print("OpenAI not available")

try:
    logfire.instrument_anthropic()
    print("Anthropic instrumentation enabled")
except Exception:
    print("Anthropic not available")


def example_openai_chat() -> None:
    """Example: Trace OpenAI chat completion."""
    print("\n=== OpenAI Chat Completion ===")

    try:
        from openai import OpenAI

        client = OpenAI()

        # This call is automatically traced by Logfire
        with logfire.span("customer-support-query", query_type="billing"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
                max_tokens=50,
            )

            # Calculate cost
            cost = calculate_cost(
                provider="openai",
                model="gpt-4o-mini",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

            logfire.info(
                "LLM response received",
                model=response.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost=cost.total_cost,
            )

            print(f"Response: {response.choices[0].message.content}")
            print(
                f"Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out"
            )
            print(f"Cost: ${cost.total_cost:.6f}")

    except Exception as e:
        print(f"OpenAI example skipped: {e}")


def example_anthropic_chat() -> None:
    """Example: Trace Anthropic chat completion."""
    print("\n=== Anthropic Chat Completion ===")

    try:
        from anthropic import Anthropic

        client = Anthropic()

        # This call is automatically traced by Logfire
        with logfire.span("code-review-request", review_type="security"):
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Say hello in one sentence."},
                ],
            )

            # Calculate cost
            cost = calculate_cost(
                provider="anthropic",
                model="claude-3-5-haiku-20241022",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            logfire.info(
                "Claude response received",
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cost=cost.total_cost,
            )

            print(f"Response: {response.content[0].text}")
            print(
                f"Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out"
            )
            print(f"Cost: ${cost.total_cost:.6f}")

    except Exception as e:
        print(f"Anthropic example skipped: {e}")


def example_rag_pipeline() -> None:
    """Example: Trace a RAG pipeline."""
    print("\n=== RAG Pipeline ===")

    with logfire.span("rag-query", query="What are the key findings?"):
        # Step 1: Retrieve documents
        with logfire.span("retrieve", _tags=["retrieval"]):
            # Simulate retrieval
            docs = ["Document 1 content...", "Document 2 content..."]
            logfire.info("Documents retrieved", count=len(docs))

        # Step 2: Generate response
        with logfire.span("generate", _tags=["llm"]):
            # Simulate LLM call
            response = "Based on the documents, the key findings are..."
            logfire.info(
                "Response generated",
                response_length=len(response),
                model="gpt-4o",
            )

        # Step 3: Post-process
        with logfire.span("postprocess"):
            final_response = response.strip()
            logfire.info("Response post-processed")

    print("RAG pipeline completed (check Logfire for traces)")


def example_multi_model_routing() -> None:
    """Example: Trace multi-model routing."""
    print("\n=== Multi-Model Routing ===")

    queries = [
        {"type": "simple", "text": "What is 2+2?"},
        {"type": "complex", "text": "Explain quantum computing"},
        {"type": "code", "text": "Write a Python function"},
    ]

    with logfire.span("multi-model-batch", query_count=len(queries)):
        for query in queries:
            # Route to appropriate model based on query type
            if query["type"] == "simple":
                model = "gpt-4o-mini"
            elif query["type"] == "code":
                model = "claude-3-5-sonnet-20241022"
            else:
                model = "gpt-4o"

            with logfire.span(
                f"query-{query['type']}",
                query_type=query["type"],
                selected_model=model,
            ):
                # Simulate model call
                logfire.info(
                    "Model selected",
                    model=model,
                    query_type=query["type"],
                )
                print(f"  {query['type']}: routed to {model}")

    print("Multi-model routing completed")


def example_cost_tracking() -> None:
    """Example: Track costs across multiple calls."""
    print("\n=== Cost Tracking ===")

    total_cost = 0.0
    calls = [
        ("openai", "gpt-4o", 1000, 500),
        ("openai", "gpt-4o-mini", 2000, 1000),
        ("anthropic", "claude-3-5-sonnet-20241022", 1500, 750),
        ("anthropic", "claude-3-5-haiku-20241022", 3000, 1500),
    ]

    with logfire.span("cost-analysis", call_count=len(calls)):
        for provider, model, input_tokens, output_tokens in calls:
            cost = calculate_cost(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            total_cost += cost.total_cost

            logfire.info(
                "Cost calculated",
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost.total_cost,
            )

            print(f"  {provider}/{model}: ${cost.total_cost:.6f}")

        logfire.info("Total cost calculated", total_cost=total_cost)

    print(f"Total cost: ${total_cost:.6f}")


if __name__ == "__main__":
    print("Autonomize Observer - LLM Tracing Examples")
    print("=" * 50)

    # Check for API keys
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nNote: Set OPENAI_API_KEY to run OpenAI examples")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Note: Set ANTHROPIC_API_KEY to run Anthropic examples")

    example_openai_chat()
    example_anthropic_chat()
    example_rag_pipeline()
    example_multi_model_routing()
    example_cost_tracking()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("View traces in Logfire dashboard or your OTEL backend")
