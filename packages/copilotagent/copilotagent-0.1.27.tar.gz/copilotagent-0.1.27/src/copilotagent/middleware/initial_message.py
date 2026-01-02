"""Middleware for handling default initial messages based on agent type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

from langchain_core.messages import HumanMessage

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
)


class InitialMessageMiddleware(AgentMiddleware):
    """Middleware that provides default initial messages for specific agent types.

    This middleware checks if the agent is starting fresh (no messages yet) and
    if the agent type requires a default starting message. If so, it automatically
    adds the default message as the first human message.

    For agent types without a default message (like "research"), the middleware
    does nothing and lets the normal flow proceed (requiring human input).

    Example:
        ```python
        from deepagents.middleware.initial_message import InitialMessageMiddleware
        from langchain.agents import create_agent

        # ITP-Princeton agent with default starting message
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[
                InitialMessageMiddleware(
                    agent_type="ITP-Princeton"
                )
            ]
        )
        ```

    Args:
        agent_type: Type of agent this middleware is for.
        default_message: The default starting message for this agent type.
            If None, no default message will be used.
    """

    def __init__(
        self,
        *,
        agent_type: Literal["ITP-Princeton", "DrawDoc-AWM", "research"],
        default_message: str | None = None,
    ) -> None:
        """Initialize the InitialMessageMiddleware.

        Args:
            agent_type: Type of agent (ITP-Princeton, DrawDoc-AWM, research).
            default_message: Optional default starting message.
        """
        super().__init__()
        self.agent_type = agent_type
        self.default_message = default_message

    def before_agent(self, state: AgentState, runtime: Runtime[Any]) -> dict[str, Any] | None:  # noqa: ARG002
        """Add default initial message if no human messages exist.
        
        This runs once per agent invocation, before the agent starts.
        """
        # If no default message, do nothing
        if not self.default_message:
            return None
            
        messages = state.get("messages", [])
        
        # Check if we have any human messages
        has_human_messages = any(
            isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human"
            for msg in messages
        )
        
        # If we have a default message and no human messages yet, add it
        if not has_human_messages:
            return {"messages": [HumanMessage(content=self.default_message)]}
        
        return None

