import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
import structlog

from tork.core.models import EvaluationRequest, EvaluationResult, PolicyDecision

logger = structlog.get_logger(__name__)


class PolicyReceipt(BaseModel):
    """
    Audit receipt for a policy evaluation decision.
    
    Contains all relevant information for compliance auditing,
    including tamper-detection signature.
    """
    
    receipt_id: str = Field(..., description="Unique receipt identifier (UUID)")
    timestamp: datetime = Field(..., description="When the evaluation occurred")
    agent_id: str = Field(..., description="ID of the agent that performed the action")
    action: str = Field(..., description="Action that was evaluated")
    decision: PolicyDecision = Field(..., description="Policy decision outcome")
    policy_names: list[str] = Field(default_factory=list, description="Policies that were evaluated")
    violations: list[str] = Field(default_factory=list, description="List of policy violations")
    payload_hash: str = Field(..., description="SHA256 hash of original payload")
    modified_payload_hash: Optional[str] = Field(default=None, description="SHA256 hash of modified payload (if redacted)")
    pii_redacted: bool = Field(default=False, description="Whether PII was redacted")
    pii_types_found: list[str] = Field(default_factory=list, description="Types of PII detected")
    signature: str = Field(..., description="HMAC signature for tamper detection")


class ReceiptGenerator:
    """
    Generates and verifies compliance receipts for audit trails.
    
    Uses HMAC-SHA256 for tamper detection signatures.
    """
    
    def __init__(self, signing_key: str) -> None:
        """
        Initialize the receipt generator.
        
        Args:
            signing_key: Secret key used for HMAC signatures.
        """
        self.signing_key = signing_key
        logger.info("ReceiptGenerator initialized")
    
    def create_receipt(
        self,
        result: EvaluationResult,
        request: EvaluationRequest,
        policy_names: Optional[list[str]] = None,
    ) -> PolicyReceipt:
        """
        Generate a compliance receipt from an evaluation result.
        
        Args:
            result: The evaluation result from the governance engine.
            request: The original evaluation request.
            policy_names: Optional list of policy names that were evaluated.
            
        Returns:
            PolicyReceipt with tamper-detection signature.
        """
        receipt_id = str(uuid.uuid4())
        timestamp = result.timestamp if hasattr(result, 'timestamp') and result.timestamp else datetime.now(timezone.utc)
        
        payload_hash = self._hash_payload(result.original_payload)
        modified_payload_hash = None
        if result.modified_payload:
            modified_payload_hash = self._hash_payload(result.modified_payload)
        
        pii_redacted = len(result.pii_matches) > 0
        pii_types_found = []
        for match in result.pii_matches:
            if hasattr(match, 'pii_type'):
                pii_type = match.pii_type.value if hasattr(match.pii_type, 'value') else str(match.pii_type)
                if pii_type not in pii_types_found:
                    pii_types_found.append(pii_type)
        
        receipt_data = {
            "receipt_id": receipt_id,
            "timestamp": timestamp.isoformat(),
            "agent_id": request.agent_id,
            "action": request.action,
            "decision": result.decision.value,
            "policy_names": policy_names or [],
            "violations": result.violations,
            "payload_hash": payload_hash,
            "modified_payload_hash": modified_payload_hash,
            "pii_redacted": pii_redacted,
            "pii_types_found": pii_types_found,
        }
        
        signature = self._compute_signature(receipt_data)
        
        receipt = PolicyReceipt(
            receipt_id=receipt_id,
            timestamp=timestamp,
            agent_id=request.agent_id,
            action=request.action,
            decision=result.decision,
            policy_names=policy_names or [],
            violations=result.violations,
            payload_hash=payload_hash,
            modified_payload_hash=modified_payload_hash,
            pii_redacted=pii_redacted,
            pii_types_found=pii_types_found,
            signature=signature,
        )
        
        logger.info(
            "Receipt generated",
            receipt_id=receipt_id,
            agent_id=request.agent_id,
            decision=result.decision.value,
        )
        
        return receipt
    
    def generate(
        self,
        result: EvaluationResult,
        request: EvaluationRequest,
        policy_names: Optional[list[str]] = None,
    ) -> PolicyReceipt:
        """Alias for create_receipt to maintain backward compatibility if needed."""
        return self.create_receipt(result, request, policy_names)
    
    def verify(self, receipt: PolicyReceipt) -> bool:
        """
        Verify that a receipt has not been tampered with.
        
        Args:
            receipt: The receipt to verify.
            
        Returns:
            True if signature is valid, False if tampered.
        """
        receipt_data = {
            "receipt_id": receipt.receipt_id,
            "timestamp": receipt.timestamp.isoformat(),
            "agent_id": receipt.agent_id,
            "action": receipt.action,
            "decision": receipt.decision.value,
            "policy_names": receipt.policy_names,
            "violations": receipt.violations,
            "payload_hash": receipt.payload_hash,
            "modified_payload_hash": receipt.modified_payload_hash,
            "pii_redacted": receipt.pii_redacted,
            "pii_types_found": receipt.pii_types_found,
        }
        
        expected_signature = self._compute_signature(receipt_data)
        is_valid = hmac.compare_digest(receipt.signature, expected_signature)
        
        logger.info(
            "Receipt verification",
            receipt_id=receipt.receipt_id,
            is_valid=is_valid,
        )
        
        return is_valid
    
    def _compute_signature(self, receipt_data: dict) -> str:
        """
        Compute HMAC-SHA256 signature for receipt data.
        
        Args:
            receipt_data: Dictionary of receipt fields (excluding signature).
            
        Returns:
            Hexadecimal HMAC signature.
        """
        canonical = json.dumps(receipt_data, sort_keys=True, default=str)
        signature = hmac.new(
            self.signing_key.encode('utf-8'),
            canonical.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return signature
    
    def _hash_payload(self, payload: dict) -> str:
        """
        Compute SHA256 hash of a payload.
        
        Args:
            payload: Dictionary payload to hash.
            
        Returns:
            Hexadecimal SHA256 hash.
        """
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
