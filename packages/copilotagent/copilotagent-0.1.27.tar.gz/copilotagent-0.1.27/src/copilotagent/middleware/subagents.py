"""Middleware for providing subagents to an agent via a `task` tool."""

from collections.abc import Awaitable, Callable, Sequence
from typing import Any, TypedDict, cast
from typing_extensions import NotRequired

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, InterruptOnConfig
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain.tools import BaseTool, ToolRuntime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import StructuredTool
from langgraph.config import get_config
from langgraph.types import Command
from pydantic import BaseModel, Field


class SubAgent(TypedDict):
    """Specification for an agent.

    When specifying custom agents, the `default_middleware` from `SubAgentMiddleware`
    will be applied first, followed by any `middleware` specified in this spec.
    To use only custom middleware without the defaults, pass `default_middleware=[]`
    to `SubAgentMiddleware`.
    """

    name: str
    """The name of the agent."""

    description: str
    """The description of the agent."""

    system_prompt: str
    """The system prompt to use for the agent."""

    tools: Sequence[BaseTool | Callable | dict[str, Any]]
    """The tools to use for the agent."""

    model: NotRequired[str | BaseChatModel]
    """The model for the agent. Defaults to `default_model`."""

    middleware: NotRequired[list[AgentMiddleware]]
    """Additional middleware to append after `default_middleware`."""

    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]
    """The tool configs to use for the agent."""


class CompiledSubAgent(TypedDict):
    """A pre-compiled agent spec."""

    name: str
    """The name of the agent."""

    description: str
    """The description of the agent."""

    runnable: Runnable
    """The Runnable to use for the agent."""


DEFAULT_SUBAGENT_PROMPT = "In order to complete the objective that the user asks of you, you have access to a number of standard tools."

# State keys that should be excluded when passing state to subagents
_EXCLUDED_STATE_KEYS = ("messages", "todos")

TASK_TOOL_DESCRIPTION = """Launch an ephemeral subagent to handle complex, multi-step independent tasks with isolated context windows.

Available agent types and the tools they have access to:
{available_agents}

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

## Parameters:
- **description** (required): Task description for the subagent. Provide clear, detailed instructions.
- **subagent_type** (required): Which agent type to invoke (see available agents above).
- **inputs** (optional): Structured dictionary of inputs for the subagent.
  - Some subagents require specific inputs (check agent descriptions above for requirements)
  - Format: {{"key1": "value1", "key2": "value2"}}
  - Example: {{"borrower_name": "Smith, John", "loan_number": "12345"}}
  - The inputs are passed directly to the subagent's state - no parsing required

## Usage notes:
1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to create content, perform analysis, or just do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent
6. If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.
7. When only the general-purpose agent is provided, you should use it for all tasks. It is great for isolating context and token usage, and completing specific, complex tasks, as it has all the same capabilities as the main agent.

### Example usage of the general-purpose agent:

<example_agent_descriptions>
"general-purpose": use this agent for general purpose tasks, it has access to all tools as the main agent.
</example_agent_descriptions>

<example>
User: "I want to conduct research on the accomplishments of Lebron James, Michael Jordan, and Kobe Bryant, and then compare them."
Assistant: *Uses the task tool in parallel to conduct isolated research on each of the three players*
Assistant: *Synthesizes the results of the three isolated research tasks and responds to the User*
<commentary>
Research is a complex, multi-step task in it of itself.
The research of each individual player is not dependent on the research of the other players.
The assistant uses the task tool to break down the complex objective into three isolated tasks.
Each research task only needs to worry about context and tokens about one player, then returns synthesized information about each player as the Tool Result.
This means each research task can dive deep and spend tokens and context deeply researching each player, but the final result is synthesized information, and saves us tokens in the long run when comparing the players to each other.
</commentary>
</example>

<example>
User: "Analyze a single large code repository for security vulnerabilities and generate a report."
Assistant: *Launches a single `task` subagent for the repository analysis*
Assistant: *Receives report and integrates results into final summary*
<commentary>
Subagent is used to isolate a large, context-heavy task, even though there is only one. This prevents the main thread from being overloaded with details.
If the user then asks followup questions, we have a concise report to reference instead of the entire history of analysis and tool calls, which is good and saves us time and money.
</commentary>
</example>

<example>
User: "Schedule two meetings for me and prepare agendas for each."
Assistant: *Calls the task tool in parallel to launch two `task` subagents (one per meeting) to prepare agendas*
Assistant: *Returns final schedules and agendas*
<commentary>
Tasks are simple individually, but subagents help silo agenda preparation.
Each subagent only needs to worry about the agenda for one meeting.
</commentary>
</example>

<example>
User: "I want to order a pizza from Dominos, order a burger from McDonald's, and order a salad from Subway."
Assistant: *Calls tools directly in parallel to order a pizza from Dominos, a burger from McDonald's, and a salad from Subway*
<commentary>
The assistant did not use the task tool because the objective is super simple and clear and only requires a few trivial tool calls.
It is better to just complete the task directly and NOT use the `task`tool.
</commentary>
</example>

### Example usage with custom agents:

<example_agent_descriptions>
"content-reviewer": use this agent after you are done creating significant content or documents
"greeting-responder": use this agent when to respond to user greetings with a friendly joke
"research-analyst": use this agent to conduct thorough research on complex topics
</example_agent_description>

<example>
user: "Please write a function that checks if a number is prime"
assistant: Sure let me write a function that checks if a number is prime
assistant: First let me use the Write tool to write a function that checks if a number is prime
assistant: I'm going to use the Write tool to write the following code:
<code>
function isPrime(n) {{
  if (n <= 1) return false
  for (let i = 2; i * i <= n; i++) {{
    if (n % i === 0) return false
  }}
  return true
}}
</code>
<commentary>
Since significant content was created and the task was completed, now use the content-reviewer agent to review the work
</commentary>
assistant: Now let me use the content-reviewer agent to review the code
assistant: Uses the Task tool to launch with the content-reviewer agent
</example>

<example>
user: "Can you help me research the environmental impact of different renewable energy sources and create a comprehensive report?"
<commentary>
This is a complex research task that would benefit from using the research-analyst agent to conduct thorough analysis
</commentary>
assistant: I'll help you research the environmental impact of renewable energy sources. Let me use the research-analyst agent to conduct comprehensive research on this topic.
assistant: Uses the Task tool to launch with the research-analyst agent, providing detailed instructions about what research to conduct and what format the report should take
</example>

<example>
user: "Hello"
<commentary>
Since the user is greeting, use the greeting-responder agent to respond with a friendly joke
</commentary>
assistant: "I'm going to use the Task tool to launch with the greeting-responder agent"
</example>

### Example with structured inputs:

<example_agent_descriptions>
"data-processor": processes loan data for a specific borrower. Requires inputs: {{"borrower_name": "string", "loan_number": "string"}}
</example_agent_descriptions>

<example>
user: "Process the loan data for borrower John Smith with loan number 12345"
<commentary>
The data-processor agent requires structured inputs with borrower_name and loan_number.
These should be passed via the inputs parameter, not embedded in the description.
</commentary>
assistant: *Uses the task tool with structured inputs*
task(
  subagent_type="data-processor",
  description="Process the loan data and generate a report",
  inputs={{"borrower_name": "Smith, John", "loan_number": "12345"}}
)
</example>"""  # noqa: E501

