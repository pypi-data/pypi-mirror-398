"""
FastAPI Application

REST API for governance operations.
"""

from typing import Any, Optional
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tork.api.playground import PlaygroundService


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str


class EvaluateRequest(BaseModel):
    """Evaluate payload request."""
    payload: dict[str, Any]
    agent_id: str = Field(default="playground")


class EvaluateResponse(BaseModel):
    """Evaluate response."""
    decision: str
    violations: list[str]
    modified_payload: dict[str, Any]
    pii_found: list[dict[str, Any]]
    processing_time_ms: float


class RedactRequest(BaseModel):
    """Redact text request."""
    text: str
    pii_types: Optional[list[str]] = None


class RedactResponse(BaseModel):
    """Redact response."""
    original: str
    redacted: str
    matches: list[dict[str, Any]]
    processing_time_ms: float


class ScanRequest(BaseModel):
    """Scan content request."""
    content: str
    filename: str = Field(default="config.json")


class ScanResponse(BaseModel):
    """Scan response."""
    findings: list[dict[str, Any]]
    summary: dict[str, int]
    processing_time_ms: float


class PoliciesResponse(BaseModel):
    """Policies list response."""
    policies: list[dict[str, Any]]


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Tork Governance API",
        description="REST API for AI agent governance operations",
        version="0.1.0",
    )
    
    playground = PlaygroundService()
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version="0.1.0")
    
    @app.post("/playground/evaluate", response_model=EvaluateResponse)
    async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
        """Evaluate a payload against governance policies."""
        result = playground.evaluate_payload(
            payload=request.payload,
            agent_id=request.agent_id,
        )
        return EvaluateResponse(**result)
    
    @app.post("/playground/redact", response_model=RedactResponse)
    async def redact(request: RedactRequest) -> RedactResponse:
        """Redact PII from text."""
        result = playground.redact_text(
            text=request.text,
            pii_types=request.pii_types,
        )
        return RedactResponse(**result)
    
    @app.post("/playground/scan", response_model=ScanResponse)
    async def scan(request: ScanRequest) -> ScanResponse:
        """Scan configuration content for security issues."""
        result = playground.scan_content(
            content=request.content,
            filename=request.filename,
        )
        return ScanResponse(**result)
    
    @app.get("/playground/policies", response_model=PoliciesResponse)
    async def policies() -> PoliciesResponse:
        """List all available policies."""
        policy_list = playground.list_policies()
        return PoliciesResponse(policies=policy_list)
    
    @app.get("/")
    async def root() -> FileResponse:
        """Serve the playground UI."""
        static_path = Path(__file__).parent / "static" / "index.html"
        return FileResponse(static_path)
    
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    return app


app = create_app()
