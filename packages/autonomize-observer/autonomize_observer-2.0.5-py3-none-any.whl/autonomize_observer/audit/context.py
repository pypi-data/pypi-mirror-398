"""Actor context management with Keycloak JWT support.

Provides thread-safe actor context using contextvars, with built-in
support for extracting user information from Keycloak JWT tokens.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Thread-safe context variable for current actor
_actor_context: ContextVar[ActorContext | None] = ContextVar(
    "actor_context", default=None
)


@dataclass
class ActorContext:
    """Context about the actor performing an action.

    Can be populated from:
    - Keycloak JWT token
    - Custom provider function
    - Manual construction
    """

    actor_id: str
    actor_type: str = "user"  # user, service, system
    email: str | None = None
    name: str | None = None
    username: str | None = None
    roles: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    organization_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    raw_claims: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def system(cls, service_name: str = "system") -> ActorContext:
        """Create a system actor context."""
        return cls(
            actor_id=service_name,
            actor_type="system",
            name=service_name,
        )

    @classmethod
    def service(cls, service_id: str, service_name: str) -> ActorContext:
        """Create a service actor context."""
        return cls(
            actor_id=service_id,
            actor_type="service",
            name=service_name,
        )

    @classmethod
    def from_keycloak_token(
        cls,
        token_payload: dict[str, Any],
        claim_mappings: dict[str, str] | None = None,
    ) -> ActorContext:
        """Create ActorContext from a decoded Keycloak JWT payload.

        Args:
            token_payload: Decoded JWT payload (claims)
            claim_mappings: Optional custom claim mappings. Keys are
                ActorContext field names, values are JWT claim paths.
                Supports nested claims with dot notation.

        Returns:
            ActorContext populated from the token

        Example:
            # Standard Keycloak token
            payload = {
                "sub": "user-123",
                "email": "user@example.com",
                "name": "John Doe",
                "preferred_username": "johnd",
                "realm_access": {"roles": ["admin", "user"]},
            }
            actor = ActorContext.from_keycloak_token(payload)

            # Custom claim mappings
            custom_mappings = {
                "tenant_id": "custom_claims.tenant",
                "organization_id": "org_id",
            }
            actor = ActorContext.from_keycloak_token(payload, custom_mappings)
        """
        # Default Keycloak claim mappings
        defaults = {
            "actor_id": "sub",
            "email": "email",
            "name": "name",
            "username": "preferred_username",
            "roles": "realm_access.roles",
            "groups": "groups",
            "tenant_id": "tenant_id",
            "organization_id": "organization_id",
            "session_id": "session_state",
        }

        # Merge with custom mappings
        mappings = {**defaults, **(claim_mappings or {})}

        def get_nested_claim(data: dict, path: str) -> Any:
            """Get a nested claim value using dot notation."""
            keys = path.split(".")
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                    if value is None:
                        return None
                else:
                    return None
            return value

        # Extract values using mappings
        actor_id = get_nested_claim(token_payload, mappings["actor_id"]) or "unknown"
        email = get_nested_claim(token_payload, mappings["email"])
        name = get_nested_claim(token_payload, mappings["name"])
        username = get_nested_claim(token_payload, mappings["username"])
        roles = get_nested_claim(token_payload, mappings["roles"]) or []
        groups = get_nested_claim(token_payload, mappings["groups"]) or []
        tenant_id = get_nested_claim(token_payload, mappings["tenant_id"])
        organization_id = get_nested_claim(token_payload, mappings["organization_id"])
        session_id = get_nested_claim(token_payload, mappings["session_id"])

        # Ensure roles and groups are lists
        if isinstance(roles, str):
            roles = [roles]
        if isinstance(groups, str):
            groups = [groups]

        return cls(
            actor_id=str(actor_id),
            actor_type="user",
            email=email,
            name=name,
            username=username,
            roles=list(roles),
            groups=list(groups),
            tenant_id=tenant_id,
            organization_id=organization_id,
            session_id=session_id,
            raw_claims=token_payload,
        )

    @classmethod
    def from_jwt(
        cls,
        token: str,
        secret_or_public_key: str | bytes | None = None,
        algorithms: list[str] | None = None,
        verify: bool = True,
        claim_mappings: dict[str, str] | None = None,
    ) -> ActorContext:
        """Create ActorContext by decoding a JWT token.

        Args:
            token: The JWT token string
            secret_or_public_key: Key for verification. If None, token
                is decoded without verification (not recommended for prod)
            algorithms: List of allowed algorithms (default: ["RS256", "HS256"])
            verify: Whether to verify the signature
            claim_mappings: Custom claim mappings

        Returns:
            ActorContext populated from the token
        """
        import jwt

        options = {"verify_signature": verify}
        if not verify:
            options["verify_exp"] = False
            options["verify_aud"] = False

        algorithms = algorithms or ["RS256", "HS256"]

        try:
            if verify and secret_or_public_key:
                payload = jwt.decode(
                    token,
                    secret_or_public_key,
                    algorithms=algorithms,
                    options=options,
                )
            else:
                # Decode without verification (for testing or when
                # verification is done elsewhere)
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )

            return cls.from_keycloak_token(payload, claim_mappings)

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "email": self.email,
            "name": self.name,
            "username": self.username,
            "roles": self.roles,
            "groups": self.groups,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
        }


# Custom provider type
ActorContextProvider = Callable[[], ActorContext | None]

# Registry for custom providers
_custom_providers: list[ActorContextProvider] = []


def register_actor_provider(provider: ActorContextProvider) -> None:
    """Register a custom actor context provider.

    Providers are called in order until one returns a non-None value.

    Args:
        provider: Callable that returns ActorContext or None

    Example:
        def get_actor_from_request():
            # Get from Flask/FastAPI request context
            if has_request_context():
                return ActorContext.from_jwt(request.headers.get("Authorization"))
            return None

        register_actor_provider(get_actor_from_request)
    """
    _custom_providers.append(provider)


def clear_actor_providers() -> None:
    """Clear all registered actor context providers."""
    _custom_providers.clear()


def get_actor_context() -> ActorContext | None:
    """Get the current actor context.

    First checks the contextvar, then tries registered providers.

    Returns:
        Current ActorContext or None if not set
    """
    # First check contextvar
    ctx = _actor_context.get()
    if ctx is not None:
        return ctx

    # Try registered providers
    for provider in _custom_providers:
        try:
            ctx = provider()
            if ctx is not None:
                return ctx
        except Exception as e:
            logger.warning(f"Actor provider failed: {e}")

    return None


def set_actor_context(actor: ActorContext | None) -> None:
    """Set the current actor context.

    Args:
        actor: ActorContext to set, or None to clear
    """
    _actor_context.set(actor)


def set_actor_from_keycloak_token(
    token_payload: dict[str, Any],
    claim_mappings: dict[str, str] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ActorContext:
    """Set actor context from a decoded Keycloak JWT payload.

    Convenience function that creates and sets the actor context.

    Args:
        token_payload: Decoded JWT payload
        claim_mappings: Optional custom claim mappings
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created ActorContext
    """
    actor = ActorContext.from_keycloak_token(token_payload, claim_mappings)
    actor.ip_address = ip_address
    actor.user_agent = user_agent
    set_actor_context(actor)
    return actor