TASK_SYSTEM_PROMPT = """## `task` (subagent spawner)

You have access to a `task` tool to launch short-lived subagents that handle isolated tasks. These agents are ephemeral — they live only for the duration of the task and return a single result.

When to use the task tool:
- When a task is complex and multi-step, and can be fully delegated in isolation
- When a task is independent of other tasks and can run in parallel
- When a task requires focused reasoning or heavy token/context usage that would bloat the orchestrator thread
- When sandboxing improves reliability (e.g. code execution, structured searches, data formatting)
- When you only care about the output of the subagent, and not the intermediate steps (ex. performing a lot of research and then returned a synthesized report, performing a series of computations or lookups to achieve a concise, relevant answer.)

Subagent lifecycle:
1. **Spawn** → Provide clear role, instructions, and expected output
2. **Run** → The subagent completes the task autonomously
3. **Return** → The subagent provides a single structured result
4. **Reconcile** → Incorporate or synthesize the result into the main thread

When NOT to use the task tool:
- If you need to see the intermediate reasoning or steps after the subagent has completed (the task tool hides them)
- If the task is trivial (a few tool calls or simple lookup)
- If delegating does not reduce token usage, complexity, or context switching
- If splitting would add latency without benefit

## Important Task Tool Usage Notes to Remember
- Whenever possible, parallelize the work that you do. This is true for both tool_calls, and for tasks. Whenever you have independent steps to complete - make tool_calls, or kick off tasks (subagents) in parallel to accomplish them faster. This saves time for the user, which is incredibly important.
- Remember to use the `task` tool to silo independent tasks within a multi-part objective.
- You should use the `task` tool whenever you have a complex task that will take multiple steps, and is independent from other tasks that the agent needs to complete. These agents are highly competent and efficient."""  # noqa: E501


DEFAULT_GENERAL_PURPOSE_DESCRIPTION = "General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. This agent has access to all tools as the main agent."  # noqa: E501


def _get_subagents(
    *,
    default_model: str | BaseChatModel,
    default_tools: Sequence[BaseTool | Callable | dict[str, Any]],
    default_middleware: list[AgentMiddleware] | None,
    default_interrupt_on: dict[str, bool | InterruptOnConfig] | None,
    subagents: list[SubAgent | CompiledSubAgent],
    general_purpose_agent: bool,
) -> tuple[dict[str, Any], list[str]]:
    """Create subagent instances from specifications.

    Args:
        default_model: Default model for subagents that don't specify one.
        default_tools: Default tools for subagents that don't specify tools.
        default_middleware: Middleware to apply to all subagents. If `None`,
            no default middleware is applied.
        default_interrupt_on: The tool configs to use for the default general-purpose subagent. These
            are also the fallback for any subagents that don't specify their own tool configs.
        subagents: List of agent specifications or pre-compiled agents.
        general_purpose_agent: Whether to include a general-purpose subagent.

    Returns:
        Tuple of (agent_dict, description_list) where agent_dict maps agent names
        to runnable instances and description_list contains formatted descriptions.
    """
    # Use empty list if None (no default middleware)
    default_subagent_middleware = default_middleware or []

    agents: dict[str, Any] = {}
    subagent_descriptions = []

    # Create general-purpose agent if enabled
    if general_purpose_agent:
        general_purpose_middleware = [*default_subagent_middleware]
        if default_interrupt_on:
            general_purpose_middleware.append(HumanInTheLoopMiddleware(interrupt_on=default_interrupt_on))
        general_purpose_subagent = create_agent(
            default_model,
            system_prompt=DEFAULT_SUBAGENT_PROMPT,
            tools=default_tools,
            middleware=general_purpose_middleware,
        )
        agents["general-purpose"] = general_purpose_subagent
        subagent_descriptions.append(f"- general-purpose: {DEFAULT_GENERAL_PURPOSE_DESCRIPTION}")

    # Process custom subagents
    for agent_ in subagents:
        subagent_descriptions.append(f"- {agent_['name']}: {agent_['description']}")
        if "runnable" in agent_:
            custom_agent = cast("CompiledSubAgent", agent_)
            agents[custom_agent["name"]] = custom_agent["runnable"]
            continue
        _tools = agent_.get("tools", list(default_tools))

        subagent_model = agent_.get("model", default_model)

        _middleware = [*default_subagent_middleware, *agent_["middleware"]] if "middleware" in agent_ else [*default_subagent_middleware]

        interrupt_on = agent_.get("interrupt_on", default_interrupt_on)
        if interrupt_on:
            _middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))

        agents[agent_["name"]] = create_agent(
            subagent_model,
            system_prompt=agent_["system_prompt"],
            tools=_tools,
            middleware=_middleware,
            checkpointer=False,
        )
    return agents, subagent_descriptions


