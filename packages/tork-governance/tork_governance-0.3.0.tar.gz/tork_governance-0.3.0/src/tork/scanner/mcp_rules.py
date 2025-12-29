"""
MCP Security Rules.

Provides 10 security rules for scanning MCP configurations.
"""

import re
from tork.scanner.rules import SecurityRule, ScanFinding, ScanSeverity


class MCP001HardcodedSecrets(SecurityRule):
    """Detect hardcoded secrets in configuration files."""
    
    id = "MCP001"
    severity = ScanSeverity.CRITICAL
    title = "Hardcoded Secrets Detected"
    description = "API keys, tokens, or passwords are hardcoded in the configuration file."
    
    SECRET_PATTERNS = [
        (r'(?:sk_live_|sk_test_|pk_live_|pk_test_)[a-zA-Z0-9]{20,}', "Stripe key"),
        (r'(?:ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36,}', "GitHub token"),
        (r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}', "Slack token"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        (r'AIza[0-9A-Za-z\-_]{35}', "Google API key"),
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "JWT token"),
        (r'["\']?password["\']?\s*[:=]\s*["\'](?![\$\{])[^"\']{8,}["\']', "Hardcoded password"),
        (r'["\']?(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\'](?![\$\{])(?:[a-zA-Z0-9_\-]{32,})["\']', "API key"),
    ]
    
    ENV_VAR_PATTERN = r'\$\{?\w+\}?|\%\w+\%|process\.env\.'
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip lines that reference environment variables
            if re.search(self.ENV_VAR_PATTERN, line):
                continue
            
            for pattern, secret_type in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=f"Remove {secret_type} from code. Use environment variables or a secrets manager.",
                    ))
                    break
        
        return findings


class MCP002NoAuthentication(SecurityRule):
    """Detect missing authentication configuration."""
    
    id = "MCP002"
    severity = ScanSeverity.HIGH
    title = "No Authentication Configured"
    description = "MCP server does not have authentication enabled or configured."
    
    AUTH_PATTERNS = [
        r'["\']?auth(?:entication)?["\']?\s*[:=]\s*["\']?(?:none|disabled|false)["\']?',
        r'["\']?require[_-]?auth["\']?\s*[:=]\s*["\']?false["\']?',
        r'["\']?anonymous[_-]?access["\']?\s*[:=]\s*["\']?(?:true|enabled)["\']?',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.AUTH_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Enable authentication. Configure API keys, OAuth, or other auth mechanisms.",
                    ))
                    break
        
        return findings


class MCP003OverlyPermissiveCORS(SecurityRule):
    """Detect overly permissive CORS settings."""
    
    id = "MCP003"
    severity = ScanSeverity.HIGH
    title = "Overly Permissive CORS Settings"
    description = "CORS is configured to allow all origins (*), which can expose the API to cross-origin attacks."
    
    CORS_PATTERNS = [
        r'["\']?(?:cors[_-]?)?origin[s]?["\']?\s*[:=]\s*["\']?\*["\']?',
        r'["\']?allow[_-]?origin[s]?["\']?\s*[:=]\s*["\']?\*["\']?',
        r'Access-Control-Allow-Origin["\']?\s*[:=]\s*["\']?\*["\']?',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.CORS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Restrict CORS origins to specific trusted domains instead of using '*'.",
                    ))
                    break
        
        return findings


class MCP004DebugModeEnabled(SecurityRule):
    """Detect debug mode enabled in production configuration."""
    
    id = "MCP004"
    severity = ScanSeverity.HIGH
    title = "Debug Mode Enabled"
    description = "Debug mode is enabled, which can expose sensitive information in production."
    
    DEBUG_PATTERNS = [
        r'["\']?debug["\']?\s*[:=]\s*["\']?true["\']?',
        r'["\']?debug[_-]?mode["\']?\s*[:=]\s*["\']?(?:true|enabled|on|1)["\']?',
        r'["\']?verbose["\']?\s*[:=]\s*["\']?true["\']?',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.DEBUG_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Disable debug mode in production configurations.",
                    ))
                    break
        
        return findings


class MCP005InsecureTransport(SecurityRule):
    """Detect insecure transport (HTTP instead of HTTPS)."""
    
    id = "MCP005"
    severity = ScanSeverity.MEDIUM
    title = "Insecure Transport Protocol"
    description = "Configuration uses HTTP instead of HTTPS, exposing data to interception."
    
    HTTP_PATTERNS = [
        r'["\']?(?:url|endpoint|host|server)["\']?\s*[:=]\s*["\']?http://[^"\'\s]+["\']?',
        r'["\']?https["\']?\s*[:=]\s*["\']?false["\']?',
        r'["\']?ssl["\']?\s*[:=]\s*["\']?(?:false|disabled)["\']?',
        r'["\']?tls["\']?\s*[:=]\s*["\']?(?:false|disabled)["\']?',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip localhost/127.0.0.1 as these are often intentionally HTTP
            if 'localhost' in line.lower() or '127.0.0.1' in line:
                continue
            
            for pattern in self.HTTP_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Use HTTPS for all external connections. Enable SSL/TLS.",
                    ))
                    break
        
        return findings


