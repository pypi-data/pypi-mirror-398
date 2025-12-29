"""
Security scanning rules and models.

Provides base classes and data models for security scanning.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ScanSeverity(str, Enum):
    """Severity levels for security findings."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanFinding(BaseModel):
    """A security finding from scanning."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    severity: ScanSeverity = Field(..., description="Severity level")
    title: str = Field(..., description="Short title of the finding")
    description: str = Field(..., description="Detailed description")
    file_path: str = Field(..., description="Path to the affected file")
    line_number: Optional[int] = Field(default=None, description="Line number if applicable")
    recommendation: str = Field(..., description="Recommended remediation")


class ScanResult(BaseModel):
    """Result of a security scan."""
    
    findings: list[ScanFinding] = Field(default_factory=list, description="List of findings")
    files_scanned: int = Field(default=0, description="Number of files scanned")
    scan_duration: float = Field(default=0.0, description="Scan duration in seconds")
    summary: dict[str, int] = Field(default_factory=dict, description="Counts by severity")
    
    def compute_summary(self) -> None:
        """Compute the summary counts from findings."""
        self.summary = {
            ScanSeverity.CRITICAL.value: 0,
            ScanSeverity.HIGH.value: 0,
            ScanSeverity.MEDIUM.value: 0,
            ScanSeverity.LOW.value: 0,
            ScanSeverity.INFO.value: 0,
        }
        for finding in self.findings:
            self.summary[finding.severity.value] += 1
    
    @property
    def has_critical_or_high(self) -> bool:
        """Check if there are critical or high severity findings."""
        return any(
            f.severity in (ScanSeverity.CRITICAL, ScanSeverity.HIGH)
            for f in self.findings
        )


class SecurityRule(ABC):
    """Base class for security rules."""
    
    id: str
    severity: ScanSeverity
    title: str
    description: str
    
    @abstractmethod
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        """
        Check file content for security issues.
        
        Args:
            file_path: Path to the file being scanned.
            content: Content of the file.
            
        Returns:
            List of findings detected by this rule.
        """
        pass
    
    def create_finding(
        self,
        file_path: str,
        line_number: Optional[int] = None,
        recommendation: Optional[str] = None,
    ) -> ScanFinding:
        """Create a finding for this rule."""
        return ScanFinding(
            rule_id=self.id,
            severity=self.severity,
            title=self.title,
            description=self.description,
            file_path=file_path,
            line_number=line_number,
            recommendation=recommendation or f"Review and fix: {self.title}",
        )
