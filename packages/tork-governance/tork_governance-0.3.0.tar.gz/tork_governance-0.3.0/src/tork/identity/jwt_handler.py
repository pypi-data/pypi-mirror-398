"""
JWT-based identity handler for AI agent authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import structlog

from tork.identity.exceptions import (
    InvalidTokenError,
    ExpiredTokenError,
    RevokedTokenError,
)
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class AgentClaims(BaseModel):
    """JWT claims for an AI agent."""
    
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: Optional[str] = Field(None, description="Human-readable agent name")
    permissions: list[str] = Field(default_factory=list, description="List of permissions (e.g., read, write, execute)")
    organization_id: Optional[str] = Field(None, description="Organization that owns the agent")
    issued_at: datetime = Field(..., description="Token issuance time")
    expires_at: datetime = Field(..., description="Token expiration time")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class JWTHandler:
    """Handler for JWT token operations."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        default_expiry_hours: int = 24,
    ) -> None:
        """
        Initialize JWT handler.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            default_expiry_hours: Default token expiry in hours
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.default_expiry_hours = default_expiry_hours
        self._revoked_tokens: set[str] = set()
        
        logger.info(
            "JWTHandler initialized",
            algorithm=algorithm,
            default_expiry_hours=default_expiry_hours,
        )
    
    def issue_token(self, claims: AgentClaims) -> str:
        """
        Issue a JWT token for an agent.
        
        Args:
            claims: AgentClaims object with agent information
            
        Returns:
            Encoded JWT token
        """
        payload = {
            "agent_id": claims.agent_id,
            "agent_name": claims.agent_name,
            "permissions": claims.permissions,
            "organization_id": claims.organization_id,
            "issued_at": claims.issued_at.isoformat(),
            "expires_at": claims.expires_at.isoformat(),
            "exp": claims.expires_at,
            "metadata": claims.metadata or {},
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(
            "Token issued",
            agent_id=claims.agent_id,
            expires_at=claims.expires_at.isoformat(),
        )
        
        return token
    
    def verify_token(self, token: str) -> AgentClaims:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded AgentClaims
            
        Raises:
            RevokedTokenError: If token has been revoked
            ExpiredTokenError: If token has expired
            InvalidTokenError: If token is invalid
        """
        if self.is_revoked(token):
            raise RevokedTokenError("Token has been revoked")
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True},
            )
        except jwt.ExpiredSignatureError as e:
            raise ExpiredTokenError(f"Token has expired: {str(e)}")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        
        try:
            claims = AgentClaims(
                agent_id=payload["agent_id"],
                agent_name=payload.get("agent_name"),
                permissions=payload.get("permissions", []),
                organization_id=payload.get("organization_id"),
                issued_at=datetime.fromisoformat(payload["issued_at"]),
                expires_at=datetime.fromisoformat(payload["expires_at"]),
                metadata=payload.get("metadata"),
            )
        except (KeyError, ValueError) as e:
            raise InvalidTokenError(f"Invalid token claims: {str(e)}")
        
        logger.info("Token verified", agent_id=claims.agent_id)
        return claims
    
    def refresh_token(self, token: str, extend_hours: int = 24) -> str:
        """
        Refresh a token by extending its expiration.
        
        Args:
            token: Current token to refresh
            extend_hours: Hours to extend expiration by
            
        Returns:
            New token with extended expiration
            
        Raises:
            InvalidTokenError: If token cannot be refreshed
        """
        try:
            claims = self.verify_token(token)
        except InvalidTokenError as e:
            raise InvalidTokenError(f"Cannot refresh invalid token: {str(e)}")
        
        # Revoke old token
        self.revoke_token(token)
        
        # Create new token with extended expiration
        now = datetime.now(timezone.utc)
        new_claims = AgentClaims(
            agent_id=claims.agent_id,
            agent_name=claims.agent_name,
            permissions=claims.permissions,
            organization_id=claims.organization_id,
            issued_at=now,
            expires_at=now + timedelta(hours=extend_hours),
            metadata=claims.metadata,
        )
        
        new_token = self.issue_token(new_claims)
        
        logger.info(
            "Token refreshed",
            agent_id=claims.agent_id,
            extend_hours=extend_hours,
        )
        
        return new_token
    
    def revoke_token(self, token: str) -> None:
        """
        Revoke a token.
        
        Args:
            token: Token to revoke
        """
        self._revoked_tokens.add(token)
        logger.info("Token revoked")
    
    def is_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: Token to check
            
        Returns:
            True if token is revoked, False otherwise
        """
        return token in self._revoked_tokens