class MCP006MissingRateLimiting(SecurityRule):
    """Detect missing rate limiting configuration."""
    
    id = "MCP006"
    severity = ScanSeverity.MEDIUM
    title = "Missing Rate Limiting"
    description = "No rate limiting configuration detected, which can lead to abuse or DoS attacks."
    
    RATE_LIMIT_KEYWORDS = [
        'rate_limit', 'ratelimit', 'rate-limit',
        'throttle', 'throttling',
        'requests_per', 'max_requests',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        content_lower = content.lower()
        
        # Check if any rate limiting keywords exist
        has_rate_limit = any(keyword in content_lower for keyword in self.RATE_LIMIT_KEYWORDS)
        
        if not has_rate_limit and ('server' in content_lower or 'api' in content_lower):
            return [self.create_finding(
                file_path=file_path,
                recommendation="Implement rate limiting to protect against abuse and DoS attacks.",
            )]
        
        return []


class MCP007VerboseErrors(SecurityRule):
    """Detect verbose error message configuration."""
    
    id = "MCP007"
    severity = ScanSeverity.MEDIUM
    title = "Verbose Error Messages Exposed"
    description = "Configuration exposes detailed error messages which can leak sensitive information."
    
    VERBOSE_ERROR_PATTERNS = [
        r'["\']?(?:show|expose|include)[_-]?(?:stack[_-]?trace|errors?|exception)["\']?\s*[:=]\s*["\']?true["\']?',
        r'["\']?error[_-]?detail[s]?["\']?\s*[:=]\s*["\']?(?:full|verbose|all)["\']?',
        r'["\']?stack[_-]?trace["\']?\s*[:=]\s*["\']?true["\']?',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in self.VERBOSE_ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Disable verbose error messages in production. Log details server-side only.",
                    ))
                    break
        
        return findings


class MCP008NoInputValidation(SecurityRule):
    """Detect missing input validation schema."""
    
    id = "MCP008"
    severity = ScanSeverity.MEDIUM
    title = "No Input Validation Schema"
    description = "No input validation schema defined for tools, which can lead to injection attacks."
    
    VALIDATION_KEYWORDS = [
        'schema', 'validation', 'validate',
        'input_schema', 'inputschema',
        'parameters', 'param_schema',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        content_lower = content.lower()
        
        # Only check files that appear to define tools
        if 'tool' not in content_lower and 'function' not in content_lower:
            return []
        
        has_validation = any(keyword in content_lower for keyword in self.VALIDATION_KEYWORDS)
        
        if not has_validation:
            return [self.create_finding(
                file_path=file_path,
                recommendation="Define input validation schemas for all tools and functions.",
            )]
        
        return []


class MCP009PrivilegedToolAccess(SecurityRule):
    """Detect privileged tool access without restrictions."""
    
    id = "MCP009"
    severity = ScanSeverity.HIGH
    title = "Privileged Tool Access Without Restrictions"
    description = "Tools with privileged operations (file system, shell, network) lack access restrictions."
    
    PRIVILEGED_PATTERNS = [
        (r'["\']?(?:shell|exec|execute|command|cmd)["\']?', "shell execution"),
        (r'["\']?(?:file[_-]?system|fs|read[_-]?file|write[_-]?file)["\']?', "file system access"),
        (r'["\']?(?:sudo|root|admin|elevated)["\']?', "elevated privileges"),
        (r'["\']?(?:delete|remove|drop|truncate)[_-]?(?:all|database|table)?["\']?', "destructive operations"),
    ]
    
    RESTRICTION_KEYWORDS = [
        'restrict', 'permission', 'allow', 'deny',
        'authorized', 'capability', 'scope',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        findings = []
        content_lower = content.lower()
        
        has_restrictions = any(keyword in content_lower for keyword in self.RESTRICTION_KEYWORDS)
        
        if not has_restrictions:
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, access_type in self.PRIVILEGED_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(self.create_finding(
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=f"Add access restrictions for {access_type}. Define allowed operations and scope.",
                        ))
                        break
        
        return findings


class MCP010MissingAuditLogging(SecurityRule):
    """Detect missing audit logging configuration."""
    
    id = "MCP010"
    severity = ScanSeverity.LOW
    title = "Missing Audit Logging Configuration"
    description = "No audit logging configuration detected for tracking security-relevant events."
    
    AUDIT_KEYWORDS = [
        'audit', 'logging', 'log_level',
        'access_log', 'security_log',
        'event_log', 'trace',
    ]
    
    def check(self, file_path: str, content: str) -> list[ScanFinding]:
        content_lower = content.lower()
        
        has_audit = any(keyword in content_lower for keyword in self.AUDIT_KEYWORDS)
        
        if not has_audit and len(content) > 50:  # Only flag non-trivial files
            return [self.create_finding(
                file_path=file_path,
                recommendation="Configure audit logging to track security-relevant events and access patterns.",
            )]
        
        return []


def get_all_mcp_rules() -> list[SecurityRule]:
    """Get all MCP security rules."""
    return [
        MCP001HardcodedSecrets(),
        MCP002NoAuthentication(),
        MCP003OverlyPermissiveCORS(),
        MCP004DebugModeEnabled(),
        MCP005InsecureTransport(),
        MCP006MissingRateLimiting(),
        MCP007VerboseErrors(),
        MCP008NoInputValidation(),
        MCP009PrivilegedToolAccess(),
        MCP010MissingAuditLogging(),
    ]
