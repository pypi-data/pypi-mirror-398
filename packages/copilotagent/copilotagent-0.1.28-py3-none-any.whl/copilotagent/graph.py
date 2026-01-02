"""Deepagents come with planning, filesystem, and subagents."""

from collections.abc import Callable, Sequence
from typing import Any, Literal

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, InterruptOnConfig
from langchain.agents.middleware.summarization import SummarizationMiddleware
from langchain.agents.middleware.types import AgentMiddleware
from langchain.agents.structured_output import ResponseFormat
from langchain_anthropic import ChatAnthropic
from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.cache.base import BaseCache
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer

from copilotagent.middleware.dynamic_tools import DynamicToolMiddleware
from copilotagent.middleware.filesystem import FilesystemMiddleware
from copilotagent.middleware.initial_message import InitialMessageMiddleware
from copilotagent.middleware.patch_tool_calls import PatchToolCallsMiddleware
from copilotagent.middleware.planning import PlanningMiddleware
from copilotagent.middleware.subagents import CompiledSubAgent, SubAgent, SubAgentMiddleware

# Global default agent type for planning middleware
DEFAULT_AGENT_TYPE: Literal["ITP-Princeton", "DrawDoc-AWM", "research"] = "ITP-Princeton"

BASE_AGENT_PROMPT = "In order to complete the objective that the user asks of you, you have access to a number of standard tools."


def get_default_model() -> ChatAnthropic:
    """Get the default model for deep agents.

    Returns:
        ChatAnthropic instance configured with Claude Sonnet 4.
    """
    return ChatAnthropic(
        model_name="claude-sonnet-4-5-20250929",
        max_tokens=20000,
    )


def get_default_starting_message(
    agent_type: Literal["ITP-Princeton", "DrawDoc-AWM", "research"]
) -> str | None:
    """Get the default starting message for an agent type.
    
    Note: Agents should pass their own default_starting_message parameter to
    create_deep_agent() instead of relying on this function. This function
    exists for backward compatibility only.

    Args:
        agent_type: The type of agent.

    Returns:
        None - agents should define their own starting messages.
    """
    return None


def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    response_format: ResponseFormat | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    use_longterm_memory: bool = False,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    agent_type: Literal["ITP-Princeton", "DrawDoc-AWM", "research"] | None = None,
    planning_prompt: str | None = None,
    default_starting_message: str | None = None,
    tool_resolver: Callable[[dict[str, Any]], Sequence[BaseTool | Callable | dict[str, Any]]] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph:
    """Create a deep agent.

    This agent will by default have access to a tool to write todos (write_todos),
    four file editing tools: write_file, ls, read_file, edit_file, and a tool to call
    subagents.

    Args:
        tools: The tools the agent should have access to.
        system_prompt: The additional instructions the agent should have. Will go in
            the system prompt.
        middleware: Additional middleware to apply after standard middleware.
        model: The model to use.
        subagents: The subagents to use. Each subagent should be a dictionary with the
            following keys:
                - `name`
                - `description` (used by the main agent to decide whether to call the
                  sub agent)
                - `prompt` (used as the system prompt in the subagent)
                - (optional) `tools`
                - (optional) `model` (either a LanguageModelLike instance or dict
                  settings)
                - (optional) `middleware` (list of AgentMiddleware)
        response_format: A structured output response format to use for the agent.
        context_schema: The schema of the deep agent.
        checkpointer: Optional checkpointer for persisting agent state between runs.
        store: Optional store for persisting longterm memories.
        use_longterm_memory: Whether to use longterm memory - you must provide a store
            in order to use longterm memory.
        interrupt_on: Optional Dict[str, bool | InterruptOnConfig] mapping tool names to
            interrupt configs.
        agent_type: Type of agent for planning prompts. Options: "ITP-Princeton",
            "DrawDoc-AWM", "research". Defaults to the global DEFAULT_AGENT_TYPE.
        planning_prompt: Custom planning prompt to use instead of the built-in prompt
            for the agent_type. This allows agents to provide their own planning
            prompts without modifying the PyPI package.
        default_starting_message: Optional default message to auto-send when the agent
            starts with no messages. If provided, InitialMessageMiddleware will inject
            this as the first message. If None, no auto-start message is used.
        tool_resolver: Optional callable that dynamically filters tools based on state.
            Called before each model invocation with the current state and should return
            a list of tools to bind for that specific call. This enables reducing context
            window usage by only passing relevant tools per step. If None, all tools are
            always bound (default behavior).
        debug: Whether to enable debug mode. Passed through to create_agent.
        name: The name of the agent. Passed through to create_agent.
        cache: The cache to use for the agent. Passed through to create_agent.

    Returns:
        A configured deep agent.
    """
    if model is None:
        model = get_default_model()

    # Use the provided agent_type or fall back to the global default
    if agent_type is None:
        agent_type = DEFAULT_AGENT_TYPE

    # Use the provided default_starting_message, or get it from agent_type if not provided
    if default_starting_message is None:
        default_starting_message = get_default_starting_message(agent_type)

    deepagent_middleware = []
    
    # Only add InitialMessageMiddleware if there's a default message
    # If no default message, agents should use default_input in langgraph.json
    if default_starting_message:
        deepagent_middleware.append(
        InitialMessageMiddleware(
            agent_type=agent_type,
            default_message=default_starting_message,
            )
        )
    
    # Add dynamic tool middleware if tool_resolver is provided
    # This should come early in the middleware chain to filter tools
    # before they are processed by other middleware
    if tool_resolver is not None:
        deepagent_middleware.append(
            DynamicToolMiddleware(
                tool_resolver=tool_resolver,
                fallback_tools=tools if tools is not None else [],
            )
        )
    
    # Add remaining middleware
    deepagent_middleware.extend([
        PlanningMiddleware(
            agent_type=agent_type,
            system_prompt=planning_prompt,
        ),
        FilesystemMiddleware(
            long_term_memory=use_longterm_memory,
        ),
        SubAgentMiddleware(
            default_model=model,
            default_tools=tools,
            subagents=subagents if subagents is not None else [],
            default_middleware=[
                PlanningMiddleware(
                    agent_type=agent_type,
                    system_prompt=planning_prompt,
                ),
                FilesystemMiddleware(
                    long_term_memory=use_longterm_memory,
                ),
                SummarizationMiddleware(
                    model=model,
                    max_tokens_before_summary=170000,
                    messages_to_keep=6,
                ),
                AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore"),
                PatchToolCallsMiddleware(),
            ],
            default_interrupt_on=interrupt_on,
            general_purpose_agent=True,
        ),
        SummarizationMiddleware(
            model=model,
            max_tokens_before_summary=170000,
            messages_to_keep=6,
        ),
        AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore"),
        PatchToolCallsMiddleware(),
    ])
    
    if interrupt_on is not None:
        deepagent_middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))
    if middleware is not None:
        deepagent_middleware.extend(middleware)

    return create_agent(
        model,
        system_prompt=system_prompt + "\n\n" + BASE_AGENT_PROMPT if system_prompt else BASE_AGENT_PROMPT,
        tools=tools,
        middleware=deepagent_middleware,
        response_format=response_format,
        context_schema=context_schema,
        checkpointer=checkpointer,
        store=store,
        debug=debug,
        name=name,
        cache=cache,
    ).with_config({"recursion_limit": 1000})
