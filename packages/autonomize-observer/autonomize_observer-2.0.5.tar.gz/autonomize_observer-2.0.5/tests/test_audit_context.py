"""Tests for audit context module."""

from unittest.mock import MagicMock, patch

import pytest

from autonomize_observer.audit.context import (
    ActorContext,
    clear_actor_providers,
    get_actor_context,
    register_actor_provider,
    set_actor_context,
    set_actor_from_keycloak_token,
)


class TestActorContext:
    """Tests for ActorContext."""

    def test_basic_creation(self):
        """Test basic actor context creation."""
        actor = ActorContext(actor_id="user-123")
        assert actor.actor_id == "user-123"
        assert actor.actor_type == "user"
        assert actor.email is None
        assert actor.name is None
        assert actor.roles == []
        assert actor.groups == []

    def test_full_creation(self):
        """Test actor context with all fields."""
        actor = ActorContext(
            actor_id="user-123",
            actor_type="service",
            email="test@example.com",
            name="Test User",
            username="testuser",
            roles=["admin"],
            groups=["team-a"],
            tenant_id="tenant-1",
            organization_id="org-1",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session-123",
        )
        assert actor.actor_id == "user-123"
        assert actor.actor_type == "service"
        assert actor.email == "test@example.com"
        assert actor.name == "Test User"
        assert actor.username == "testuser"
        assert actor.roles == ["admin"]
        assert actor.groups == ["team-a"]
        assert actor.tenant_id == "tenant-1"
        assert actor.organization_id == "org-1"
        assert actor.ip_address == "192.168.1.1"
        assert actor.user_agent == "Mozilla/5.0"
        assert actor.session_id == "session-123"

    def test_system_factory(self):
        """Test system actor factory method."""
        actor = ActorContext.system("my-service")
        assert actor.actor_id == "my-service"
        assert actor.actor_type == "system"
        assert actor.name == "my-service"

    def test_service_factory(self):
        """Test service actor factory method."""
        actor = ActorContext.service("svc-123", "My Service")
        assert actor.actor_id == "svc-123"
        assert actor.actor_type == "service"
        assert actor.name == "My Service"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        actor = ActorContext(
            actor_id="user-123",
            email="test@example.com",
            roles=["admin"],
        )
        result = actor.to_dict()
        assert result["actor_id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["roles"] == ["admin"]
        assert "actor_type" in result


class TestActorContextFromKeycloak:
    """Tests for Keycloak token parsing."""

    def test_from_keycloak_token(self, sample_keycloak_token):
        """Test creating actor from Keycloak token."""
        actor = ActorContext.from_keycloak_token(sample_keycloak_token)
        assert actor.actor_id == "user-123"
        assert actor.email == "test@example.com"
        assert actor.name == "Test User"
        assert actor.username == "testuser"
        assert actor.roles == ["admin", "user"]
        assert actor.groups == ["/org/team"]
        assert actor.session_id == "session-456"
        assert actor.actor_type == "user"

    def test_from_keycloak_token_custom_mappings(self):
        """Test custom claim mappings."""
        token = {
            "sub": "user-456",
            "custom_email": "custom@example.com",
            "nested": {"tenant": "tenant-1"},
        }
        mappings = {
            "email": "custom_email",
            "tenant_id": "nested.tenant",
        }
        actor = ActorContext.from_keycloak_token(token, mappings)
        assert actor.actor_id == "user-456"
        assert actor.email == "custom@example.com"
        assert actor.tenant_id == "tenant-1"

    def test_from_keycloak_token_missing_claims(self):
        """Test with minimal token."""
        token = {"sub": "minimal-user"}
        actor = ActorContext.from_keycloak_token(token)
        assert actor.actor_id == "minimal-user"
        assert actor.email is None
        assert actor.name is None
        assert actor.roles == []

    def test_from_jwt_without_verification(self):
        """Test JWT decoding without verification."""
        # Create a test JWT (unsigned for testing)
        import jwt

        payload = {
            "sub": "jwt-user",
            "email": "jwt@example.com",
            "name": "JWT User",
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        actor = ActorContext.from_jwt(token, verify=False)
        assert actor.actor_id == "jwt-user"
        assert actor.email == "jwt@example.com"
        assert actor.name == "JWT User"

    def test_roles_as_string(self):
        """Test handling roles as string instead of list."""
        token = {
            "sub": "user-1",
            "realm_access": {"roles": "single-role"},
        }
        actor = ActorContext.from_keycloak_token(token)
        assert actor.roles == ["single-role"]


class TestActorContextGlobal:
    """Tests for global actor context management."""

    def setup_method(self):
        """Reset context before each test."""
        set_actor_context(None)
        clear_actor_providers()

    def test_get_set_actor_context(self):
        """Test getting and setting actor context."""
        assert get_actor_context() is None

        actor = ActorContext(actor_id="user-123")
        set_actor_context(actor)

        result = get_actor_context()
        assert result is not None
        assert result.actor_id == "user-123"

    def test_clear_actor_context(self):
        """Test clearing actor context."""
        actor = ActorContext(actor_id="user-123")
        set_actor_context(actor)
        assert get_actor_context() is not None

        set_actor_context(None)
        assert get_actor_context() is None

    def test_set_actor_from_keycloak_token(self, sample_keycloak_token):
        """Test setting actor from Keycloak token."""
        actor = set_actor_from_keycloak_token(
            sample_keycloak_token,
            ip_address="10.0.0.1",
            user_agent="Test Agent",
        )

        assert actor.actor_id == "user-123"
        assert actor.ip_address == "10.0.0.1"
        assert actor.user_agent == "Test Agent"

        # Verify it was set globally
        result = get_actor_context()
        assert result is not None
        assert result.actor_id == "user-123"

    def test_register_actor_provider(self):
        """Test registering custom actor provider."""
        actor = ActorContext(actor_id="provider-user")

        def custom_provider():
            return actor

        register_actor_provider(custom_provider)

        result = get_actor_context()
        assert result is not None
        assert result.actor_id == "provider-user"

    def test_provider_returns_none(self):
        """Test provider that returns None."""

        def null_provider():
            return None

        register_actor_provider(null_provider)
        assert get_actor_context() is None

    def test_multiple_providers(self):
        """Test multiple providers - first non-None wins."""

        def null_provider():
            return None

        actor = ActorContext(actor_id="second-provider")

        def second_provider():
            return actor

        register_actor_provider(null_provider)
        register_actor_provider(second_provider)

        result = get_actor_context()
        assert result is not None
        assert result.actor_id == "second-provider"

    def test_context_var_priority_over_provider(self):
        """Test that contextvar takes priority over providers."""
        actor1 = ActorContext(actor_id="contextvar-user")
        actor2 = ActorContext(actor_id="provider-user")

        def custom_provider():
            return actor2

        register_actor_provider(custom_provider)
        set_actor_context(actor1)

        result = get_actor_context()
        assert result.actor_id == "contextvar-user"

    def test_provider_exception_handling(self):
        """Test that provider exceptions don't crash."""

        def failing_provider():
            raise ValueError("Provider failed")

        register_actor_provider(failing_provider)

        # Should not raise, just return None
        result = get_actor_context()
        assert result is None


class TestActorContextEdgeCases:
    """Tests for edge cases in actor context."""

    def test_nested_claim_non_dict_value(self):
        """Test get_nested_claim when intermediate value is not a dict."""
        # This tests line 125 - when value is not a dict in nested claim
        token = {
            "sub": "user-1",
            "simple_value": "not-a-dict",
        }
        mappings = {
            "tenant_id": "simple_value.nested.key",
        }
        actor = ActorContext.from_keycloak_token(token, mappings)
        assert actor.tenant_id is None

    def test_groups_as_string(self):
        """Test handling groups as string instead of list."""
        token = {
            "sub": "user-1",
            "groups": "single-group",
        }
        actor = ActorContext.from_keycloak_token(token)
        assert actor.groups == ["single-group"]

    def test_from_jwt_with_verification(self):
        """Test JWT decoding with verification."""
        import jwt

        payload = {
            "sub": "verified-user",
            "email": "verified@example.com",
        }
        secret = "test-secret"
        token = jwt.encode(payload, secret, algorithm="HS256")

        actor = ActorContext.from_jwt(
            token,
            secret_or_public_key=secret,
            algorithms=["HS256"],
            verify=True,
        )
        assert actor.actor_id == "verified-user"
        assert actor.email == "verified@example.com"

    def test_from_jwt_expired_token(self):
        """Test handling expired JWT token."""
        from datetime import datetime, timedelta, timezone

        import jwt

        payload = {
            "sub": "expired-user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            ActorContext.from_jwt(
                token,
                secret_or_public_key="secret",
                algorithms=["HS256"],
                verify=True,
            )

    def test_from_jwt_invalid_token(self):
        """Test handling invalid JWT token."""
        import jwt

        with pytest.raises(jwt.InvalidTokenError):
            ActorContext.from_jwt(
                "invalid-token",
                secret_or_public_key="secret",
                algorithms=["HS256"],
                verify=True,
            )
