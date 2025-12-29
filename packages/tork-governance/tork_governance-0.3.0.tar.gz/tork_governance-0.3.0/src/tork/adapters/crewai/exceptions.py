class GovernanceBlockedError(Exception):
    """Raised when a task is blocked by governance policy."""
    pass

class PIIDetectedError(Exception):
    """Raised when PII is detected and the action is DENY."""
    pass
