class AutoGenGovernanceError(Exception):
    """Base exception for AutoGen governance errors."""
    pass

class MessageBlockedError(AutoGenGovernanceError):
    """Raised when an incoming message is blocked by policy."""
    pass

class ResponseBlockedError(AutoGenGovernanceError):
    """Raised when an outgoing response is blocked by policy."""
    pass
