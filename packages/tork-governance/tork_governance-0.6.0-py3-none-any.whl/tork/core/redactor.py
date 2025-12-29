"""
PII (Personally Identifiable Information) redactor.

Detects and redacts sensitive information in text and data structures.
"""

from enum import Enum
from typing import Any, Optional
import re
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected and redacted."""
    
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"


class PIIMatch(BaseModel):
    """A match of PII in text."""
    
    pii_type: PIIType = Field(..., description="Type of PII detected")
    original: str = Field(..., description="Original detected text")
    redacted: str = Field(..., description="Redacted replacement text")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")


class RedactionResult(BaseModel):
    """Result of redacting text for PII."""
    
    original_text: str = Field(..., description="Original unmodified text")
    redacted_text: str = Field(..., description="Text with PII redacted")
    matches: list[PIIMatch] = Field(default_factory=list, description="List of PII matches found")
    
    @property
    def pii_found(self) -> bool:
        """Check if any PII was found."""
        return len(self.matches) > 0


class PIIRedactor:
    """Detects and redacts personally identifiable information."""
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'(?:\+1)?[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    IP_ADDRESS_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    API_KEY_PATTERN = r'\b(?:sk_|api_|key_|token_)[a-zA-Z0-9_]{20,}\b'
    CREDIT_CARD_PATTERN = r'\b(?:\d[\s-]*?){13,19}\b'
    
    def __init__(self, enabled_types: Optional[list[PIIType]] = None) -> None:
        """
        Initialize the PII redactor.
        
        Args:
            enabled_types: List of PII types to detect. Defaults to all types.
        """
        if enabled_types is None:
            self.enabled_types = list(PIIType)
        else:
            self.enabled_types = enabled_types
        
        logger.info("PIIRedactor initialized", enabled_types=[t.value for t in self.enabled_types])
    
    def redact_text(self, text: str) -> RedactionResult:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact.
            
        Returns:
            RedactionResult with redacted text and matches.
        """
        if not isinstance(text, str):
            return RedactionResult(
                original_text=str(text),
                redacted_text=str(text),
                matches=[],
            )
        
        matches: list[PIIMatch] = []
        redacted_text = text
        
        # Collect all matches
        all_matches = []
        
        if PIIType.EMAIL in self.enabled_types:
            all_matches.extend(
                (PIIType.EMAIL, start, end, match)
                for start, end, match in self._detect_email(text)
            )
        
        if PIIType.PHONE in self.enabled_types:
            all_matches.extend(
                (PIIType.PHONE, start, end, match)
                for start, end, match in self._detect_phone(text)
            )
        
        if PIIType.SSN in self.enabled_types:
            all_matches.extend(
                (PIIType.SSN, start, end, match)
                for start, end, match in self._detect_ssn(text)
            )
        
        if PIIType.CREDIT_CARD in self.enabled_types:
            all_matches.extend(
                (PIIType.CREDIT_CARD, start, end, match)
                for start, end, match in self._detect_credit_card(text)
            )
        
        if PIIType.IP_ADDRESS in self.enabled_types:
            all_matches.extend(
                (PIIType.IP_ADDRESS, start, end, match)
                for start, end, match in self._detect_ip_address(text)
            )
        
        if PIIType.API_KEY in self.enabled_types:
            all_matches.extend(
                (PIIType.API_KEY, start, end, match)
                for start, end, match in self._detect_api_key(text)
            )
        
        # Filter overlapping matches - keep only the best match
        all_matches = self._filter_overlapping_matches(all_matches)
        
        # Sort matches by position (reverse to avoid offset issues when replacing)
        all_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Apply redactions
        for pii_type, start, end, original in all_matches:
            redacted = f"[REDACTED_{pii_type.value.upper()}]"
            redacted_text = redacted_text[:start] + redacted + redacted_text[end:]
            
            matches.insert(
                0,
                PIIMatch(
                    pii_type=pii_type,
                    original=original,
                    redacted=redacted,
                    start=start,
                    end=end,
                ),
            )
        
        logger.info("Text redacted", pii_count=len(matches))
        
        return RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            matches=matches,
        )
    
    def redact_dict(self, data: dict[str, Any]) -> tuple[dict[str, Any], list[PIIMatch]]:
        """
        Recursively redact PII from dictionary values.
        
        Args:
            data: Dictionary to redact.
            
        Returns:
            Tuple of (redacted_dict, list_of_matches).
        """
        redacted = {}
        all_matches: list[PIIMatch] = []
        
        for key, value in data.items():
            if isinstance(value, str):
                result = self.redact_text(value)
                redacted[key] = result.redacted_text
                all_matches.extend(result.matches)
            elif isinstance(value, dict):
                redacted[key], matches = self.redact_dict(value)
                all_matches.extend(matches)
            elif isinstance(value, list):
                redacted[key] = []
                for item in value:
                    if isinstance(item, str):
                        result = self.redact_text(item)
                        redacted[key].append(result.redacted_text)
                        all_matches.extend(result.matches)
                    elif isinstance(item, dict):
                        redacted_item, matches = self.redact_dict(item)
                        redacted[key].append(redacted_item)
                        all_matches.extend(matches)
                    else:
                        redacted[key].append(item)
            else:
                redacted[key] = value
        
        logger.info("Dictionary redacted", pii_count=len(all_matches))
        
        return redacted, all_matches
    
    def _detect_email(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect email addresses in text.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.EMAIL_PATTERN, text):
            matches.append((match.start(), match.end(), match.group()))
        return matches
    
    def _detect_phone(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect US phone numbers in text.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.PHONE_PATTERN, text):
            matches.append((match.start(), match.end(), match.group()))
        return matches
    
    def _detect_ssn(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect Social Security Numbers in text.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.SSN_PATTERN, text):
            matches.append((match.start(), match.end(), match.group()))
        return matches
    
    def _detect_credit_card(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect credit card numbers in text with Luhn validation.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.CREDIT_CARD_PATTERN, text):
            # Remove spaces and dashes
            digits_only = re.sub(r'[\s-]', '', match.group())
            
            # Must be 13-19 digits
            if 13 <= len(digits_only) <= 19 and digits_only.isdigit():
                # Validate with Luhn algorithm
                if self._luhn_check(digits_only):
                    matches.append((match.start(), match.end(), match.group()))
        
        return matches
    
    def _detect_ip_address(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect IPv4 addresses in text.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.IP_ADDRESS_PATTERN, text):
            matches.append((match.start(), match.end(), match.group()))
        return matches
    
    def _detect_api_key(self, text: str) -> list[tuple[int, int, str]]:
        """
        Detect API keys in text.
        
        Returns:
            List of (start, end, matched_text) tuples.
        """
        matches = []
        for match in re.finditer(self.API_KEY_PATTERN, text):
            matches.append((match.start(), match.end(), match.group()))
        return matches
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """
        Validate a credit card number using the Luhn algorithm.
        
        Args:
            card_number: String of digits to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if not card_number.isdigit():
            return False
        
        digits = [int(d) for d in card_number]
        
        # Double every second digit from the right
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        # Sum all digits and check if divisible by 10
        return sum(digits) % 10 == 0
    
    @staticmethod
    def _filter_overlapping_matches(
        matches: list[tuple[PIIType, int, int, str]]
    ) -> list[tuple[PIIType, int, int, str]]:
        """
        Filter out overlapping matches, keeping only the best match.
        
        Priority order (higher = keep if overlap):
        1. CREDIT_CARD (most specific)
        2. SSN
        3. API_KEY
        4. PHONE
        5. IP_ADDRESS
        6. EMAIL (least specific)
        
        Args:
            matches: List of (pii_type, start, end, original) tuples.
            
        Returns:
            Filtered list with overlaps removed.
        """
        if not matches:
            return matches
        
        # Priority map (higher number = higher priority)
        priority_map = {
            PIIType.CREDIT_CARD: 6,
            PIIType.SSN: 5,
            PIIType.API_KEY: 4,
            PIIType.PHONE: 3,
            PIIType.IP_ADDRESS: 2,
            PIIType.EMAIL: 1,
        }
        
        # Sort by start position, then by priority (descending)
        sorted_matches = sorted(
            matches,
            key=lambda x: (x[1], -priority_map.get(x[0], 0))
        )
        
        filtered: list[tuple[PIIType, int, int, str]] = []
        
        for pii_type, start, end, original in sorted_matches:
            # Check if this match overlaps with any already filtered match
            overlaps = False
            for filtered_type, filtered_start, filtered_end, _ in filtered:
                # Check if ranges overlap
                if not (end <= filtered_start or start >= filtered_end):
                    overlaps = True
                    # Keep the one with higher priority
                    if priority_map.get(pii_type, 0) > priority_map.get(filtered_type, 0):
                        # Remove the lower priority match
                        filtered.remove((filtered_type, filtered_start, filtered_end, _))
                    break
            
            if not overlaps:
                filtered.append((pii_type, start, end, original))
        
        return filtered
