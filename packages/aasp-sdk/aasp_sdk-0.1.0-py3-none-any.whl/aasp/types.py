"""Type definitions for AASP SDK"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    API_CALL = "api_call"
    DB_QUERY = "db_query"
    FILE_ACCESS = "file_access"


class Decision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ActionRequest:
    """Request to evaluate an agent action"""

    agent_id: str
    action_type: str
    target: str
    params: dict[str, Any]


@dataclass
class ActionResult:
    """Result of evaluating an agent action"""

    success: bool
    action_id: str
    decision: str
    reason: str
    policy_id: str | None = None
    approval_id: str | None = None


@dataclass
class ApprovalResult:
    """Result of checking approval status"""

    status: str
    decided_at: str | None = None
    decided_by: str | None = None
    reason: str | None = None
