"""Audit logging module with Keycloak integration.

This is functionality NOT provided by Logfire - we add:
- Keycloak JWT token parsing for actor context
- Compliance-focused audit events (HIPAA, GDPR, SOC2)
- Immutable audit trail with retention policies
- Custom actor context providers
"""

from autonomize_observer.audit.context import (
    ActorContext,
    get_actor_context,
    set_actor_context,
    set_actor_from_keycloak_token,
)
from autonomize_observer.audit.logger import AuditLogger

__all__ = [
    "AuditLogger",
    "ActorContext",
    "get_actor_context",
    "set_actor_context",
    "set_actor_from_keycloak_token",
]