def _create_task_tool(
    *,
    default_model: str | BaseChatModel,
    default_tools: Sequence[BaseTool | Callable | dict[str, Any]],
    default_middleware: list[AgentMiddleware] | None,
    default_interrupt_on: dict[str, bool | InterruptOnConfig] | None,
    subagents: list[SubAgent | CompiledSubAgent],
    general_purpose_agent: bool,
    task_description: str | None = None,
) -> BaseTool:
    """Create a task tool for invoking subagents.

    Args:
        default_model: Default model for subagents.
        default_tools: Default tools for subagents.
        default_middleware: Middleware to apply to all subagents.
        default_interrupt_on: The tool configs to use for the default general-purpose subagent. These
            are also the fallback for any subagents that don't specify their own tool configs.
        subagents: List of subagent specifications.
        general_purpose_agent: Whether to include general-purpose agent.
        task_description: Custom description for the task tool. If `None`,
            uses default template. Supports `{available_agents}` placeholder.

    Returns:
        A StructuredTool that can invoke subagents by type.
    """
    subagent_graphs, subagent_descriptions = _get_subagents(
        default_model=default_model,
        default_tools=default_tools,
        default_middleware=default_middleware,
        default_interrupt_on=default_interrupt_on,
        subagents=subagents,
        general_purpose_agent=general_purpose_agent,
    )
    subagent_description_str = "\n".join(subagent_descriptions)

    def _return_command_with_state_update(result: dict, tool_call_id: str, subagent_type: str | None = None) -> Command:
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Extract subagent metadata if present (from RemoteGraphRunnable)
        subagent_metadata = result.pop("_subagent_metadata", None)
        if subagent_metadata:
            logger.info(f"Subagent metadata: thread_id={subagent_metadata.get('thread_id')}, graph_id={subagent_metadata.get('graph_id')}")
        
        state_update = {k: v for k, v in result.items() if k not in _EXCLUDED_STATE_KEYS}
        logger.info(f"State keys being added to parent agent: {list(state_update.keys())}")
        
        # Automatically save CSV data to files state if present
        if "table_csv" in state_update and state_update["table_csv"]:
            from datetime import UTC, datetime
            
            csv_content = state_update["table_csv"]
            # Convert CSV string to FileData format (required by FilesystemMiddleware)
            # FileData expects: {"content": [list of lines], "created_at": str, "modified_at": str}
            csv_lines = csv_content.splitlines()
            now = datetime.now(UTC).isoformat()
            
            file_data = {
                "content": csv_lines,
                "created_at": now,
                "modified_at": now,
            }
            
            # Store in the 'files' state key (which is part of the agent's state schema)
            state_update["files"] = state_update.get("files", {})
            state_update["files"]["/borrower_table.csv"] = file_data
            logger.info(f"Automatically saved table_csv to /borrower_table.csv in files state ({len(csv_lines)} lines, {len(csv_content)} chars)")
        
        # Handle messages - check if empty (e.g., when subagent returns error without messages)
        if not result.get("messages") or len(result["messages"]) == 0:
            # No messages returned - create error message from status/error fields
            error_msg = result.get("error", "Subagent returned no messages")
            status = result.get("status", "Unknown")
            message_content = f"Subagent completed with status: {status}\nError: {error_msg}"
            logger.warning(f"Subagent returned empty messages array. Status: {status}, Error: {error_msg}")
        else:
            # Get the last message - handle both Message objects and dicts
            last_message = result["messages"][-1]
            if isinstance(last_message, dict):
                # Message is serialized as a dict (from cloud subagents)
                message_content = last_message.get("content", "")
                logger.info(f"Processing dict message with content length: {len(str(message_content))}")
            else:
                # Message is a Message object (from local subagents)
                message_content = last_message.content
                logger.info(f"Processing Message object with content length: {len(str(message_content))}")
        
        # If we have subagent metadata, try to include it in a structured way
        # This allows the agent to reference the subagent's thread_id in reports
        if subagent_metadata:
            # Add metadata to state_update so it can be accessed by the agent
            subagent_call_data = {
                "subagent_name": subagent_type,
                "subagent_thread_id": subagent_metadata.get("thread_id"),
                "subagent_graph_id": subagent_metadata.get("graph_id"),
                "subagent_url": subagent_metadata.get("url"),
            }
            
            # Capture screenshot_url or web_url from the subagent result (cute subagents return these)
            # cute-screenshot returns "screenshot_url", other cute agents may return "web_url"
            screenshot_url = state_update.get("screenshot_url") or state_update.get("web_url")
            if screenshot_url:
                subagent_call_data["screenshot_url"] = screenshot_url
                # Also add to state for easy access
                state_update["screenshot_url"] = screenshot_url
                logger.info(f"Captured screenshot_url from subagent: {screenshot_url}")
            
            state_update["_last_subagent_call"] = subagent_call_data
            logger.info(f"Added subagent metadata to state: {state_update['_last_subagent_call']}")
            
            # IMPORTANT: Append subagent metadata to message content so the LLM can use it
            # The LLM doesn't see state updates directly, only the tool message content
            metadata_lines = [
                "",
                "---",
                "**Subagent Execution Metadata** (use these when calling save_step_report):",
                f"- subagent_name: {subagent_type}",
                f"- subagent_thread_id: {subagent_metadata.get('thread_id')}",
            ]
            if screenshot_url:
                metadata_lines.append(f"- screenshot_url: {screenshot_url}")
            message_content = str(message_content) + "\n".join(metadata_lines)
        
        return Command(
            update={
                **state_update,
                "messages": [ToolMessage(message_content, tool_call_id=tool_call_id)],
            }
        )

    def _validate_and_prepare_state(
        subagent_type: str, 
        description: str, 
        runtime: ToolRuntime,
        inputs: dict[str, Any] | None = None,
    ) -> tuple[Runnable, dict, dict[str, Any] | None]:
        """Validate subagent type and prepare state for invocation.
        
        Args:
            subagent_type: Type of subagent to invoke
            description: Task description for the subagent
            runtime: Tool runtime context
            inputs: Optional structured inputs to pass to the subagent
                   (e.g., {"borrower_name": "Smith", "loan_number": "12345"})
                   
        Returns:
            Tuple of (subagent_runnable, subagent_state, middleware_config)
        """
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Handle LLM sometimes passing inputs as a JSON string instead of dict
        if inputs and isinstance(inputs, str):
            try:
                inputs = json.loads(inputs)
                logger.warning(f"Parsed inputs from JSON string to dict: {inputs}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse inputs as JSON string: {inputs}")
                inputs = None
        
        if subagent_type not in subagent_graphs:
            msg = f"Error: invoked agent of type {subagent_type}, the only allowed types are {[f'`{k}`' for k in subagent_graphs]}"
            raise ValueError(msg)
        subagent = subagent_graphs[subagent_type]
        
        # Extract middleware_config from subagent if it's a RemoteGraphRunnable
        middleware_config = None
        if hasattr(subagent, 'middleware_config'):
            middleware_config = subagent.middleware_config
            logger.info(f"Found middleware_config for subagent '{subagent_type}': {middleware_config}")
        
        # Get the parent thread_id from config
        config = get_config()
        thread_id = None
        if config:
            thread_id = config.get("configurable", {}).get("thread_id")
        
        logger.info(f"Preparing state for subagent_type: {subagent_type}, thread_id: {thread_id}, inputs: {inputs}")
        
        # For cloud subagents (cute-linear, cute-finish-itp, cute-screenshot, lg-mers, lg-nmls), use minimal state with station_thread_id
        # For local subagents, use full state with messages
        if subagent_type in ["cute-linear", "cute-finish-itp", "cute-screenshot", "lg-mers", "lg-nmls"]:
            # Cloud subagents expect station_thread_id (snake_case)
            subagent_state = {"station_thread_id": str(thread_id) if thread_id else None}
            
            # Add any structured inputs provided by the caller
            if inputs:
                from datetime import UTC, datetime
                
                logger.info(f"Adding structured inputs to cloud subagent state: {inputs}")
                subagent_state.update(inputs)
                
                # Automatically add decision_timestamp if not already provided
                if "decision_timestamp" not in subagent_state:
                    subagent_state["decision_timestamp"] = datetime.now(UTC).isoformat()
                
                logger.info(f"✅ Successfully prepared state with inputs: {list(inputs.keys())}")
            
            logger.info(f"Cloud subagent state prepared: {subagent_state}")
        else:
            # Local subagents get full state with messages
            subagent_state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
            # Local subagents require a system message first, then the human message
            subagent_state["messages"] = [
                SystemMessage(content="You are a specialized subagent. Complete the task described by the user."),
                HumanMessage(content=description)
            ]
            # Add any structured inputs to local subagent state as well
            if inputs:
                logger.info(f"Adding structured inputs to local subagent state: {inputs}")
                subagent_state.update(inputs)
            logger.info(f"Local subagent state prepared with {len(subagent_state.get('messages', []))} messages")
        
        return subagent, subagent_state, middleware_config

    # Use custom description if provided, otherwise use default template
    if task_description is None:
        task_description = TASK_TOOL_DESCRIPTION.format(available_agents=subagent_description_str)
    elif "{available_agents}" in task_description:
        # If custom description has placeholder, format with agent descriptions
        task_description = task_description.format(available_agents=subagent_description_str)

    def task(
        description: str,
        subagent_type: str,
        inputs: dict[str, Any] | str | None = None,
        runtime: ToolRuntime = None,
    ) -> str | Command:
        """Invoke a subagent to handle a complex task.
        
        Args:
            description: Task description for the subagent
            subagent_type: Type of subagent to invoke
            inputs: Optional structured inputs as a dictionary or JSON string
                   (e.g., {"borrower_name": "Smith", "loan_number": "12345"})
            runtime: Tool runtime context (auto-injected)
        """
        import logging
        import json
        import os
        logger = logging.getLogger(__name__)
        
        # Handle LLM passing inputs as a JSON string instead of dict
        if inputs and isinstance(inputs, str):
            try:
                inputs = json.loads(inputs)
                logger.warning(f"[TASK] Parsed inputs from JSON string to dict: {inputs}")
            except json.JSONDecodeError:
                logger.error(f"[TASK] Failed to parse inputs as JSON string: {inputs}")
                inputs = None
        
        # If no inputs provided, check pending_subagent_inputs in state
        # This allows collect_* tools to stage inputs for subagents
        if not inputs and runtime and hasattr(runtime, "state") and runtime.state:
            pending_inputs = runtime.state.get("pending_subagent_inputs", {})
            if subagent_type in pending_inputs:
                inputs = pending_inputs[subagent_type]
                logger.info(f"[TASK] Using staged inputs from state for {subagent_type}: {inputs}")
        
        subagent, subagent_state, middleware_config = _validate_and_prepare_state(subagent_type, description, runtime, inputs)
        
        # Handle Server Middleware if configured
        server_config = middleware_config.get("server", {}) if middleware_config else {}
        station_agent = None
        server_loaded = False
        
        if server_config:
            print(f"🔧 [SubagentMiddleware] Server coordination enabled for subagent: {subagent_type}")
            server_id = server_config.get("server_id", "BrowserAgent")
            checkpoint = server_config.get("checkpoint", "Chrome")
            server_index = server_config.get("server_index", 0)
            server_task_type = server_config.get("server_task_type", subagent_type)
            
            try:
                from cuteagent import StationAgent  # type: ignore[import-not-found]
                
                station_token = os.getenv("STATION_TOKEN")
                if not station_token:
                    raise ValueError("STATION_TOKEN environment variable required for server coordination")
                
                # Initialize StationAgent with server_id as station_thread_id
                print(f"🔌 [SubagentMiddleware] Initializing StationAgent for server: {server_id}")
                config = runtime.config or {}
                graph_thread_id = config.get("configurable", {}).get("thread_id", "subagent-task")
                
                num_servers = 4
                initial_server_state = {
                    "server": ["idle"] * num_servers,
                    "serverThread": ["idle"] * num_servers,
                    "serverCheckpoint": ["Chrome"] * num_servers,
                    "serverTaskType": ["taskPlaceholder"] * num_servers,
                }
                
                station_agent = StationAgent(
                    station_thread_id=server_id,  # server_id IS the station_thread_id
                    graph_thread_id=graph_thread_id,
                    token=station_token,
                    initial_state=initial_server_state,
                    langgraph_token=os.getenv("LANGGRAPH_TOKEN"),
                )
                
                print(f"🔄 [SubagentMiddleware] Loading server {server_id}[{server_index}]...")
                load_result = station_agent.server.load(
                    serverThreadId=server_id,
                    serverCheckpoint=checkpoint,
                    serverIndex=server_index,
                    serverTaskType=server_task_type,
                )
                
                print(f"   ← Load result: {load_result}")
                
                if load_result.get("status") == "loaded":
                    print(f"✅ [SubagentMiddleware] Server loaded for subagent {subagent_type}")
                    server_loaded = True
                else:
                    print(f"⚠️  [SubagentMiddleware] Server load failed: {load_result}")
                    
            except Exception as e:
                print(f"❌ [SubagentMiddleware] Server coordination error: {e}")
                logger.error(f"Server coordination error for subagent {subagent_type}: {e}")
        
        # Execute subagent
        try:
            result = subagent.invoke(subagent_state)
        finally:
            # Unload server if it was loaded
            if server_loaded and station_agent:
                try:
                    print(f"🔓 [SubagentMiddleware] Unloading server {server_id}[{server_index}]...")
                    unload_result = station_agent.server.unload(checkpoint=checkpoint, index=server_index)
                    print(f"✅ [SubagentMiddleware] Server unloaded: {unload_result}")
                except Exception as e:
                    print(f"⚠️  [SubagentMiddleware] Failed to unload server: {e}")
                    logger.error(f"Failed to unload server: {e}")
        
        # Handle Station Middleware if configured (AFTER subagent completes)
        station_config = middleware_config.get("station", {}) if middleware_config else {}
        if station_config:
            print(f"📊 [SubagentMiddleware] Station syncing enabled for subagent: {subagent_type}")
            variables_to_sync = station_config.get("variables", [])
            station_id = station_config.get("station_id")
            
            # station_id must be provided in middleware_config
            if not station_id:
                print(f"⚠️  [SubagentMiddleware] No station_id in config - skipping station sync")
            else:
                print(f"🔗 [SubagentMiddleware] Using station_id from config: {station_id}")
            
            if station_id and variables_to_sync:
                try:
                    from cuteagent import StationAgent  # type: ignore[import-not-found]
                    
                    station_token = os.getenv("STATION_TOKEN")
                    if not station_token:
                        raise ValueError("STATION_TOKEN required for station syncing")
                    
                    # Initialize StationAgent for syncing (separate from server coordination)
                    print(f"🔌 [SubagentMiddleware] Initializing StationAgent for syncing to station: {station_id}")
                    config = runtime.config or {}
                    graph_thread_id = config.get("configurable", {}).get("thread_id", "subagent-sync")
                    
                    sync_station = StationAgent(
                        station_thread_id=station_id,  # For station sync, use the actual station_id
                        graph_thread_id=graph_thread_id,
                        token=station_token,
                        initial_state=None,  # Connect to existing station
                        langgraph_token=os.getenv("LANGGRAPH_TOKEN"),
                    )
                    
                    # Sync variables from subagent result
                    synced_vars = []
                    for var_name in variables_to_sync:
                        if var_name in result:
                            var_value = result[var_name]
                            sync_station.state.set(var_name, var_value)
                            synced_vars.append(var_name)
                            print(f"  ✅ Synced '{var_name}' to station '{station_id}'")
                    
                    if synced_vars:
                        print(f"📊 [SubagentMiddleware] Synced {len(synced_vars)} variables: {synced_vars}")
                    else:
                        print(f"⚠️  [SubagentMiddleware] No variables found in result to sync")
                        
                except Exception as e:
                    print(f"❌ [SubagentMiddleware] Station syncing error: {e}")
                    logger.error(f"Station syncing error for subagent {subagent_type}: {e}")
            else:
                print(f"⚠️  [SubagentMiddleware] Skipping station sync (station_id={station_id}, variables={variables_to_sync})")
        
        # Log the full response from subagent
        logger.info(f"=== Response from {subagent_type} subagent ===")
        logger.info(f"Result keys: {list(result.keys())}")
        if "messages" in result:
            logger.info(f"Number of messages: {len(result['messages'])}")
            for i, msg in enumerate(result["messages"]):
                if isinstance(msg, dict):
                    logger.info(f"Message {i}: type={msg.get('type')}, content_length={len(str(msg.get('content', '')))}")
                    logger.info(f"Message {i} content preview: {str(msg.get('content', ''))[:200]}...")
                else:
                    logger.info(f"Message {i}: type={msg.type}, content_length={len(str(msg.content))}")
                    logger.info(f"Message {i} content preview: {str(msg.content)[:200]}...")
        logger.info(f"Full result (truncated): {json.dumps(result, default=str, indent=2)[:1000]}...")
        
        if not runtime.tool_call_id:
            value_error_msg = "Tool call ID is required for subagent invocation"
            raise ValueError(value_error_msg)
        return _return_command_with_state_update(result, runtime.tool_call_id, subagent_type)

    async def atask(
        description: str,
        subagent_type: str,
        inputs: dict[str, Any] | str | None = None,
        runtime: ToolRuntime = None,
    ) -> str | Command:
        """Async invoke a subagent to handle a complex task.
        
        Args:
            description: Task description for the subagent
            subagent_type: Type of subagent to invoke
            inputs: Optional structured inputs as a dictionary or JSON string
                   (e.g., {"borrower_name": "Smith", "loan_number": "12345"})
            runtime: Tool runtime context (auto-injected)
        """
        import logging
        import json
        import os
        import asyncio
        logger = logging.getLogger(__name__)
        
        # Handle LLM passing inputs as a JSON string instead of dict
        if inputs and isinstance(inputs, str):
            try:
                inputs = json.loads(inputs)
                logger.warning(f"[TASK ASYNC] Parsed inputs from JSON string to dict: {inputs}")
            except json.JSONDecodeError:
                logger.error(f"[TASK ASYNC] Failed to parse inputs as JSON string: {inputs}")
                inputs = None
        
        # If no inputs provided, check pending_subagent_inputs in state
        # This allows collect_* tools to stage inputs for subagents
        if not inputs and runtime and hasattr(runtime, "state") and runtime.state:
            pending_inputs = runtime.state.get("pending_subagent_inputs", {})
            if subagent_type in pending_inputs:
                inputs = pending_inputs[subagent_type]
                logger.info(f"[TASK ASYNC] Using staged inputs from state for {subagent_type}: {inputs}")
        
        subagent, subagent_state, middleware_config = _validate_and_prepare_state(subagent_type, description, runtime, inputs)
        
        # Handle Server Middleware if configured
        server_config = middleware_config.get("server", {}) if middleware_config else {}
        station_agent = None
        server_loaded = False
        
        if server_config:
            print(f"🔧 [SubagentMiddleware ASYNC] Server coordination enabled for subagent: {subagent_type}")
            server_id = server_config.get("server_id", "BrowserAgent")
            checkpoint = server_config.get("checkpoint", "Chrome")
            server_index = server_config.get("server_index", 0)
            server_task_type = server_config.get("server_task_type", subagent_type)
            
            try:
                # Import cuteagent in a thread to avoid blocking call during import
                # (cuteagent imports huggingface_hub which has blocking file reads)
                def _import_and_init_station_agent(
                    server_id: str,
                    graph_thread_id: str,
                    station_token: str,
                    initial_state: dict,
                    langgraph_token: str | None,
                ):
                    from cuteagent import StationAgent  # type: ignore[import-not-found]
                    return StationAgent(
                        station_thread_id=server_id,
                        graph_thread_id=graph_thread_id,
                        token=station_token,
                        initial_state=initial_state,
                        langgraph_token=langgraph_token,
                        current_graph_url=None,
                        current_graph_assistant_id=None,
                    )
                
                station_token = os.getenv("STATION_TOKEN")
                if not station_token:
                    raise ValueError("STATION_TOKEN environment variable required for server coordination")
                
                # Initialize StationAgent with server_id as station_thread_id
                print(f"🔌 [SubagentMiddleware ASYNC] Initializing StationAgent for server: {server_id}")
                config = runtime.config or {}
                graph_thread_id = config.get("configurable", {}).get("thread_id", "subagent-task")
                
                num_servers = 4
                initial_server_state = {
                    "server": ["idle"] * num_servers,
                    "serverThread": ["idle"] * num_servers,
                    "serverCheckpoint": ["Chrome"] * num_servers,
                    "serverTaskType": ["taskPlaceholder"] * num_servers,
                }
                
                # Run import and initialization in a thread to avoid blocking
                station_agent = await asyncio.to_thread(
                    _import_and_init_station_agent,
                    server_id=server_id,
                    graph_thread_id=graph_thread_id,
                    station_token=station_token,
                    initial_state=initial_server_state,
                    langgraph_token=os.getenv("LANGGRAPH_TOKEN"),
                )
                
                print(f"🔄 [SubagentMiddleware ASYNC] Loading server {server_id}[{server_index}]...")
                load_result = await asyncio.to_thread(
                    station_agent.server.load,
                    serverThreadId=server_id,
                    serverCheckpoint=checkpoint,
                    serverIndex=server_index,
                    serverTaskType=server_task_type,
                )
                
                print(f"   ← Load result: {load_result}")
                
                if load_result.get("status") == "loaded":
                    print(f"✅ [SubagentMiddleware ASYNC] Server loaded for subagent {subagent_type}")
                    server_loaded = True
                else:
                    print(f"⚠️  [SubagentMiddleware ASYNC] Server load failed: {load_result}")
                    
            except Exception as e:
                print(f"❌ [SubagentMiddleware ASYNC] Server coordination error: {e}")
                logger.error(f"Server coordination error for subagent {subagent_type}: {e}")
        
        # Execute subagent
        try:
            result = await subagent.ainvoke(subagent_state)
        finally:
            # Unload server if it was loaded
            if server_loaded and station_agent:
                try:
                    print(f"🔓 [SubagentMiddleware ASYNC] Unloading server {server_id}[{server_index}]...")
                    unload_result = await asyncio.to_thread(station_agent.server.unload, checkpoint=checkpoint, index=server_index)
                    print(f"✅ [SubagentMiddleware ASYNC] Server unloaded: {unload_result}")
                except Exception as e:
                    print(f"⚠️  [SubagentMiddleware ASYNC] Failed to unload server: {e}")
                    logger.error(f"Failed to unload server: {e}")
        
        # Handle Station Middleware if configured (AFTER subagent completes)
        station_config = middleware_config.get("station", {}) if middleware_config else {}
        if station_config:
            print(f"📊 [SubagentMiddleware ASYNC] Station syncing enabled for subagent: {subagent_type}")
            variables_to_sync = station_config.get("variables", [])
            sync_station_id = station_config.get("station_id")
            
            # If no station_id in config, try to get from runtime state or config
            if not sync_station_id:
                # Check runtime state first
                state = getattr(runtime, "state", {})
                sync_station_id = state.get("station_thread_id") or state.get("stationThreadId")
                
                # If still not found, get from runtime config (parent's thread_id)
                if not sync_station_id:
                    config = runtime.config or {}
                    sync_station_id = config.get("configurable", {}).get("thread_id")
                
                if sync_station_id:
                    print(f"🔗 [SubagentMiddleware ASYNC] Found station_id from runtime: {sync_station_id}")
                else:
                    print(f"⚠️  [SubagentMiddleware ASYNC] No station_id found in config, state, or runtime")
            else:
                print(f"🔗 [SubagentMiddleware ASYNC] Using station_id from config: {sync_station_id}")
            
            if sync_station_id and variables_to_sync:
                try:
                    # Import cuteagent in a thread to avoid blocking call during import
                    # (cuteagent imports huggingface_hub which has blocking file reads)
                    def _import_and_init_sync_station(
                        station_thread_id: str,
                        graph_thread_id: str,
                        station_token: str,
                        langgraph_token: str | None,
                    ):
                        from cuteagent import StationAgent  # type: ignore[import-not-found]
                        return StationAgent(
                            station_thread_id=station_thread_id,
                            graph_thread_id=graph_thread_id,
                            token=station_token,
                            initial_state=None,  # Connect to existing station
                            langgraph_token=langgraph_token,
                            current_graph_url=None,
                            current_graph_assistant_id=None,
                        )
                    
                    station_token = os.getenv("STATION_TOKEN")
                    if not station_token:
                        raise ValueError("STATION_TOKEN required for station syncing")
                    
                    # Initialize StationAgent for syncing (separate from server coordination)
                    print(f"🔌 [SubagentMiddleware ASYNC] Initializing StationAgent for syncing to station: {sync_station_id}")
                    config = runtime.config or {}
                    graph_thread_id = config.get("configurable", {}).get("thread_id", "subagent-sync")
                    
                    # Run import and initialization in a thread to avoid blocking
                    sync_station = await asyncio.to_thread(
                        _import_and_init_sync_station,
                        station_thread_id=sync_station_id,
                        graph_thread_id=graph_thread_id,
                        station_token=station_token,
                        langgraph_token=os.getenv("LANGGRAPH_TOKEN"),
                    )
                    
                    # Sync variables from subagent result
                    synced_vars = []
                    for var_name in variables_to_sync:
                        if var_name in result:
                            var_value = result[var_name]
                            await asyncio.to_thread(sync_station.state.set, var_name, var_value)
                            synced_vars.append(var_name)
                            print(f"  ✅ Synced '{var_name}' to station '{sync_station_id}'")
                    
                    if synced_vars:
                        print(f"📊 [SubagentMiddleware ASYNC] Synced {len(synced_vars)} variables: {synced_vars}")
                    else:
                        print(f"⚠️  [SubagentMiddleware ASYNC] No variables found in result to sync")
                        
                except Exception as e:
                    print(f"❌ [SubagentMiddleware ASYNC] Station syncing error: {e}")
                    logger.error(f"Station syncing error for subagent {subagent_type}: {e}")
            else:
                print(f"⚠️  [SubagentMiddleware ASYNC] Skipping station sync (station_id={sync_station_id}, variables={variables_to_sync})")
        
        # Log the full response from subagent
        logger.info(f"=== Response from {subagent_type} subagent ===")
        logger.info(f"Result keys: {list(result.keys())}")
        if "messages" in result:
            logger.info(f"Number of messages: {len(result['messages'])}")
            for i, msg in enumerate(result["messages"]):
                if isinstance(msg, dict):
                    logger.info(f"Message {i}: type={msg.get('type')}, content_length={len(str(msg.get('content', '')))}")
                    logger.info(f"Message {i} content preview: {str(msg.get('content', ''))[:200]}...")
                else:
                    logger.info(f"Message {i}: type={msg.type}, content_length={len(str(msg.content))}")
                    logger.info(f"Message {i} content preview: {str(msg.content)[:200]}...")
        logger.info(f"Full result (truncated): {json.dumps(result, default=str, indent=2)[:1000]}...")
        
        if not runtime.tool_call_id:
            value_error_msg = "Tool call ID is required for subagent invocation"
            raise ValueError(value_error_msg)
        return _return_command_with_state_update(result, runtime.tool_call_id, subagent_type)

    task_tool = StructuredTool.from_function(
        name="task",
        func=task,
        coroutine=atask,
        description=task_description,
    )
    # Rebuild the Pydantic model to resolve forward references (needed for Python 3.14+)
    if hasattr(task_tool, 'args_schema') and task_tool.args_schema is not None:
        try:
            task_tool.args_schema.model_rebuild()
        except Exception:
            pass  # Ignore if model_rebuild fails or doesn't exist
    return task_tool


