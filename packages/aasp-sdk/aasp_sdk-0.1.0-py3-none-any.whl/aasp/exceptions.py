"""Custom exceptions for AASP SDK"""


class AASPError(Exception):
    """Base exception for AASP SDK"""

    pass


class ToolBlockedError(AASPError):
    """Raised when a tool call is blocked by policy"""

    def __init__(self, reason: str, policy_id: str | None = None):
        self.reason = reason
        self.policy_id = policy_id
        super().__init__(f"Tool blocked: {reason}")


class ApprovalTimeoutError(AASPError):
    """Raised when approval request times out"""

    def __init__(self, approval_id: str, timeout: int):
        self.approval_id = approval_id
        self.timeout = timeout
        super().__init__(f"Approval request {approval_id} timed out after {timeout}s")


class ApprovalRejectedError(AASPError):
    """Raised when approval request is rejected"""

    def __init__(self, approval_id: str, reason: str | None = None):
        self.approval_id = approval_id
        self.reason = reason
        msg = f"Approval request {approval_id} rejected"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class AuthenticationError(AASPError):
    """Raised when API key is invalid"""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message)


class NetworkError(AASPError):
    """Raised when network request fails"""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)
