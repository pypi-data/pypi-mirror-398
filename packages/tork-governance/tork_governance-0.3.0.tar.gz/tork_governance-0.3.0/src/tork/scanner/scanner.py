"""
MCP Security Scanner.

Provides the main scanner class for detecting security issues in MCP configurations.
"""

import time
from pathlib import Path
from typing import Optional
import structlog

from tork.scanner.rules import SecurityRule, ScanFinding, ScanResult, ScanSeverity
from tork.scanner.mcp_rules import get_all_mcp_rules

logger = structlog.get_logger(__name__)


class MCPScanner:
    """
    Security scanner for MCP configurations.
    
    Scans files and directories for security vulnerabilities
    based on configurable rules.
    """
    
    DEFAULT_PATTERNS = ["*.json", "*.yaml", "*.yml", "*.toml", "mcp.config.*", "*.config", "config.*"]
    
    def __init__(self, rules: Optional[list[SecurityRule]] = None) -> None:
        """
        Initialize the MCP scanner.
        
        Args:
            rules: List of security rules to use. Defaults to all MCP rules.
        """
        if rules is None:
            self.rules = get_all_mcp_rules()
        else:
            self.rules = rules
        
        logger.info("MCPScanner initialized", rule_count=len(self.rules))
    
    def scan_file(self, file_path: str) -> list[ScanFinding]:
        """
        Scan a single file for security issues.
        
        Args:
            file_path: Path to the file to scan.
            
        Returns:
            List of findings from all rules.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning("File not found", file_path=file_path)
            return []
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error("Failed to read file", file_path=file_path, error=str(e))
            return []
        
        findings: list[ScanFinding] = []
        
        for rule in self.rules:
            try:
                rule_findings = rule.check(file_path, content)
                findings.extend(rule_findings)
            except Exception as e:
                logger.error(
                    "Rule check failed",
                    rule_id=rule.id,
                    file_path=file_path,
                    error=str(e),
                )
        
        logger.debug("File scanned", file_path=file_path, findings=len(findings))
        
        return findings
    
    def scan_directory(
        self,
        dir_path: str,
        patterns: Optional[list[str]] = None,
    ) -> ScanResult:
        """
        Scan a directory for security issues.
        
        Args:
            dir_path: Path to the directory to scan.
            patterns: File patterns to match. Defaults to config file patterns.
            
        Returns:
            ScanResult with all findings and summary.
        """
        start_time = time.time()
        
        if patterns is None:
            patterns = self.DEFAULT_PATTERNS
        
        path = Path(dir_path)
        
        if not path.exists():
            logger.warning("Directory not found", dir_path=dir_path)
            return ScanResult(
                findings=[],
                files_scanned=0,
                scan_duration=time.time() - start_time,
            )
        
        all_findings: list[ScanFinding] = []
        files_scanned = 0
        
        # Collect all matching files
        matched_files: set[Path] = set()
        for pattern in patterns:
            matched_files.update(path.rglob(pattern))
        
        # Scan each file
        for file_path in sorted(matched_files):
            if file_path.is_file():
                findings = self.scan_file(str(file_path))
                all_findings.extend(findings)
                files_scanned += 1
        
        duration = time.time() - start_time
        
        result = ScanResult(
            findings=all_findings,
            files_scanned=files_scanned,
            scan_duration=duration,
        )
        result.compute_summary()
        
        logger.info(
            "Directory scan complete",
            dir_path=dir_path,
            files_scanned=files_scanned,
            findings=len(all_findings),
            duration=f"{duration:.2f}s",
        )
        
        return result
    
    def get_rules_by_severity(self, severity: ScanSeverity) -> list[SecurityRule]:
        """Get all rules of a specific severity or higher."""
        severity_order = [
            ScanSeverity.CRITICAL,
            ScanSeverity.HIGH,
            ScanSeverity.MEDIUM,
            ScanSeverity.LOW,
            ScanSeverity.INFO,
        ]
        
        min_index = severity_order.index(severity)
        valid_severities = set(severity_order[:min_index + 1])
        
        return [rule for rule in self.rules if rule.severity in valid_severities]