class SubAgentMiddleware(AgentMiddleware):
    """Middleware for providing subagents to an agent via a `task` tool.

    This  middleware adds a `task` tool to the agent that can be used to invoke subagents.
    Subagents are useful for handling complex tasks that require multiple steps, or tasks
    that require a lot of context to resolve.

    A chief benefit of subagents is that they can handle multi-step tasks, and then return
    a clean, concise response to the main agent.

    Subagents are also great for different domains of expertise that require a narrower
    subset of tools and focus.

    This middleware comes with a default general-purpose subagent that can be used to
    handle the same tasks as the main agent, but with isolated context.

    Args:
        default_model: The model to use for subagents.
            Can be a LanguageModelLike or a dict for init_chat_model.
        default_tools: The tools to use for the default general-purpose subagent.
        default_middleware: Default middleware to apply to all subagents. If `None` (default),
            no default middleware is applied. Pass a list to specify custom middleware.
        default_interrupt_on: The tool configs to use for the default general-purpose subagent. These
            are also the fallback for any subagents that don't specify their own tool configs.
        subagents: A list of additional subagents to provide to the agent.
        system_prompt: Full system prompt override. When provided, completely replaces
            the agent's system prompt.
        general_purpose_agent: Whether to include the general-purpose agent. Defaults to `True`.
        task_description: Custom description for the task tool. If `None`, uses the
            default description template.

    Example:
        ```python
        from langchain.agents.middleware.subagents import SubAgentMiddleware
        from langchain.agents import create_agent

        # Basic usage with defaults (no default middleware)
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[
                SubAgentMiddleware(
                    default_model="openai:gpt-4o",
                    subagents=[],
                )
            ],
        )

        # Add custom middleware to subagents
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[
                SubAgentMiddleware(
                    default_model="openai:gpt-4o",
                    default_middleware=[TodoListMiddleware()],
                    subagents=[],
                )
            ],
        )
        ```
    """

    def __init__(
        self,
        *,
        default_model: str | BaseChatModel,
        default_tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
        default_middleware: list[AgentMiddleware] | None = None,
        default_interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
        subagents: list[SubAgent | CompiledSubAgent] | None = None,
        system_prompt: str | None = TASK_SYSTEM_PROMPT,
        general_purpose_agent: bool = True,
        task_description: str | None = None,
    ) -> None:
        """Initialize the SubAgentMiddleware."""
        super().__init__()
        self.system_prompt = system_prompt
        task_tool = _create_task_tool(
            default_model=default_model,
            default_tools=default_tools or [],
            default_middleware=default_middleware,
            default_interrupt_on=default_interrupt_on,
            subagents=subagents or [],
            general_purpose_agent=general_purpose_agent,
            task_description=task_description,
        )
        self.tools = [task_tool]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Update the system prompt to include instructions on using subagents."""
        if self.system_prompt is not None:
            request.system_prompt = request.system_prompt + "\n\n" + self.system_prompt if request.system_prompt else self.system_prompt
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """(async) Update the system prompt to include instructions on using subagents."""
        if self.system_prompt is not None:
            request.system_prompt = request.system_prompt + "\n\n" + self.system_prompt if request.system_prompt else self.system_prompt
        return await handler(request)
