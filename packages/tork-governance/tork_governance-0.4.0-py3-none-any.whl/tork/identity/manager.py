"""
Identity manager for AI agent authentication and authorization.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import structlog

from tork.identity.jwt_handler import JWTHandler, AgentClaims
from tork.identity.exceptions import InvalidTokenError

logger = structlog.get_logger(__name__)


class IdentityManager:
    """Manages agent identities and authentication."""
    
    def __init__(self, jwt_handler: JWTHandler) -> None:
        """
        Initialize identity manager.
        
        Args:
            jwt_handler: JWTHandler instance for token operations
        """
        self.jwt_handler = jwt_handler
        self._registered_agents: dict[str, AgentClaims] = {}
        
        logger.info("IdentityManager initialized")
    
    def register_agent(
        self,
        agent_id: str,
        permissions: list[str],
        agent_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Register a new agent and issue a token.
        
        Args:
            agent_id: Unique agent identifier
            permissions: List of permissions (e.g., ["read", "write", "execute"])
            agent_name: Human-readable agent name
            organization_id: Organization that owns the agent
            metadata: Additional metadata
            
        Returns:
            JWT token for the agent
        """
        now = datetime.now(timezone.utc)
        
        claims = AgentClaims(
            agent_id=agent_id,
            agent_name=agent_name,
            permissions=permissions,
            organization_id=organization_id,
            issued_at=now,
            expires_at=now + timedelta(hours=self.jwt_handler.default_expiry_hours),
            metadata=metadata,
        )
        
        self._registered_agents[agent_id] = claims
        token = self.jwt_handler.issue_token(claims)
        
        logger.info(
            "Agent registered",
            agent_id=agent_id,
            permissions=permissions,
            organization_id=organization_id,
        )
        
        return token
    
    def verify_agent(self, token: str) -> AgentClaims:
        """
        Verify an agent token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded AgentClaims for the agent
            
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        claims = self.jwt_handler.verify_token(token)
        logger.info("Agent verified", agent_id=claims.agent_id)
        return claims
    
    def update_permissions(
        self,
        token: str,
        permissions: list[str],
    ) -> str:
        """
        Update agent permissions and issue a new token.
        
        Args:
            token: Current agent token
            permissions: Updated list of permissions
            
        Returns:
            New JWT token with updated permissions
            
        Raises:
            InvalidTokenError: If token is invalid
        """
        try:
            claims = self.jwt_handler.verify_token(token)
        except InvalidTokenError as e:
            raise InvalidTokenError(f"Cannot update permissions: {str(e)}")
        
        # Revoke old token
        self.jwt_handler.revoke_token(token)
        
        # Create new token with updated permissions
        now = datetime.now(timezone.utc)
        new_claims = AgentClaims(
            agent_id=claims.agent_id,
            agent_name=claims.agent_name,
            permissions=permissions,
            organization_id=claims.organization_id,
            issued_at=now,
            expires_at=now + timedelta(hours=self.jwt_handler.default_expiry_hours),
            metadata=claims.metadata,
        )
        
        new_token = self.jwt_handler.issue_token(new_claims)
        
        # Update registered agent
        self._registered_agents[claims.agent_id] = new_claims
        
        logger.info(
            "Agent permissions updated",
            agent_id=claims.agent_id,
            permissions=permissions,
        )
        
        return new_token
    
    def list_registered_agents(self) -> list[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._registered_agents.keys())
