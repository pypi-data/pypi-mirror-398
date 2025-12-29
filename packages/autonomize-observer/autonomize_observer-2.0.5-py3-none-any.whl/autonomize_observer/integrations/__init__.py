"""Integrations for Langflow, FastAPI, and other frameworks.

These integrations leverage Logfire for tracing while adding
Autonomize-specific functionality like audit logging and Keycloak.
"""

from autonomize_observer.integrations.fastapi import (
    create_fastapi_middleware,
    setup_fastapi,
)
from autonomize_observer.integrations.langflow import (
    FlowContext,
    trace_component,
    trace_flow,
)

__all__ = [
    # FastAPI
    "create_fastapi_middleware",
    "setup_fastapi",
    # Langflow
    "FlowContext",
    "trace_flow",
    "trace_component",
]
