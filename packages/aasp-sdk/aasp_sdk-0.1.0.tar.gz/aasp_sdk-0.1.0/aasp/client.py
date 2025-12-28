"""AASP API Client"""

import time
from typing import Any

import httpx

from .exceptions import (
    ApprovalRejectedError,
    ApprovalTimeoutError,
    AuthenticationError,
    NetworkError,
    ToolBlockedError,
)
from .types import ActionResult, ApprovalResult, ApprovalStatus, Decision


class AASPClient:
    """HTTP client for AASP API"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://aasp.dev/api/v1",
        timeout: float = 30.0,
    ):
        """Initialize the AASP client.

        Args:
            api_key: Your AASP API key (starts with aasp_live_ or aasp_test_)
            base_url: Base URL for the AASP API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aasp-python/0.1.0",
            },
            timeout=timeout,
        )
        self._current_action_id: str | None = None

    def evaluate_action(
        self,
        agent_id: str,
        action_type: str,
        target: str,
        params: dict[str, Any],
    ) -> ActionResult:
        """Send an action to AASP for policy evaluation.

        Args:
            agent_id: Identifier for the agent making the action
            action_type: Type of action (tool_call, api_call, db_query, file_access)
            target: Target of the action (tool name, URL, table name, etc.)
            params: Additional parameters for the action

        Returns:
            ActionResult with decision and metadata

        Raises:
            ToolBlockedError: If the action is blocked by policy
            AuthenticationError: If the API key is invalid
            NetworkError: If the request fails
        """
        try:
            response = self._http.post(
                "/ingest",
                json={
                    "agent_id": agent_id,
                    "action_type": action_type,
                    "target": target,
                    "params": params,
                },
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")

            response.raise_for_status()
            data = response.json()

            result = ActionResult(
                success=data.get("success", True),
                action_id=data["action_id"],
                decision=data["decision"],
                reason=data["reason"],
                policy_id=data.get("policy_id"),
                approval_id=data.get("approval_id"),
            )

            self._current_action_id = result.action_id
            return result

        except httpx.HTTPStatusError as e:
            raise NetworkError(f"HTTP error: {e.response.status_code}", e)
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}", e)

    def check_approval_status(self, approval_id: str) -> ApprovalResult:
        """Check the status of an approval request.

        Args:
            approval_id: ID of the approval request

        Returns:
            ApprovalResult with current status
        """
        try:
            response = self._http.get(f"/approvals/{approval_id}/status")

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")

            response.raise_for_status()
            data = response.json()

            return ApprovalResult(
                status=data["status"],
                decided_at=data.get("decided_at"),
                decided_by=data.get("decided_by"),
                reason=data.get("reason"),
            )

        except httpx.HTTPStatusError as e:
            raise NetworkError(f"HTTP error: {e.response.status_code}", e)
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}", e)

    def wait_for_approval(
        self,
        approval_id: str,
        timeout: int = 300,
        poll_interval: float = 2.0,
    ) -> ApprovalResult:
        """Wait for an approval request to be resolved.

        Args:
            approval_id: ID of the approval request
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            ApprovalResult when approved

        Raises:
            ApprovalTimeoutError: If approval times out
            ApprovalRejectedError: If approval is rejected
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise ApprovalTimeoutError(approval_id, timeout)

            result = self.check_approval_status(approval_id)

            if result.status == ApprovalStatus.APPROVED.value:
                return result
            elif result.status == ApprovalStatus.REJECTED.value:
                raise ApprovalRejectedError(approval_id, result.reason)

            time.sleep(poll_interval)

    def log_action_result(self, output: str) -> None:
        """Log the result of a completed action.

        Args:
            output: Output/result of the action
        """
        if not self._current_action_id:
            return

        try:
            self._http.post(
                f"/actions/{self._current_action_id}/result",
                json={"output": output[:10000]},  # Limit output size
            )
        except Exception:
            # Don't raise on logging failures
            pass

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> "AASPClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
