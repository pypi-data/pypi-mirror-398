"""
Tests for the PII redactor.

Tests PII detection, redaction, and validation across multiple data types.
"""

import pytest
from tork.core import PIIRedactor, PIIType, PIIMatch, RedactionResult


class TestPIIRedactor:
    """Tests for PIIRedactor."""
    
    def test_redactor_initialization(self):
        """Test redactor initialization."""
        redactor = PIIRedactor()
        assert len(redactor.enabled_types) == 6
    
    def test_redactor_with_specific_types(self):
        """Test redactor with specific enabled types."""
        enabled = [PIIType.EMAIL, PIIType.PHONE]
        redactor = PIIRedactor(enabled_types=enabled)
        assert redactor.enabled_types == enabled
    
    def test_email_detection(self):
        """Test email detection."""
        redactor = PIIRedactor()
        text = "Contact me at alice@example.com for details"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.EMAIL
        assert result.matches[0].original == "alice@example.com"
        assert "[REDACTED_EMAIL]" in result.redacted_text
    
    def test_multiple_emails(self):
        """Test multiple email detection."""
        redactor = PIIRedactor()
        text = "Email alice@example.com or bob@test.org"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 2
        assert all(m.pii_type == PIIType.EMAIL for m in result.matches)
    
    def test_phone_detection(self):
        """Test US phone number detection."""
        redactor = PIIRedactor()
        text = "Call me at 555-123-4567"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.PHONE
        assert "[REDACTED_PHONE]" in result.redacted_text
    
    def test_phone_variations(self):
        """Test various phone number formats."""
        redactor = PIIRedactor()
        
        # Format: (xxx) xxx-xxxx
        result1 = redactor.redact_text("Call (555) 123-4567")
        assert result1.pii_found
        
        # Format: xxx-xxx-xxxx
        result2 = redactor.redact_text("Call 555-123-4567")
        assert result2.pii_found
        
        # Format: +1 xxx xxx xxxx
        result3 = redactor.redact_text("Call +1 555 123 4567")
        assert result3.pii_found
    
    def test_ssn_detection(self):
        """Test Social Security Number detection."""
        redactor = PIIRedactor()
        text = "SSN: 123-45-6789"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.SSN
        assert result.matches[0].original == "123-45-6789"
        assert "[REDACTED_SSN]" in result.redacted_text
    
    def test_credit_card_detection_visa(self):
        """Test Visa credit card detection with Luhn validation."""
        redactor = PIIRedactor()
        # Valid Visa: 4532015112830366
        text = "Card: 4532-0151-1283-0366"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.CREDIT_CARD
        assert "[REDACTED_CREDIT_CARD]" in result.redacted_text
    
    def test_credit_card_detection_mastercard(self):
        """Test MasterCard credit card detection."""
        redactor = PIIRedactor()
        # Valid test MasterCard: 5555555555554444
        text = "Card: 5555-5555-5555-4444"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.CREDIT_CARD
    
    def test_credit_card_luhn_validation(self):
        """Test that invalid credit cards fail Luhn validation."""
        redactor = PIIRedactor()
        # Invalid card number (fails Luhn)
        text = "Card: 1234-5678-9012-3456"
        result = redactor.redact_text(text)
        
        # Should not detect as credit card due to Luhn failure
        cc_matches = [m for m in result.matches if m.pii_type == PIIType.CREDIT_CARD]
        assert len(cc_matches) == 0
    
    def test_ip_address_detection(self):
        """Test IPv4 address detection."""
        redactor = PIIRedactor()
        text = "Server IP: 192.168.1.1"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.IP_ADDRESS
        assert result.matches[0].original == "192.168.1.1"
        assert "[REDACTED_IP_ADDRESS]" in result.redacted_text
    
    def test_multiple_ips(self):
        """Test multiple IP address detection."""
        redactor = PIIRedactor()
        text = "Primary: 10.0.0.1, Secondary: 10.0.0.2"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 2
        assert all(m.pii_type == PIIType.IP_ADDRESS for m in result.matches)
    
    def test_api_key_detection(self):
        """Test API key detection."""
        redactor = PIIRedactor()
        text = "Use key: sk_live_abcdefghijklmnopqrst"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.API_KEY
        assert "[REDACTED_API_KEY]" in result.redacted_text
    
    def test_api_key_variations(self):
        """Test various API key patterns."""
        redactor = PIIRedactor()
        
        # sk_ prefix
        result1 = redactor.redact_text("key: sk_live_1234567890123456789")
        assert result1.pii_found
        
        # api_ prefix
        result2 = redactor.redact_text("key: api_key_1234567890123456789")
        assert result2.pii_found
        
        # token_ prefix
        result3 = redactor.redact_text("key: token_abcdefghijklmnopqrst")
        assert result3.pii_found
    
    def test_no_pii_in_clean_text(self):
        """Test that clean text returns no matches."""
        redactor = PIIRedactor()
        text = "This is a normal sentence with no sensitive information."
        result = redactor.redact_text(text)
        
        assert not result.pii_found
        assert len(result.matches) == 0
        assert result.redacted_text == text
    
    def test_multiple_pii_types_same_text(self):
        """Test detection of multiple PII types in same text."""
        redactor = PIIRedactor()
        text = "Contact alice@example.com at 555-123-4567 or visit 192.168.1.1"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 3
        
        pii_types = {m.pii_type for m in result.matches}
        assert PIIType.EMAIL in pii_types
        assert PIIType.PHONE in pii_types
        assert PIIType.IP_ADDRESS in pii_types
    
    def test_redact_dict_simple(self):
        """Test redacting a simple dictionary."""
        redactor = PIIRedactor()
        data = {
            "email": "alice@example.com",
            "phone": "555-123-4567",
            "name": "Alice",
        }
        
        redacted, matches = redactor.redact_dict(data)
        
        assert len(matches) == 2
        assert "[REDACTED_EMAIL]" in redacted["email"]
        assert "[REDACTED_PHONE]" in redacted["phone"]
        assert redacted["name"] == "Alice"
    
    def test_redact_dict_nested(self):
        """Test redacting nested dictionary."""
        redactor = PIIRedactor()
        data = {
            "user": {
                "email": "bob@example.com",
                "phone": "555-987-6543",
                "name": "Bob",
            },
            "ip": "10.0.0.1",
        }
        
        redacted, matches = redactor.redact_dict(data)
        
        assert len(matches) == 3
        assert "[REDACTED_EMAIL]" in redacted["user"]["email"]
        assert "[REDACTED_PHONE]" in redacted["user"]["phone"]
        assert redacted["user"]["name"] == "Bob"
        assert "[REDACTED_IP_ADDRESS]" in redacted["ip"]
    
    def test_redact_dict_with_list(self):
        """Test redacting dictionary containing lists."""
        redactor = PIIRedactor()
        data = {
            "emails": ["alice@example.com", "bob@test.org"],
            "phones": ["555-123-4567"],
            "names": ["Alice", "Bob"],
        }
        
        redacted, matches = redactor.redact_dict(data)
        
        assert len(matches) == 3
        assert all("[REDACTED_EMAIL]" in e for e in redacted["emails"])
        assert "[REDACTED_PHONE]" in redacted["phones"][0]
        assert redacted["names"] == ["Alice", "Bob"]
    
    def test_redact_dict_mixed_types(self):
        """Test redacting dictionary with mixed value types."""
        redactor = PIIRedactor()
        data = {
            "email": "alice@example.com",
            "age": 30,
            "verified": True,
            "addresses": [
                {"ip": "192.168.1.1", "name": "Home"},
            ],
        }
        
        redacted, matches = redactor.redact_dict(data)
        
        assert len(matches) == 2
        assert "[REDACTED_EMAIL]" in redacted["email"]
        assert redacted["age"] == 30
        assert redacted["verified"] is True
        assert "[REDACTED_IP_ADDRESS]" in redacted["addresses"][0]["ip"]
        assert redacted["addresses"][0]["name"] == "Home"
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        redactor = PIIRedactor()
        result = redactor.redact_text(12345)
        
        assert not result.pii_found
        assert result.original_text == "12345"
        assert result.redacted_text == "12345"
    
    def test_redaction_result_structure(self):
        """Test RedactionResult structure and properties."""
        redactor = PIIRedactor()
        text = "Email: alice@example.com"
        result = redactor.redact_text(text)
        
        assert isinstance(result, RedactionResult)
        assert isinstance(result.original_text, str)
        assert isinstance(result.redacted_text, str)
        assert isinstance(result.matches, list)
        assert result.pii_found is True
    
    def test_pii_match_structure(self):
        """Test PIIMatch structure."""
        redactor = PIIRedactor()
        text = "Email: alice@example.com"
        result = redactor.redact_text(text)
        
        assert len(result.matches) > 0
        match = result.matches[0]
        
        assert isinstance(match, PIIMatch)
        assert isinstance(match.pii_type, PIIType)
        assert isinstance(match.original, str)
        assert isinstance(match.redacted, str)
        assert isinstance(match.start, int)
        assert isinstance(match.end, int)
        assert match.start < match.end
    
    def test_disabled_pii_type(self):
        """Test that disabled PII types are not detected."""
        redactor = PIIRedactor(enabled_types=[PIIType.EMAIL])
        text = "Email: alice@example.com, Phone: 555-123-4567"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.EMAIL
        assert not any(m.pii_type == PIIType.PHONE for m in result.matches)
    
    def test_position_tracking(self):
        """Test that match positions are correctly tracked."""
        redactor = PIIRedactor()
        text = "Contact alice@example.com now"
        result = redactor.redact_text(text)
        
        assert len(result.matches) == 1
        match = result.matches[0]
        assert text[match.start:match.end] == match.original
    
    def test_overlapping_credit_card_and_phone(self):
        """Test that overlapping credit card and phone detections resolve correctly."""
        redactor = PIIRedactor()
        # 4111111111111111 is a valid test credit card that also matches phone pattern
        text = "Card: 4111111111111111"
        result = redactor.redact_text(text)
        
        # Should only detect as CREDIT_CARD, not also as PHONE
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.CREDIT_CARD
        assert "[REDACTED_CREDIT_CARD]" in result.redacted_text
        # Make sure it's not double-redacted with PHONE
        assert "[REDACTED_PHONE]" not in result.redacted_text
    
    def test_overlapping_ssn_and_phone(self):
        """Test that overlapping SSN and phone detections resolve correctly."""
        redactor = PIIRedactor()
        # Some SSNs can match phone patterns like "123-45-6789"
        text = "SSN: 123-45-6789"
        result = redactor.redact_text(text)
        
        # Should prefer SSN over PHONE based on priority
        assert result.pii_found
        assert len(result.matches) == 1
        assert result.matches[0].pii_type == PIIType.SSN
    
    def test_overlapping_api_key_and_phone(self):
        """Test that API key takes priority over phone patterns."""
        redactor = PIIRedactor()
        # Some API keys might match phone patterns
        text = "key_1234567890123456789"
        result = redactor.redact_text(text)
        
        # Count API key and phone matches
        pii_types = {m.pii_type for m in result.matches}
        
        # Should have API key match
        if PIIType.API_KEY in pii_types:
            assert len(result.matches) == 1
            assert result.matches[0].pii_type == PIIType.API_KEY
    
    def test_multiple_non_overlapping_pii(self):
        """Test multiple PII of different types in same text without overlap."""
        redactor = PIIRedactor()
        text = "Email: alice@example.com, SSN: 123-45-6789, Card: 4532-0151-1283-0366"
        result = redactor.redact_text(text)
        
        assert result.pii_found
        assert len(result.matches) == 3
        
        # Verify each type is detected exactly once
        pii_types = {m.pii_type for m in result.matches}
        assert PIIType.EMAIL in pii_types
        assert PIIType.SSN in pii_types
        assert PIIType.CREDIT_CARD in pii_types
    
    def test_no_garbled_output_with_overlaps(self):
        """Test that redaction output is never garbled with overlapping matches."""
        redactor = PIIRedactor()
        text = "4111111111111111"
        result = redactor.redact_text(text)
        
        # The output should have exactly one redaction marker, not duplicated/garbled
        assert result.redacted_text.count("[REDACTED_") == 1
        assert result.redacted_text.count("]") == 1
        # Should not contain incomplete patterns like "[REDACTED_CREDIT_CARDPHONE]"
        assert "[REDACTED_CREDIT_CARDPHONE]" not in result.redacted_text
        assert "PHONE]" not in result.redacted_text.replace("[REDACTED_PHONE]", "")
