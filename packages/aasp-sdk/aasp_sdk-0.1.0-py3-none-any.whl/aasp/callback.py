"""LangChain callback handler for AASP"""

from typing import Any
from uuid import UUID

from .client import AASPClient
from .exceptions import ApprovalTimeoutError, ToolBlockedError
from .types import Decision

# Try to import LangChain - it's an optional dependency
try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Create a dummy base class if LangChain is not installed
    class BaseCallbackHandler:  # type: ignore
        """Dummy base class when LangChain is not installed"""

        pass


class AASPCallback(BaseCallbackHandler):
    """LangChain callback handler that integrates with AASP.

    This callback intercepts tool calls and sends them to AASP for
    policy evaluation before execution.

    Example:
        ```python
        from langchain.agents import AgentExecutor
        from aasp import AASPCallback

        callback = AASPCallback(api_key="aasp_live_xxx")

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            callbacks=[callback]
        )

        executor.invoke({"input": "Process the invoice"})
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://aasp.dev/api/v1",
        agent_id: str | None = None,
        block_on_error: bool = False,
        approval_timeout: int = 300,
    ):
        """Initialize the AASP callback.

        Args:
            api_key: Your AASP API key
            base_url: Base URL for the AASP API
            agent_id: Optional identifier for this agent (auto-generated if not provided)
            block_on_error: If True, block actions when AASP is unreachable
            approval_timeout: Timeout in seconds for approval requests
        """
        super().__init__()
        self.client = AASPClient(api_key, base_url)
        self.agent_id = agent_id
        self.block_on_error = block_on_error
        self.approval_timeout = approval_timeout
        self._run_agent_id: str | None = None

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts running."""
        # Use the run_id as agent_id if not specified
        if not self.agent_id:
            self._run_agent_id = str(run_id)[:8]

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running.

        This is the main interception point where we evaluate the action
        against AASP policies.
        """
        tool_name = serialized.get("name", "unknown_tool")
        agent_id = self.agent_id or self._run_agent_id or "default"

        # Build params from available data
        params = {
            "input": input_str,
            "tool_name": tool_name,
        }

        # Add any additional kwargs that might be useful
        if metadata:
            params["metadata"] = metadata
        if tags:
            params["tags"] = tags

        try:
            result = self.client.evaluate_action(
                agent_id=agent_id,
                action_type="tool_call",
                target=tool_name,
                params=params,
            )

            if result.decision == Decision.BLOCK.value:
                raise ToolBlockedError(result.reason, result.policy_id)

            elif result.decision == Decision.REQUIRE_APPROVAL.value:
                if result.approval_id:
                    # Wait for human approval
                    self.client.wait_for_approval(
                        result.approval_id,
                        timeout=self.approval_timeout,
                    )

        except ToolBlockedError:
            raise  # Re-raise blocking errors

        except ApprovalTimeoutError:
            raise  # Re-raise timeout errors

        except Exception as e:
            # Handle connection errors based on block_on_error setting
            if self.block_on_error:
                raise ToolBlockedError(f"AASP unavailable: {str(e)}")
            # Otherwise, allow the action to proceed (fail-open)

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes running."""
        # Log the output for audit purposes
        output_str = str(output) if output else ""
        self.client.log_action_result(output_str)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool errors."""
        # Log the error
        self.client.log_action_result(f"ERROR: {str(error)}")
