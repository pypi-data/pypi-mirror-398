"""
Tests for the compliance receipts system.
"""

import os
import tempfile
import shutil
from datetime import datetime, timedelta, timezone

import pytest

from tork.core.models import EvaluationRequest, EvaluationResult, PolicyDecision
from tork.compliance.receipts import PolicyReceipt, ReceiptGenerator
from tork.compliance.store import MemoryReceiptStore, FileReceiptStore


class TestReceiptGenerator:
    """Tests for ReceiptGenerator class."""
    
    def test_generate_receipt(self):
        """Test generating a receipt from evaluation result."""
        generator = ReceiptGenerator(signing_key="test-signing-key")
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="send_message",
            payload={"content": "Hello world"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="No violations",
            original_payload={"content": "Hello world"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request, policy_names=["default-policy"])
        
        assert receipt.receipt_id is not None
        assert receipt.agent_id == "agent-001"
        assert receipt.action == "send_message"
        assert receipt.decision == PolicyDecision.ALLOW
        assert receipt.policy_names == ["default-policy"]
        assert receipt.violations == []
        assert receipt.payload_hash is not None
        assert receipt.signature is not None
        assert receipt.pii_redacted is False
    
    def test_generate_receipt_with_violations(self):
        """Test generating a receipt with policy violations."""
        generator = ReceiptGenerator(signing_key="test-signing-key")
        
        request = EvaluationRequest(
            agent_id="agent-002",
            action="access_data",
            payload={"resource": "sensitive-file"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.DENY,
            reason="Access denied",
            original_payload={"resource": "sensitive-file"},
            violations=["Unauthorized resource access", "Missing credentials"],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request, policy_names=["security-policy"])
        
        assert receipt.decision == PolicyDecision.DENY
        assert len(receipt.violations) == 2
        assert "Unauthorized resource access" in receipt.violations
    
    def test_generate_receipt_with_redaction(self):
        """Test generating a receipt when payload was redacted."""
        generator = ReceiptGenerator(signing_key="test-signing-key")
        
        request = EvaluationRequest(
            agent_id="agent-003",
            action="send_email",
            payload={"email": "user@example.com", "content": "Hello"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.REDACT,
            reason="PII redacted",
            original_payload={"email": "user@example.com", "content": "Hello"},
            modified_payload={"email": "[REDACTED]", "content": "Hello"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        
        assert receipt.decision == PolicyDecision.REDACT
        assert receipt.payload_hash is not None
        assert receipt.modified_payload_hash is not None
        assert receipt.payload_hash != receipt.modified_payload_hash
    
    def test_verify_signature_valid(self):
        """Test verifying a valid receipt signature."""
        generator = ReceiptGenerator(signing_key="test-signing-key")
        
        request = EvaluationRequest(
            agent_id="agent-004",
            action="test_action",
            payload={"data": "test"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={"data": "test"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        
        assert generator.verify(receipt) is True
    
    def test_verify_signature_tampered(self):
        """Test that tampering with receipt is detected."""
        generator = ReceiptGenerator(signing_key="test-signing-key")
        
        request = EvaluationRequest(
            agent_id="agent-005",
            action="test_action",
            payload={"data": "test"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={"data": "test"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        
        tampered_receipt = PolicyReceipt(
            receipt_id=receipt.receipt_id,
            timestamp=receipt.timestamp,
            agent_id="hacker-agent",
            action=receipt.action,
            decision=receipt.decision,
            policy_names=receipt.policy_names,
            violations=receipt.violations,
            payload_hash=receipt.payload_hash,
            modified_payload_hash=receipt.modified_payload_hash,
            pii_redacted=receipt.pii_redacted,
            pii_types_found=receipt.pii_types_found,
            signature=receipt.signature,
        )
        
        assert generator.verify(tampered_receipt) is False
    
    def test_verify_signature_wrong_key(self):
        """Test that verification fails with wrong signing key."""
        generator1 = ReceiptGenerator(signing_key="key-one")
        generator2 = ReceiptGenerator(signing_key="key-two")
        
        request = EvaluationRequest(
            agent_id="agent-006",
            action="test_action",
            payload={"data": "test"},
        )
        
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={"data": "test"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator1.generate(result, request)
        
        assert generator2.verify(receipt) is False


class TestMemoryReceiptStore:
    """Tests for MemoryReceiptStore class."""
    
    def test_save_and_get(self):
        """Test saving and retrieving a receipt."""
        store = MemoryReceiptStore()
        generator = ReceiptGenerator(signing_key="test-key")
        
        request = EvaluationRequest(
            agent_id="agent-001",
            action="test",
            payload={},
        )
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        store.save(receipt)
        
        retrieved = store.get(receipt.receipt_id)
        
        assert retrieved is not None
        assert retrieved.receipt_id == receipt.receipt_id
        assert retrieved.agent_id == "agent-001"
    
    def test_get_nonexistent(self):
        """Test retrieving a non-existent receipt."""
        store = MemoryReceiptStore()
        
        assert store.get("nonexistent-id") is None
    
    def test_list_by_agent(self):
        """Test listing receipts by agent ID."""
        store = MemoryReceiptStore()
        generator = ReceiptGenerator(signing_key="test-key")
        
        for i in range(5):
            agent_id = "agent-A" if i < 3 else "agent-B"
            request = EvaluationRequest(agent_id=agent_id, action="test", payload={})
            result = EvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="OK",
                original_payload={},
                violations=[],
                pii_matches=[],
            )
            receipt = generator.generate(result, request)
            store.save(receipt)
        
        agent_a_receipts = store.list_by_agent("agent-A")
        agent_b_receipts = store.list_by_agent("agent-B")
        
        assert len(agent_a_receipts) == 3
        assert len(agent_b_receipts) == 2
        assert all(r.agent_id == "agent-A" for r in agent_a_receipts)
    
    def test_list_by_agent_with_limit(self):
        """Test listing receipts with a limit."""
        store = MemoryReceiptStore()
        generator = ReceiptGenerator(signing_key="test-key")
        
        for i in range(10):
            request = EvaluationRequest(agent_id="agent-X", action="test", payload={})
            result = EvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="OK",
                original_payload={},
                violations=[],
                pii_matches=[],
            )
            receipt = generator.generate(result, request)
            store.save(receipt)
        
        limited = store.list_by_agent("agent-X", limit=5)
        
        assert len(limited) == 5
    
    def test_list_by_date_range(self):
        """Test listing receipts by date range."""
        store = MemoryReceiptStore()
        
        now = datetime.now(timezone.utc)
        
        timestamps = [
            now - timedelta(days=5),
            now - timedelta(days=3),
            now - timedelta(days=1),
            now,
        ]
        
        for i, ts in enumerate(timestamps):
            receipt = PolicyReceipt(
                receipt_id=f"receipt-{i}",
                timestamp=ts,
                agent_id="agent-test",
                action="test",
                decision=PolicyDecision.ALLOW,
                policy_names=[],
                violations=[],
                payload_hash="abc123",
                pii_redacted=False,
                pii_types_found=[],
                signature="sig123",
            )
            store.save(receipt)
        
        start = now - timedelta(days=4)
        end = now - timedelta(hours=12)
        
        receipts = store.list_by_date_range(start, end)
        
        assert len(receipts) == 2
    
    def test_clear(self):
        """Test clearing the store."""
        store = MemoryReceiptStore()
        generator = ReceiptGenerator(signing_key="test-key")
        
        request = EvaluationRequest(agent_id="agent", action="test", payload={})
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        store.save(receipt)
        
        assert store.count == 1
        
        store.clear()
        
        assert store.count == 0


class TestFileReceiptStore:
    """Tests for FileReceiptStore class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path)
    
    def test_save_and_get(self, temp_dir):
        """Test saving and retrieving a receipt from file."""
        store = FileReceiptStore(storage_dir=temp_dir)
        generator = ReceiptGenerator(signing_key="test-key")
        
        request = EvaluationRequest(
            agent_id="agent-file-001",
            action="file_test",
            payload={"key": "value"},
        )
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={"key": "value"},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        store.save(receipt)
        
        file_path = os.path.join(temp_dir, f"{receipt.receipt_id}.json")
        assert os.path.exists(file_path)
        
        retrieved = store.get(receipt.receipt_id)
        
        assert retrieved is not None
        assert retrieved.receipt_id == receipt.receipt_id
        assert retrieved.agent_id == "agent-file-001"
    
    def test_get_nonexistent(self, temp_dir):
        """Test retrieving a non-existent receipt."""
        store = FileReceiptStore(storage_dir=temp_dir)
        
        assert store.get("nonexistent-id") is None
    
    def test_list_by_agent(self, temp_dir):
        """Test listing receipts by agent ID from files."""
        store = FileReceiptStore(storage_dir=temp_dir)
        generator = ReceiptGenerator(signing_key="test-key")
        
        for i in range(4):
            agent_id = "file-agent-A" if i < 2 else "file-agent-B"
            request = EvaluationRequest(agent_id=agent_id, action="test", payload={})
            result = EvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="OK",
                original_payload={},
                violations=[],
                pii_matches=[],
            )
            receipt = generator.generate(result, request)
            store.save(receipt)
        
        agent_a_receipts = store.list_by_agent("file-agent-A")
        agent_b_receipts = store.list_by_agent("file-agent-B")
        
        assert len(agent_a_receipts) == 2
        assert len(agent_b_receipts) == 2
    
    def test_list_by_date_range(self, temp_dir):
        """Test listing receipts by date range from files."""
        store = FileReceiptStore(storage_dir=temp_dir)
        
        now = datetime.now(timezone.utc)
        
        timestamps = [
            now - timedelta(days=10),
            now - timedelta(days=2),
            now - timedelta(hours=5),
        ]
        
        for i, ts in enumerate(timestamps):
            receipt = PolicyReceipt(
                receipt_id=f"file-receipt-{i}",
                timestamp=ts,
                agent_id="agent-date-test",
                action="test",
                decision=PolicyDecision.ALLOW,
                policy_names=[],
                violations=[],
                payload_hash="hash123",
                pii_redacted=False,
                pii_types_found=[],
                signature="sig123",
            )
            store.save(receipt)
        
        start = now - timedelta(days=3)
        end = now
        
        receipts = store.list_by_date_range(start, end)
        
        assert len(receipts) == 2
    
    def test_delete(self, temp_dir):
        """Test deleting a receipt file."""
        store = FileReceiptStore(storage_dir=temp_dir)
        generator = ReceiptGenerator(signing_key="test-key")
        
        request = EvaluationRequest(agent_id="agent", action="test", payload={})
        result = EvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason="OK",
            original_payload={},
            violations=[],
            pii_matches=[],
        )
        
        receipt = generator.generate(result, request)
        store.save(receipt)
        
        assert store.count == 1
        assert store.delete(receipt.receipt_id) is True
        assert store.count == 0
        assert store.get(receipt.receipt_id) is None
    
    def test_delete_nonexistent(self, temp_dir):
        """Test deleting a non-existent receipt."""
        store = FileReceiptStore(storage_dir=temp_dir)
        
        assert store.delete("nonexistent") is False
    
    def test_count(self, temp_dir):
        """Test counting receipts in file store."""
        store = FileReceiptStore(storage_dir=temp_dir)
        generator = ReceiptGenerator(signing_key="test-key")
        
        assert store.count == 0
        
        for i in range(3):
            request = EvaluationRequest(agent_id="agent", action="test", payload={})
            result = EvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="OK",
                original_payload={},
                violations=[],
                pii_matches=[],
            )
            receipt = generator.generate(result, request)
            store.save(receipt)
        
        assert store.count == 3
