"""
FastAPI server for governed HTTP proxy.

Creates a FastAPI application that proxies requests through
governance controls.
"""

from typing import Any, Optional
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import JSONResponse
import structlog

from tork.core.engine import GovernanceEngine
from tork.adapters.http.proxy import ProxyConfig, GovernedProxy

logger = structlog.get_logger(__name__)


def create_proxy_app(
    config: ProxyConfig,
    engine: GovernanceEngine,
    identity_manager: Optional[Any] = None,
    receipt_generator: Optional[Any] = None,
    title: str = "Tork Governed Proxy",
    description: str = "HTTP proxy with governance controls",
) -> FastAPI:
    """
    Create a FastAPI application for governed HTTP proxying.
    
    Args:
        config: Proxy configuration with target URL.
        engine: GovernanceEngine for policy evaluation.
        identity_manager: Optional IdentityManager for authentication.
        receipt_generator: Optional ReceiptGenerator for audit trails.
        title: API title for OpenAPI docs.
        description: API description for OpenAPI docs.
        
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title=title, description=description)
    
    proxy = GovernedProxy(
        config=config,
        engine=engine,
        identity_manager=identity_manager,
        receipt_generator=receipt_generator,
    )
    
    async def handle_request(
        request: Request,
        path: str,
        method: str,
        x_agent_id: Optional[str] = None,
    ) -> Response:
        """Handle a proxied request with governance controls."""
        agent_id = x_agent_id or "http-proxy"
        
        body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
            except Exception:
                body = {}
        
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)
        headers.pop("x-agent-id", None)
        
        result = await proxy.request(
            method=method,
            path=path,
            body=body,
            headers=headers,
            agent_id=agent_id,
        )
        
        response_headers = {
            "X-Tork-Request-Decision": result.request_decision.value,
            "X-Tork-Response-Decision": result.response_decision.value,
        }
        
        if result.receipts:
            response_headers["X-Tork-Receipt-ID"] = ",".join(result.receipts)
        
        return JSONResponse(
            status_code=result.status_code,
            content=result.body,
            headers=response_headers,
        )
    
    @app.api_route("/{path:path}", methods=["GET"])
    async def proxy_get(
        request: Request,
        path: str,
        x_agent_id: Optional[str] = Header(None),
    ) -> Response:
        """Proxy GET requests with governance controls."""
        return await handle_request(request, path, "GET", x_agent_id)
    
    @app.api_route("/{path:path}", methods=["POST"])
    async def proxy_post(
        request: Request,
        path: str,
        x_agent_id: Optional[str] = Header(None),
    ) -> Response:
        """Proxy POST requests with governance controls."""
        return await handle_request(request, path, "POST", x_agent_id)
    
    @app.api_route("/{path:path}", methods=["PUT"])
    async def proxy_put(
        request: Request,
        path: str,
        x_agent_id: Optional[str] = Header(None),
    ) -> Response:
        """Proxy PUT requests with governance controls."""
        return await handle_request(request, path, "PUT", x_agent_id)
    
    @app.api_route("/{path:path}", methods=["DELETE"])
    async def proxy_delete(
        request: Request,
        path: str,
        x_agent_id: Optional[str] = Header(None),
    ) -> Response:
        """Proxy DELETE requests with governance controls."""
        return await handle_request(request, path, "DELETE", x_agent_id)
    
    @app.api_route("/{path:path}", methods=["PATCH"])
    async def proxy_patch(
        request: Request,
        path: str,
        x_agent_id: Optional[str] = Header(None),
    ) -> Response:
        """Proxy PATCH requests with governance controls."""
        return await handle_request(request, path, "PATCH", x_agent_id)
    
    logger.info(
        "Proxy app created",
        target_url=config.target_base_url,
    )
    
    return app
