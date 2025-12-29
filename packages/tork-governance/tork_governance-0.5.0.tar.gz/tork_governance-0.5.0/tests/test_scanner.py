"""
Tests for MCP Security Scanner.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tork.scanner import (
    MCPScanner,
    ScanSeverity,
    ScanFinding,
    ScanResult,
    SecurityRule,
    get_all_mcp_rules,
)
from tork.scanner.mcp_rules import (
    MCP001HardcodedSecrets,
    MCP002NoAuthentication,
    MCP003OverlyPermissiveCORS,
    MCP004DebugModeEnabled,
    MCP005InsecureTransport,
    MCP006MissingRateLimiting,
    MCP007VerboseErrors,
    MCP008NoInputValidation,
    MCP009PrivilegedToolAccess,
    MCP010MissingAuditLogging,
)


class TestScanModels:
    """Tests for scan models."""
    
    def test_scan_severity_enum(self):
        """Test ScanSeverity enum values."""
        assert ScanSeverity.CRITICAL.value == "critical"
        assert ScanSeverity.HIGH.value == "high"
        assert ScanSeverity.MEDIUM.value == "medium"
        assert ScanSeverity.LOW.value == "low"
        assert ScanSeverity.INFO.value == "info"
    
    def test_scan_finding_model(self):
        """Test ScanFinding creation."""
        finding = ScanFinding(
            rule_id="MCP001",
            severity=ScanSeverity.CRITICAL,
            title="Test Finding",
            description="Test description",
            file_path="/test/file.json",
            line_number=10,
            recommendation="Fix it",
        )
        
        assert finding.rule_id == "MCP001"
        assert finding.severity == ScanSeverity.CRITICAL
        assert finding.line_number == 10
    
    def test_scan_result_compute_summary(self):
        """Test ScanResult summary computation."""
        findings = [
            ScanFinding(
                rule_id="MCP001",
                severity=ScanSeverity.CRITICAL,
                title="Critical Issue",
                description="Desc",
                file_path="/test.json",
                recommendation="Fix",
            ),
            ScanFinding(
                rule_id="MCP002",
                severity=ScanSeverity.HIGH,
                title="High Issue",
                description="Desc",
                file_path="/test.json",
                recommendation="Fix",
            ),
            ScanFinding(
                rule_id="MCP003",
                severity=ScanSeverity.CRITICAL,
                title="Another Critical",
                description="Desc",
                file_path="/test.json",
                recommendation="Fix",
            ),
        ]
        
        result = ScanResult(findings=findings, files_scanned=1)
        result.compute_summary()
        
        assert result.summary["critical"] == 2
        assert result.summary["high"] == 1
        assert result.summary["medium"] == 0
    
    def test_scan_result_has_critical_or_high(self):
        """Test has_critical_or_high property."""
        critical_finding = ScanFinding(
            rule_id="MCP001",
            severity=ScanSeverity.CRITICAL,
            title="Critical",
            description="Desc",
            file_path="/test.json",
            recommendation="Fix",
        )
        
        low_finding = ScanFinding(
            rule_id="MCP010",
            severity=ScanSeverity.LOW,
            title="Low",
            description="Desc",
            file_path="/test.json",
            recommendation="Fix",
        )
        
        result_with_critical = ScanResult(findings=[critical_finding])
        result_low_only = ScanResult(findings=[low_finding])
        
        assert result_with_critical.has_critical_or_high is True
        assert result_low_only.has_critical_or_high is False


class TestMCPRules:
    """Tests for individual MCP security rules."""
    
    def test_mcp001_detects_stripe_key(self):
        """Test MCP001 detects Stripe API keys."""
        rule = MCP001HardcodedSecrets()
        content = 'api_key: "sk_test_FAKEKEYFORTESTINGONLY12345"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP001"
        assert "Stripe" in findings[0].recommendation
    
    def test_mcp001_detects_github_token(self):
        """Test MCP001 detects GitHub tokens."""
        rule = MCP001HardcodedSecrets()
        content = 'token: "ghp_TESTONLYxxxxxxxxxxxxxxxxxxxxxxxx1234"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert "GitHub" in findings[0].recommendation
    
    def test_mcp001_ignores_env_vars(self):
        """Test MCP001 ignores environment variable references."""
        rule = MCP001HardcodedSecrets()
        content = 'api_key: "${API_KEY}"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0
    
    def test_mcp001_detects_aws_key(self):
        """Test MCP001 detects AWS access keys."""
        rule = MCP001HardcodedSecrets()
        content = 'access_key: "AKIAIOSFODNN7EXAMPLE"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert "AWS" in findings[0].recommendation
    
    def test_mcp001_detects_jwt(self):
        """Test MCP001 detects JWT tokens."""
        rule = MCP001HardcodedSecrets()
        content = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert "JWT" in findings[0].recommendation
    
    def test_mcp002_detects_no_auth(self):
        """Test MCP002 detects disabled authentication."""
        rule = MCP002NoAuthentication()
        content = 'authentication: "none"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP002"
    
    def test_mcp002_detects_anonymous_access(self):
        """Test MCP002 detects anonymous access enabled."""
        rule = MCP002NoAuthentication()
        content = 'anonymous_access: true'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
    
    def test_mcp003_detects_wildcard_cors(self):
        """Test MCP003 detects wildcard CORS origin."""
        rule = MCP003OverlyPermissiveCORS()
        content = 'cors_origin: "*"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP003"
    
    def test_mcp003_detects_allow_origin_wildcard(self):
        """Test MCP003 detects Access-Control-Allow-Origin wildcard."""
        rule = MCP003OverlyPermissiveCORS()
        content = 'Access-Control-Allow-Origin: *'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
    
    def test_mcp004_detects_debug_mode(self):
        """Test MCP004 detects debug mode enabled."""
        rule = MCP004DebugModeEnabled()
        content = 'debug: true'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP004"
    
    def test_mcp004_detects_debug_mode_enabled(self):
        """Test MCP004 detects debug_mode: enabled."""
        rule = MCP004DebugModeEnabled()
        content = 'debug_mode: enabled'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
    
    def test_mcp005_detects_http_url(self):
        """Test MCP005 detects HTTP URLs."""
        rule = MCP005InsecureTransport()
        content = 'endpoint: "http://api.example.com/v1"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP005"
    
    def test_mcp005_allows_localhost(self):
        """Test MCP005 allows localhost HTTP."""
        rule = MCP005InsecureTransport()
        content = 'url: "http://localhost:8080"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0
    
    def test_mcp005_detects_ssl_disabled(self):
        """Test MCP005 detects SSL disabled."""
        rule = MCP005InsecureTransport()
        content = 'ssl: false'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
    
    def test_mcp006_detects_missing_rate_limit(self):
        """Test MCP006 detects missing rate limiting."""
        rule = MCP006MissingRateLimiting()
        content = '{"server": {"port": 8080}, "api": {"version": "v1"}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP006"
    
    def test_mcp006_accepts_rate_limit_config(self):
        """Test MCP006 accepts rate_limit configuration."""
        rule = MCP006MissingRateLimiting()
        content = '{"server": {"port": 8080}, "rate_limit": {"requests_per_minute": 100}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0
    
    def test_mcp007_detects_verbose_errors(self):
        """Test MCP007 detects verbose error configuration."""
        rule = MCP007VerboseErrors()
        content = 'show_stack_trace: true'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP007"
    
    def test_mcp007_detects_error_details(self):
        """Test MCP007 detects error_details: full."""
        rule = MCP007VerboseErrors()
        content = 'error_details: "full"'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
    
    def test_mcp008_detects_missing_validation(self):
        """Test MCP008 detects missing input validation for tools."""
        rule = MCP008NoInputValidation()
        content = '{"tool": {"name": "file_reader", "description": "Reads files"}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP008"
    
    def test_mcp008_accepts_schema_defined(self):
        """Test MCP008 accepts when schema is defined."""
        rule = MCP008NoInputValidation()
        content = '{"tool": {"name": "file_reader", "input_schema": {"type": "object"}}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0
    
    def test_mcp009_detects_shell_access(self):
        """Test MCP009 detects shell access without restrictions."""
        rule = MCP009PrivilegedToolAccess()
        content = '{"tools": [{"name": "shell", "command": "bash"}]}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP009"
    
    def test_mcp009_accepts_restricted_access(self):
        """Test MCP009 accepts when restrictions are defined."""
        rule = MCP009PrivilegedToolAccess()
        content = '{"tools": [{"name": "shell", "command": "bash"}], "permissions": {"restricted": true}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0
    
    def test_mcp010_detects_missing_audit_logging(self):
        """Test MCP010 detects missing audit logging."""
        rule = MCP010MissingAuditLogging()
        content = '{"server": {"port": 8080}, "database": {"host": "localhost"}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 1
        assert findings[0].rule_id == "MCP010"
    
    def test_mcp010_accepts_logging_config(self):
        """Test MCP010 accepts logging configuration."""
        rule = MCP010MissingAuditLogging()
        content = '{"server": {"port": 8080}, "logging": {"level": "INFO"}}'
        findings = rule.check("/test.json", content)
        
        assert len(findings) == 0


class TestMCPScanner:
    """Tests for MCPScanner class."""
    
    def test_scanner_initialization_default_rules(self):
        """Test scanner initializes with default rules."""
        scanner = MCPScanner()
        
        assert len(scanner.rules) == 10
    
    def test_scanner_initialization_custom_rules(self):
        """Test scanner with custom rules."""
        rules = [MCP001HardcodedSecrets(), MCP002NoAuthentication()]
        scanner = MCPScanner(rules=rules)
        
        assert len(scanner.rules) == 2
    
    def test_scan_file(self):
        """Test scanning a single file."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            f.write('{"api_key": "sk_test_FAKEKEYFORTESTINGONLY12345", "debug": true}')
            f.flush()
            
            scanner = MCPScanner()
            findings = scanner.scan_file(f.name)
            
            # Should detect hardcoded secret and debug mode
            assert len(findings) >= 2
            rule_ids = [f.rule_id for f in findings]
            assert "MCP001" in rule_ids
            assert "MCP004" in rule_ids
    
    def test_scan_file_not_found(self):
        """Test scanning non-existent file."""
        scanner = MCPScanner()
        findings = scanner.scan_file("/nonexistent/file.json")
        
        assert len(findings) == 0
    
    def test_scan_directory(self):
        """Test scanning a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            config1 = Path(tmpdir) / "config.json"
            config1.write_text('{"debug": true}')
            
            config2 = Path(tmpdir) / "mcp.config.yaml"
            config2.write_text('cors_origin: "*"')
            
            scanner = MCPScanner()
            result = scanner.scan_directory(tmpdir)
            
            assert result.files_scanned == 2
            assert len(result.findings) >= 2
            
            rule_ids = [f.rule_id for f in result.findings]
            assert "MCP004" in rule_ids  # debug mode
            assert "MCP003" in rule_ids  # CORS wildcard
    
    def test_scan_directory_not_found(self):
        """Test scanning non-existent directory."""
        scanner = MCPScanner()
        result = scanner.scan_directory("/nonexistent/directory")
        
        assert result.files_scanned == 0
        assert len(result.findings) == 0
    
    def test_scan_directory_with_patterns(self):
        """Test scanning with custom patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            json_file = Path(tmpdir) / "config.json"
            json_file.write_text('{"debug": true}')
            
            txt_file = Path(tmpdir) / "config.txt"
            txt_file.write_text('debug: true')
            
            scanner = MCPScanner()
            
            # Only scan JSON files
            result = scanner.scan_directory(tmpdir, patterns=["*.json"])
            
            assert result.files_scanned == 1
    
    def test_get_all_mcp_rules(self):
        """Test get_all_mcp_rules function."""
        rules = get_all_mcp_rules()
        
        assert len(rules) == 10
        
        rule_ids = [r.id for r in rules]
        expected_ids = [f"MCP{str(i).zfill(3)}" for i in range(1, 11)]
        
        for expected_id in expected_ids:
            assert expected_id in rule_ids


class TestOutputFormats:
    """Tests for output format handling."""
    
    def test_scan_result_json_serializable(self):
        """Test that ScanResult can be serialized to JSON."""
        findings = [
            ScanFinding(
                rule_id="MCP001",
                severity=ScanSeverity.CRITICAL,
                title="Test",
                description="Desc",
                file_path="/test.json",
                line_number=1,
                recommendation="Fix",
            )
        ]
        
        result = ScanResult(
            findings=findings,
            files_scanned=1,
            scan_duration=0.5,
        )
        result.compute_summary()
        
        # Should be JSON serializable
        json_output = result.model_dump_json()
        parsed = json.loads(json_output)
        
        assert parsed["files_scanned"] == 1
        assert len(parsed["findings"]) == 1
