"""
HTTP Proxy with Governance Controls.

Provides a governed HTTP proxy that evaluates requests and responses
against governance policies before forwarding.
"""

from typing import Any, Optional
import httpx
import structlog
from pydantic import BaseModel, Field

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest, EvaluationResult, PolicyDecision

logger = structlog.get_logger(__name__)


class ProxyConfig(BaseModel):
    """Configuration for the governed HTTP proxy."""
    
    target_base_url: str = Field(..., description="Base URL of the target service")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    headers: dict[str, str] = Field(default_factory=dict, description="Default headers to include")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")


class ProxyResponse(BaseModel):
    """Response from the governed proxy."""
    
    status_code: int = Field(..., description="HTTP status code from target")
    body: Optional[dict | str] = Field(default=None, description="Response body")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    request_decision: PolicyDecision = Field(..., description="Governance decision for request")
    response_decision: PolicyDecision = Field(..., description="Governance decision for response")
    receipts: list[str] = Field(default_factory=list, description="Receipt IDs if generated")


class GovernedProxy:
    """
    HTTP proxy with governance controls.
    
    Evaluates requests before forwarding and responses before returning,
    enforcing governance policies at both stages.
    """
    
    def __init__(
        self,
        config: ProxyConfig,
        engine: GovernanceEngine,
        identity_manager: Optional[Any] = None,
        receipt_generator: Optional[Any] = None,
    ) -> None:
        """
        Initialize the governed proxy.
        
        Args:
            config: Proxy configuration.
            engine: GovernanceEngine for policy evaluation.
            identity_manager: Optional IdentityManager for authentication.
            receipt_generator: Optional ReceiptGenerator for audit trails.
        """
        self.config = config
        self.engine = engine
        self.identity_manager = identity_manager
        self.receipt_generator = receipt_generator
        
        logger.info(
            "GovernedProxy initialized",
            target_url=config.target_base_url,
            timeout=config.timeout,
        )
    
    def _evaluate_request(
        self,
        method: str,
        path: str,
        body: Optional[dict],
        agent_id: str,
    ) -> EvaluationResult:
        """
        Evaluate an outgoing request against governance policies.
        
        Args:
            method: HTTP method.
            path: Request path.
            body: Request body.
            agent_id: Agent making the request.
            
        Returns:
            EvaluationResult from governance engine.
        """
        payload = {
            "method": method,
            "path": path,
            "body": body or {},
        }
        
        request = EvaluationRequest(
            agent_id=agent_id,
            action=f"http_{method.lower()}_request",
            payload=payload,
        )
        
        return self.engine.evaluate(request)
    
    def _evaluate_response(
        self,
        response_body: Any,
        agent_id: str,
    ) -> EvaluationResult:
        """
        Evaluate an incoming response against governance policies.
        
        Args:
            response_body: Response body from target.
            agent_id: Agent receiving the response.
            
        Returns:
            EvaluationResult from governance engine.
        """
        if isinstance(response_body, dict):
            payload = response_body
        else:
            payload = {"response": response_body}
        
        request = EvaluationRequest(
            agent_id=agent_id,
            action="http_response",
            payload=payload,
        )
        
        return self.engine.evaluate(request)
    
    async def request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        agent_id: Optional[str] = None,
    ) -> ProxyResponse:
        """
        Make a governed HTTP request.
        
        Evaluates the request before sending, forwards to target,
        then evaluates the response before returning.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: Request path (appended to target_base_url)
            body: Optional request body (for POST/PUT)
            headers: Optional additional headers
            agent_id: Agent ID for governance (defaults to 'http-proxy')
            
        Returns:
            ProxyResponse with status, body, headers, and decisions.
        """
        agent_id = agent_id or "http-proxy"
        receipts: list[str] = []
        
        request_result = self._evaluate_request(method, path, body, agent_id)
        
        if self.receipt_generator:
            req = EvaluationRequest(
                agent_id=agent_id,
                action=f"http_{method.lower()}_request",
                payload={"method": method, "path": path, "body": body or {}},
            )
            receipt = self.receipt_generator.generate(request_result, req)
            receipts.append(receipt.receipt_id)
        
        if request_result.decision == PolicyDecision.DENY:
            logger.warning(
                "Request denied by governance",
                method=method,
                path=path,
                violations=request_result.violations,
            )
            return ProxyResponse(
                status_code=403,
                body={"error": "Request denied by governance policy", "violations": request_result.violations},
                headers={},
                request_decision=PolicyDecision.DENY,
                response_decision=PolicyDecision.ALLOW,
                receipts=receipts,
            )
        
        if request_result.decision == PolicyDecision.REDACT and request_result.modified_payload:
            body = request_result.modified_payload.get("body", body)
        
        url = f"{self.config.target_base_url.rstrip('/')}/{path.lstrip('/')}"
        
        request_headers = {**self.config.headers}
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        ) as client:
            try:
                if method.upper() in ("POST", "PUT", "PATCH"):
                    response = await client.request(
                        method=method,
                        url=url,
                        json=body,
                        headers=request_headers,
                    )
                else:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                    )
                
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text
                
                response_headers = dict(response.headers)
                status_code = response.status_code
                
            except httpx.RequestError as e:
                logger.error("HTTP request failed", error=str(e))
                return ProxyResponse(
                    status_code=502,
                    body={"error": f"Upstream request failed: {str(e)}"},
                    headers={},
                    request_decision=request_result.decision,
                    response_decision=PolicyDecision.ALLOW,
                    receipts=receipts,
                )
        
        response_result = self._evaluate_response(response_body, agent_id)
        
        if self.receipt_generator:
            req = EvaluationRequest(
                agent_id=agent_id,
                action="http_response",
                payload={"response": response_body} if not isinstance(response_body, dict) else response_body,
            )
            receipt = self.receipt_generator.generate(response_result, req)
            receipts.append(receipt.receipt_id)
        
        final_body = response_body
        if response_result.decision == PolicyDecision.REDACT and response_result.modified_payload:
            final_body = response_result.modified_payload
        
        logger.info(
            "Proxy request completed",
            method=method,
            path=path,
            status_code=status_code,
            request_decision=request_result.decision.value,
            response_decision=response_result.decision.value,
        )
        
        return ProxyResponse(
            status_code=status_code,
            body=final_body,
            headers=response_headers,
            request_decision=request_result.decision,
            response_decision=response_result.decision,
            receipts=receipts,
        )
