"""Example: Workflow Tracing with OTEL and Kafka.

This example demonstrates how to use WorkflowTracer for step-based
workflow tracing with automatic timing, OTEL integration, and Kafka export.

Run with:
    python examples/workflow_tracing.py
"""

import time

from autonomize_observer.tracing import WorkflowTracer, trace_workflow


def example_basic_workflow() -> None:
    """Example: Basic workflow with step timing."""
    print("\n=== Basic Workflow ===")

    with WorkflowTracer("order-processing", order_id="ORD-12345") as tracer:
        # Step 1: Validate order
        with tracer.step("validate") as step:
            time.sleep(0.01)  # Simulate work
            step.set("items_count", 5)
            step.set("total_amount", 149.99)
            step.log("Order validated successfully")

        # Step 2: Process payment
        with tracer.step("payment") as step:
            time.sleep(0.02)  # Simulate payment processing
            step.set("payment_method", "credit_card")
            step.set("transaction_id", "TXN-789")
            step.set("amount_charged", 149.99)

        # Step 3: Fulfill order
        with tracer.step("fulfillment") as step:
            time.sleep(0.01)  # Simulate fulfillment
            step.set("warehouse", "WH-EAST")
            step.set("shipping_method", "express")

        # Set workflow-level attributes
        tracer.set("status", "completed")
        tracer.set("customer_id", "CUST-456")

    # Access timing information
    print(f"Workflow completed in {tracer.duration_ms:.2f}ms")
    for step in tracer.steps:
        print(f"  - {step.name}: {step.duration_ms:.2f}ms")

    # Get full summary
    summary = tracer.get_summary()
    print(
        f"Summary: {summary['step_count']} steps, status={summary['attributes']['status']}"
    )


def example_with_kafka() -> None:
    """Example: Workflow with Kafka export."""
    print("\n=== Workflow with Kafka Export ===")
    print("(Kafka connection will fail if not running - that's expected)")

    try:
        with WorkflowTracer(
            "data-pipeline",
            # Kafka configuration
            kafka_bootstrap_servers="localhost:9092",
            kafka_topic="workflow-traces",
            # Workflow attributes
            pipeline_id="ETL-001",
            source="postgres",
            target="warehouse",
        ) as tracer:
            with tracer.step("extract") as step:
                time.sleep(0.01)
                step.set("rows_extracted", 10000)
                step.set("source_table", "customers")

            with tracer.step("transform") as step:
                time.sleep(0.02)
                step.set("rows_transformed", 9500)
                step.set("rows_filtered", 500)

            with tracer.step("load") as step:
                time.sleep(0.01)
                step.set("rows_loaded", 9500)
                step.set("target_table", "dim_customers")

            tracer.set("success", True)

        print(f"Pipeline completed: {tracer.duration_ms:.2f}ms")
        print("Events would be sent to Kafka topic: workflow-traces")

    except Exception as e:
        print(f"Expected error (no Kafka): {e}")


def example_with_otel() -> None:
    """Example: Workflow with OTEL/Logfire tracing."""
    print("\n=== Workflow with OTEL ===")

    with WorkflowTracer(
        "api-request",
        service_name="my-api-service",
        send_to_logfire=False,  # Keep traces local
        # Request attributes
        method="POST",
        path="/api/v1/orders",
        user_id="user-123",
    ) as tracer:
        with tracer.step("authenticate") as step:
            time.sleep(0.005)
            step.set("auth_method", "jwt")
            step.set("user_verified", True)

        with tracer.step("validate_input") as step:
            time.sleep(0.005)
            step.set("schema", "order_create")
            step.set("valid", True)

        with tracer.step("process") as step:
            time.sleep(0.01)
            step.set("order_id", "ORD-NEW-123")

        with tracer.step("respond") as step:
            time.sleep(0.002)
            step.set("status_code", 201)

        tracer.set("response_time_ms", tracer.duration_ms)

    print(f"API request processed in {tracer.duration_ms:.2f}ms")
    print("OTEL spans created (visible in Logfire/Jaeger/etc.)")


def example_error_handling() -> None:
    """Example: Workflow with error handling."""
    print("\n=== Error Handling ===")

    try:
        with WorkflowTracer("payment-flow", payment_id="PAY-999") as tracer:
            with tracer.step("validate") as step:
                time.sleep(0.005)
                step.set("card_valid", True)

            with tracer.step("charge") as step:
                time.sleep(0.01)
                # Simulate payment failure
                raise ValueError("Insufficient funds")

    except ValueError as e:
        print(f"Payment failed: {e}")
        # Check which step failed
        for step in tracer.steps:
            if step.error:
                print(f"  Failed step: {step.name}")
                print(f"  Error: {step.error}")
                print(f"  Duration before error: {step.duration_ms:.2f}ms")


def example_convenience_function() -> None:
    """Example: Using the trace_workflow convenience function."""
    print("\n=== Convenience Function ===")

    with trace_workflow("quick-task", task_id="T-123") as tracer:
        with tracer.step("step1"):
            time.sleep(0.005)
        with tracer.step("step2"):
            time.sleep(0.005)
        tracer.set("result", "success")

    print(f"Quick task: {len(tracer.steps)} steps in {tracer.duration_ms:.2f}ms")


def example_batch_processing() -> None:
    """Example: Batch processing workflow."""
    print("\n=== Batch Processing ===")

    items = ["item1", "item2", "item3", "item4", "item5"]

    with WorkflowTracer("batch-process", batch_size=len(items)) as tracer:
        with tracer.step("validate") as step:
            valid_items = [i for i in items if not i.startswith("skip")]
            step.set("valid_count", len(valid_items))
            step.set("invalid_count", len(items) - len(valid_items))

        with tracer.step("process") as step:
            processed = []
            for item in valid_items:
                time.sleep(0.002)  # Process each item
                processed.append(f"processed_{item}")
            step.set("processed_count", len(processed))

        with tracer.step("save") as step:
            time.sleep(0.01)  # Bulk save
            step.set("saved_count", len(processed))

        success_rate = len(processed) / len(items) * 100
        tracer.set("success_rate", success_rate)

    print(
        f"Batch completed: {tracer.get_summary()['attributes']['success_rate']:.1f}% success"
    )


if __name__ == "__main__":
    print("Autonomize Observer - Workflow Tracing Examples")
    print("=" * 50)

    example_basic_workflow()
    example_with_kafka()
    example_with_otel()
    example_error_handling()
    example_convenience_function()
    example_batch_processing()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")
