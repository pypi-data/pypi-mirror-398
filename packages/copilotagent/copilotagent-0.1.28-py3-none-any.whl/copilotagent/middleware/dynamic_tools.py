"""Middleware for dynamic tool binding based on agent state.

This middleware allows agents to dynamically select which tools to bind to the LLM
based on the current state, reducing context window usage by only passing relevant
tools per step.
"""

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.tools import BaseTool


class DynamicToolMiddleware(AgentMiddleware):
    """Middleware for dynamically binding tools based on agent state.

    This middleware intercepts model calls and uses a tool resolver function to
    determine which subset of tools should be bound for each specific model call.
    This can significantly reduce context window usage when dealing with large
    tool sets.

    Args:
        tool_resolver: A callable that takes the current state and returns a list
            of tools to bind for this model call. If None, all tools are passed through.
        fallback_tools: Optional fallback tools to use if tool_resolver returns None
            or an empty list.

    Example:
        ```python
        from copilotagent.middleware.dynamic_tools import DynamicToolMiddleware
        from copilotagent import create_deep_agent

        def resolve_tools_for_step(state: dict) -> list[BaseTool]:
            \"\"\"Dynamically select tools based on current step in state.\"\"\"
            current_step = state.get("current_step", "STEP_00")
            
            # Return step-specific tools
            if current_step == "STEP_00":
                return [tool1, tool2, tool3]
            elif current_step == "STEP_01":
                return [tool2, tool4, tool5]
            else:
                return [tool1, tool2, tool3, tool4, tool5]

        # Create agent with dynamic tool binding
        agent = create_deep_agent(
            model="claude-sonnet-4-5-20250929",
            tools=[tool1, tool2, tool3, tool4, tool5],  # All available tools
            middleware=[
                DynamicToolMiddleware(tool_resolver=resolve_tools_for_step)
            ],
            system_prompt="Your system prompt..."
        )
        ```

    Benefits:
        - Reduces context window usage by only passing relevant tools
        - Improves model performance by reducing noise from irrelevant tools
        - Maintains flexibility to add/remove tools dynamically
        - Backward compatible - if tool_resolver is None, all tools pass through
    """

    def __init__(
        self,
        *,
        tool_resolver: Callable[[dict[str, Any]], Sequence[BaseTool | Callable | dict[str, Any]]] | None = None,
        fallback_tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the DynamicToolMiddleware.

        Args:
            tool_resolver: Callable that receives state and returns filtered tools.
            fallback_tools: Optional fallback tools if resolver returns empty list.
        """
        super().__init__()
        self.tool_resolver = tool_resolver
        self.fallback_tools = fallback_tools or []

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Dynamically filter tools before each model call.

        Args:
            request: The model request being processed.
            handler: The handler function to call with the modified request.

        Returns:
            The model response from the handler.
        """
        # If no tool resolver, pass through unchanged
        if self.tool_resolver is None:
            return handler(request)

        # Get current state from request
        state = getattr(request, "state", {})

        # Call the tool resolver to get filtered tools
        try:
            filtered_tools = self.tool_resolver(state)
            
            # If resolver returns None or empty list, use fallback
            if not filtered_tools:
                filtered_tools = self.fallback_tools

            # Update the request with filtered tools
            # Note: The tools attribute might be on the model or the request
            # depending on LangChain's internal structure
            if hasattr(request, "tools"):
                request.tools = filtered_tools
            elif hasattr(request, "model") and hasattr(request.model, "bind_tools"):
                # Rebind the model with filtered tools
                request.model = request.model.bind_tools(filtered_tools)

        except Exception as e:
            # If tool resolution fails, log and continue with original tools
            import logging
            logging.warning(f"Tool resolver failed: {e}. Using all tools.")

        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """(async) Dynamically filter tools before each model call.

        Args:
            request: The model request being processed.
            handler: The handler function to call with the modified request.

        Returns:
            The model response from the handler.
        """
        # If no tool resolver, pass through unchanged
        if self.tool_resolver is None:
            return await handler(request)

        # Get current state from request
        state = getattr(request, "state", {})

        # Call the tool resolver to get filtered tools
        try:
            filtered_tools = self.tool_resolver(state)
            
            # If resolver returns None or empty list, use fallback
            if not filtered_tools:
                filtered_tools = self.fallback_tools

            # Update the request with filtered tools
            if hasattr(request, "tools"):
                request.tools = filtered_tools
            elif hasattr(request, "model") and hasattr(request.model, "bind_tools"):
                # Rebind the model with filtered tools
                request.model = request.model.bind_tools(filtered_tools)

        except Exception as e:
            # If tool resolution fails, log and continue with original tools
            import logging
            logging.warning(f"Tool resolver failed: {e}. Using all tools.")

        return await handler(request)


