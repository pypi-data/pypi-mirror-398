"""
Playground Service

Interactive playground for testing governance features.
"""

import time
from typing import Any, Optional

from tork.core.engine import GovernanceEngine
from tork.core.models import EvaluationRequest
from tork.core.redactor import PIIRedactor, PIIType
from tork.scanner.scanner import MCPScanner
from tork.scanner.rules import ScanFinding


class PlaygroundService:
    """
    Service for interactive playground operations.
    
    Provides evaluation, redaction, and scanning capabilities
    for testing governance features.
    """
    
    def __init__(
        self,
        engine: Optional[GovernanceEngine] = None,
        scanner: Optional[MCPScanner] = None,
    ) -> None:
        """
        Initialize the playground service.
        
        Args:
            engine: Optional GovernanceEngine instance. Creates default if None.
            scanner: Optional MCPScanner instance. Creates default if None.
        """
        if engine is None:
            self.engine = GovernanceEngine(
                pii_redactor=PIIRedactor(),
                enable_auto_redaction=True,
            )
        else:
            self.engine = engine
        
        if scanner is None:
            self.scanner = MCPScanner()
        else:
            self.scanner = scanner
        
        self._redactor = PIIRedactor()
    
    def evaluate_payload(
        self,
        payload: dict[str, Any],
        agent_id: str = "playground",
    ) -> dict[str, Any]:
        """
        Evaluate a payload against the governance engine.
        
        Args:
            payload: The payload to evaluate.
            agent_id: Optional agent ID for the request.
            
        Returns:
            Dictionary with evaluation results.
        """
        start_time = time.time()
        
        request = EvaluationRequest(
            agent_id=agent_id,
            action="playground_evaluate",
            payload=payload,
        )
        
        result = self.engine.evaluate(request)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        pii_found = []
        if result.pii_matches:
            pii_found = [
                {
                    "type": m.pii_type.value,
                    "start": m.start,
                    "end": m.end,
                }
                for m in result.pii_matches
            ]
        
        return {
            "decision": result.decision.value.upper(),
            "violations": result.violations,
            "modified_payload": result.modified_payload or result.original_payload,
            "pii_found": pii_found,
            "processing_time_ms": round(processing_time_ms, 2),
        }
    
    def redact_text(
        self,
        text: str,
        pii_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Redact PII from text.
        
        Args:
            text: The text to redact.
            pii_types: Optional list of PII types to filter. If None, detects all.
            
        Returns:
            Dictionary with original and redacted text.
        """
        start_time = time.time()
        
        result = self._redactor.redact_text(text)
        matches = result.matches
        
        if pii_types:
            type_set = set(pii_types)
            matches = [m for m in matches if m.pii_type.value in type_set]
            if matches:
                redactor_filtered = PIIRedactor(
                    enabled_types=[PIIType(t) for t in pii_types if t in [pt.value for pt in PIIType]]
                )
                result = redactor_filtered.redact_text(text)
                redacted = result.redacted_text
            else:
                redacted = text
        else:
            redacted = result.redacted_text
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return {
            "original": text,
            "redacted": redacted,
            "matches": [
                {
                    "type": m.pii_type.value,
                    "start": m.start,
                    "end": m.end,
                    "text": m.original,
                }
                for m in matches
            ],
            "processing_time_ms": round(processing_time_ms, 2),
        }
    
    def scan_content(
        self,
        content: str,
        filename: str = "config.json",
    ) -> dict[str, Any]:
        """
        Scan configuration content for security issues.
        
        Args:
            content: The configuration content to scan.
            filename: The filename to use for the scan (affects rule matching).
            
        Returns:
            Dictionary with scan findings and summary.
        """
        start_time = time.time()
        
        findings: list[ScanFinding] = []
        for rule in self.scanner.rules:
            try:
                rule_findings = rule.check(filename, content)
                findings.extend(rule_findings)
            except Exception:
                pass
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        summary = {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity.value == "critical"),
            "high": sum(1 for f in findings if f.severity.value == "high"),
            "medium": sum(1 for f in findings if f.severity.value == "medium"),
            "low": sum(1 for f in findings if f.severity.value == "low"),
            "info": sum(1 for f in findings if f.severity.value == "info"),
        }
        
        return {
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity.value,
                    "message": f.title,
                    "description": f.description,
                    "line": f.line_number,
                    "file_path": f.file_path,
                }
                for f in findings
            ],
            "summary": summary,
            "processing_time_ms": round(processing_time_ms, 2),
        }
    
    def list_policies(self) -> list[dict[str, Any]]:
        """
        List all available policies in the engine.
        
        Returns:
            List of policy information dictionaries.
        """
        policies = []
        
        for name, policy in self.engine._policies.items():
            policies.append({
                "name": name,
                "enabled": policy.enabled,
                "priority": policy.priority,
                "rules_count": len(policy.rules),
            })
        
        return policies
