"""
Tests for identity management system.
"""

from datetime import datetime, timedelta, timezone
import time
import pytest

from tork.identity import (
    JWTHandler,
    AgentClaims,
    IdentityManager,
    InvalidTokenError,
    ExpiredTokenError,
    RevokedTokenError,
)


class TestJWTHandler:
    """Tests for JWTHandler."""
    
    @pytest.fixture
    def handler(self):
        """Create a JWT handler for testing."""
        return JWTHandler(secret_key="test-secret-key-for-testing")
    
    def test_issue_token(self, handler):
        """Test issuing a token."""
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-001",
            agent_name="Test Agent",
            permissions=["read", "write"],
            organization_id="org-001",
            issued_at=now,
            expires_at=now + timedelta(hours=24),
        )
        
        token = handler.issue_token(claims)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self, handler):
        """Test verifying a valid token."""
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-002",
            agent_name="Test Agent 2",
            permissions=["read", "execute"],
            issued_at=now,
            expires_at=now + timedelta(hours=24),
            metadata={"role": "assistant"},
        )
        
        token = handler.issue_token(claims)
        verified = handler.verify_token(token)
        
        assert verified.agent_id == "agent-002"
        assert verified.agent_name == "Test Agent 2"
        assert verified.permissions == ["read", "execute"]
        assert verified.metadata == {"role": "assistant"}
    
    def test_verify_token_invalid(self, handler):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(InvalidTokenError):
            handler.verify_token(invalid_token)
    
    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        handler = JWTHandler(secret_key="test-secret", default_expiry_hours=0)
        
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-003",
            issued_at=now,
            expires_at=now - timedelta(seconds=1),
        )
        
        token = handler.issue_token(claims)
        
        time.sleep(1)
        
        with pytest.raises(ExpiredTokenError):
            handler.verify_token(token)
    
    def test_revoke_token(self, handler):
        """Test revoking a token."""
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-004",
            issued_at=now,
            expires_at=now + timedelta(hours=24),
        )
        
        token = handler.issue_token(claims)
        assert handler.is_revoked(token) is False
        
        handler.revoke_token(token)
        assert handler.is_revoked(token) is True
    
    def test_verify_revoked_token(self, handler):
        """Test verifying a revoked token raises error."""
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-005",
            issued_at=now,
            expires_at=now + timedelta(hours=24),
        )
        
        token = handler.issue_token(claims)
        handler.revoke_token(token)
        
        with pytest.raises(RevokedTokenError):
            handler.verify_token(token)
    
    def test_refresh_token(self, handler):
        """Test refreshing a token."""
        now = datetime.now(timezone.utc)
        claims = AgentClaims(
            agent_id="agent-006",
            permissions=["read"],
            issued_at=now,
            expires_at=now + timedelta(hours=24),
        )
        
        token = handler.issue_token(claims)
        
        new_token = handler.refresh_token(token, extend_hours=48)
        
        assert new_token != token
        assert handler.is_revoked(token) is True
        
        new_claims = handler.verify_token(new_token)
        assert new_claims.agent_id == "agent-006"
        assert new_claims.permissions == ["read"]
    
    def test_refresh_invalid_token(self, handler):
        """Test refreshing an invalid token raises error."""
        with pytest.raises(InvalidTokenError):
            handler.refresh_token("invalid.token")


class TestIdentityManager:
    """Tests for IdentityManager."""
    
    @pytest.fixture
    def manager(self):
        """Create an identity manager for testing."""
        handler = JWTHandler(secret_key="test-secret-key")
        return IdentityManager(handler)
    
    def test_register_agent(self, manager):
        """Test registering an agent."""
        token = manager.register_agent(
            agent_id="agent-100",
            permissions=["read", "write"],
            agent_name="Production Agent",
            organization_id="acme-corp",
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert "agent-100" in manager.list_registered_agents()
    
    def test_verify_agent(self, manager):
        """Test verifying an agent token."""
        token = manager.register_agent(
            agent_id="agent-101",
            permissions=["read", "execute"],
            agent_name="Test Agent",
        )
        
        claims = manager.verify_agent(token)
        
        assert claims.agent_id == "agent-101"
        assert claims.agent_name == "Test Agent"
        assert claims.permissions == ["read", "execute"]
    
    def test_update_permissions(self, manager):
        """Test updating agent permissions."""
        token = manager.register_agent(
            agent_id="agent-102",
            permissions=["read"],
        )
        
        new_token = manager.update_permissions(token, ["read", "write", "delete"])
        
        assert new_token != token
        
        new_claims = manager.verify_agent(new_token)
        assert new_claims.permissions == ["read", "write", "delete"]
    
    def test_list_registered_agents(self, manager):
        """Test listing registered agents."""
        manager.register_agent("agent-201", ["read"])
        manager.register_agent("agent-202", ["write"])
        manager.register_agent("agent-203", ["execute"])
        
        agents = manager.list_registered_agents()
        
        assert len(agents) == 3
        assert "agent-201" in agents
        assert "agent-202" in agents
        assert "agent-203" in agents
    
    def test_verify_expired_token(self, manager):
        """Test verifying an expired token."""
        token = manager.register_agent("agent-104", ["read"])
        
        manager.jwt_handler.revoke_token(token)
        
        with pytest.raises(RevokedTokenError):
            manager.verify_agent(token)
