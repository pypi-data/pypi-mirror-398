"""Planning middleware for agents with configurable planning strategies."""
# ruff: noqa: E501

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command
from typing_extensions import NotRequired, TypedDict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain.tools import InjectedToolCallId


class Todo(TypedDict):
    """A single todo item with content and status."""

    content: str
    """The content/description of the todo item."""

    status: Literal["pending", "in_progress", "completed"]
    """The current status of the todo item."""


class PlanningState(AgentState):
    """State schema for the planning middleware."""

    todos: NotRequired[list[Todo]]
    """List of todo items for tracking task progress."""


def _load_planner_prompt(agent_type: str) -> str:
    """Load planner prompt from markdown file.
    
    Args:
        agent_type: The agent type (ITP-Princeton, DrawDoc-AWM, research)
        
    Returns:
        The planner prompt content
    """
    # Map agent types to file names
    file_map = {
        "ITP-Princeton": "itp_princeton.md",
        "DrawDoc-AWM": "drawdoc_awm.md",
        "research": "research.md",
    }
    
    filename = file_map.get(agent_type)
    if not filename:
        return ""
    
    # Get the path to the planner prompts directory
    prompts_dir = Path(__file__).parent / "planner_prompts"
    prompt_file = prompts_dir / filename
    
    if prompt_file.exists():
        return prompt_file.read_text()
    
    # Fallback to hardcoded prompts if file doesn't exist
    return DEFAULT_PLANNING_PROMPTS.get(agent_type, "")


# Default planning prompts for different agent types (fallback)
DEFAULT_PLANNING_PROMPTS = {
    "ITP-Princeton": """## `write_todos` - ITP-Princeton Planning

You have access to the `write_todos` tool to help you manage complex objectives for the ITP-Princeton copilot.
Use this tool to break down complex tasks into clear, actionable steps.

Planning approach:
1. Start with high-level objectives
2. Break down into specific, measurable tasks
3. Mark tasks as in_progress before starting work
4. Update status in real-time as you progress
5. Mark completed immediately after finishing

Task management:
- Create todos for multi-step objectives (3+ steps)
- Keep at least one task in_progress
- Remove irrelevant tasks as scope changes
- Don't batch completions - update in real-time

Important: Use this tool for complex objectives that require careful planning and tracking. Skip it for simple, straightforward tasks.""",

    "DrawDoc-AWM": """## `write_todos` - DrawDoc-AWM Planning

You have access to the `write_todos` tool to help you manage document drawing and annotation workflows.
Use this tool to break down document processing tasks into phases.

Planning approach for DrawDoc-AWM:
1. Document analysis and understanding
2. Annotation and markup steps
3. Drawing and visual element creation
4. Review and quality assurance
5. Export and delivery

Task management:
- Create todos for each document or section
- Track annotation tasks separately from drawing tasks
- Mark quality checks as distinct milestones
- Always have at least one task in_progress

Important: Use this tool for complex document workflows with multiple stages. Skip it for simple single-document operations.""",

    "research": """## `write_todos` - Research Planning

You have access to the `write_todos` tool to help you manage complex research objectives.
Use this tool to break down research tasks into:
1. Information gathering phases (identify sources, search strategies)
2. Data collection and analysis steps
3. Synthesis and reporting milestones

For research tasks:
- Create todos for different research angles or subtopics
- Mark information-gathering tasks as you complete searches
- Track synthesis tasks separately from data collection
- Always have at least one task in_progress to show research momentum

Important: Use this tool for complex research that requires multiple searches, comparisons, or deep dives. Skip it for simple lookups.""",
}

# Default tool description for write_todos
DEFAULT_TOOL_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.

Only use this tool if you think it will be helpful in staying organized. If the user's request is trivial and takes less than 3 steps, it is better to NOT use this tool and just do the task directly.

## When to Use This Tool
Use this tool in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. The plan may need future revisions or updates based on results from the first few steps

## How to Use This Tool
1. When you start working on a task - Mark it as in_progress BEFORE beginning work.
2. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation.
3. You can also update future tasks, such as deleting them if they are no longer necessary, or adding new tasks that are necessary. Don't change previously completed tasks.
4. You can make several updates to the todo list at once. For example, when you complete a task, you can mark the next task you need to start as in_progress.

## When NOT to Use This Tool
It is important to skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (you can have multiple tasks in_progress at a time if they are not related to each other and can be run in parallel)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely
   - IMPORTANT: When you write this todo list, you should mark your first task (or tasks) as in_progress immediately!.
   - IMPORTANT: Unless all tasks are completed, you should always have at least one task in_progress to show the user that you are working on something.

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - There are unresolved issues or errors
     - Work is partial or incomplete
     - You encountered blockers that prevent completion
     - You couldn't find necessary resources or dependencies
     - Quality standards haven't been met

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully
Remember: If you only need to make a few tool calls to complete a task, and it is clear what you need to do, it is better to just do the task directly and NOT call this tool at all."""


class PlanningMiddleware(AgentMiddleware):
    """Middleware that provides configurable planning capabilities to agents.

    This middleware extends basic todo list functionality with planning strategies
    tailored to different types of copilot agents (ITP-Princeton, DrawDoc-AWM, research).

    The middleware can be configured with different planning prompts based on the agent type.

    Example:
        ```python
        from deepagents.middleware.planning import PlanningMiddleware
        from langchain.agents import create_agent

        # ITP-Princeton agent
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[
                PlanningMiddleware(
                    agent_type="ITP-Princeton"
                )
            ]
        )

        # Research agent
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[
                PlanningMiddleware(
                    agent_type="research"
                )
            ]
        )
        ```

    Args:
        agent_type: Type of agent this planning middleware is for.
            Options: "ITP-Princeton", "DrawDoc-AWM", "research"
        system_prompt: Custom system prompt override. If provided, overrides
            the default prompt for the agent_type.
        tool_description: Custom tool description override. If provided, overrides
            the default tool description.
    """

    state_schema = PlanningState

    def __init__(
        self,
        *,
        agent_type: Literal["ITP-Princeton", "DrawDoc-AWM", "research"] = "ITP-Princeton",
        system_prompt: str | None = None,
        tool_description: str | None = None,
    ) -> None:
        """Initialize the PlanningMiddleware with configurable planning strategy.

        Args:
            agent_type: Type of agent (ITP-Princeton, DrawDoc-AWM, research).
            system_prompt: Optional custom system prompt.
            tool_description: Optional custom tool description.
        """
        super().__init__()
        self.agent_type = agent_type

        # Use custom prompts if provided, otherwise load from file or use defaults
        self.system_prompt = system_prompt or _load_planner_prompt(agent_type)
        self.tool_description = tool_description or DEFAULT_TOOL_DESCRIPTION

        # Dynamically create the write_todos tool with the custom description
        @tool(description=self.tool_description)
        def write_todos(
            todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
        ) -> Command:
            """Create and manage a structured task list for your current work session."""
            return Command(
                update={
                    "todos": todos,
                    "messages": [
                        ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
                    ],
                }
            )

        self.tools = [write_todos]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """Update the system prompt to include the planning system prompt."""
        request.system_prompt = (
            request.system_prompt + "\n\n" + self.system_prompt
            if request.system_prompt
            else self.system_prompt
        )
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Update the system prompt to include the planning system prompt (async version)."""
        request.system_prompt = (
            request.system_prompt + "\n\n" + self.system_prompt
            if request.system_prompt
            else self.system_prompt
        )
        return await handler(request)
