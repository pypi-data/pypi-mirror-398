"""FastAPI integration with Keycloak JWT authentication.

Leverages Logfire for request tracing, adding Keycloak user
context extraction for audit logging.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from autonomize_observer.audit.context import ActorContext, set_actor_context

logger = logging.getLogger(__name__)


def setup_fastapi(
    app: Any,
    service_name: str = "autonomize-service",
    keycloak_enabled: bool = True,
    keycloak_claim_mappings: dict[str, str] | None = None,
    instrument_with_logfire: bool = True,
) -> None:
    """Set up FastAPI with Logfire instrumentation and Keycloak middleware.

    This function:
    1. Configures Logfire for the app (if not already configured)
    2. Instruments FastAPI with Logfire
    3. Adds middleware for Keycloak JWT extraction

    Args:
        app: FastAPI application instance
        service_name: Name of the service
        keycloak_enabled: Whether to extract user context from Keycloak JWT
        keycloak_claim_mappings: Custom claim mappings for Keycloak tokens
        instrument_with_logfire: Whether to instrument with Logfire

    Example:
        from fastapi import FastAPI
        from autonomize_observer.integrations import setup_fastapi

        app = FastAPI()
        setup_fastapi(
            app,
            service_name="my-service",
            keycloak_enabled=True,
        )
    """
    # Instrument with Logfire
    if instrument_with_logfire:
        try:
            import logfire

            logfire.configure(
                service_name=service_name,
                send_to_logfire=False,
            )
            logfire.instrument_fastapi(app)
            logger.info("FastAPI instrumented with Logfire")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI with Logfire: {e}")

    # Add Keycloak middleware
    if keycloak_enabled:
        middleware = create_fastapi_middleware(
            keycloak_claim_mappings=keycloak_claim_mappings
        )
        app.middleware("http")(middleware)
        logger.info("Keycloak middleware added to FastAPI")


def create_fastapi_middleware(
    keycloak_claim_mappings: dict[str, str] | None = None,
    header_name: str = "Authorization",
    header_prefix: str = "Bearer ",
) -> Callable:
    """Create FastAPI middleware for Keycloak JWT extraction.

    Extracts user context from JWT tokens in the Authorization header
    and sets it in the actor context for audit logging.

    Args:
        keycloak_claim_mappings: Custom claim mappings
        header_name: Name of the header containing the token
        header_prefix: Prefix before the token (e.g., "Bearer ")

    Returns:
        ASGI middleware function

    Example:
        from fastapi import FastAPI
        from autonomize_observer.integrations import create_fastapi_middleware

        app = FastAPI()

        @app.middleware("http")
        async def keycloak_middleware(request, call_next):
            middleware = create_fastapi_middleware()
            return await middleware(request, call_next)
    """

    async def middleware(request: Any, call_next: Callable) -> Any:
        # Try to extract JWT from header
        auth_header = request.headers.get(header_name)

        if auth_header and auth_header.startswith(header_prefix):
            token = auth_header[len(header_prefix) :]

            try:
                # Decode without verification - verification should be
                # done by the API gateway or a separate auth middleware
                actor = ActorContext.from_jwt(
                    token,
                    verify=False,  # Verification done elsewhere
                    claim_mappings=keycloak_claim_mappings,
                )

                # Add request context
                actor.ip_address = _get_client_ip(request)
                actor.user_agent = request.headers.get("User-Agent")

                # Set actor context for audit logging
                set_actor_context(actor)

                # Add to Logfire span if available
                try:
                    import logfire

                    logfire.info(
                        "User authenticated",
                        actor_id=actor.actor_id,
                        email=actor.email,
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.debug(f"Failed to extract actor from JWT: {e}")
                # Don't fail the request, just continue without actor context

        try:
            response = await call_next(request)
        finally:
            # Clear actor context after request
            set_actor_context(None)

        return response

    return middleware


def _get_client_ip(request: Any) -> str | None:
    """Extract client IP from request, handling proxies."""
    # Check common proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get first IP in chain (original client)
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    if hasattr(request, "client") and request.client:
        return request.client.host

    return None


def get_request_actor(request: Any) -> ActorContext | None:
    """Get actor context from a FastAPI request.

    Useful for getting user info in route handlers.

    Args:
        request: FastAPI Request object

    Returns:
        ActorContext if available, None otherwise

    Example:
        from fastapi import Request
        from autonomize_observer.integrations.fastapi import get_request_actor

        @app.get("/profile")
        async def get_profile(request: Request):
            actor = get_request_actor(request)
            if not actor:
                raise HTTPException(401)
            return {"user_id": actor.actor_id}
    """
    from autonomize_observer.audit.context import get_actor_context

    return get_actor_context()
