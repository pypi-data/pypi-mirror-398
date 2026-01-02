"""Middleware for syncing tool outputs with StationAgent from CuteAgent library.

This middleware is called AFTER tool execution to sync specified variables
from the tool's output to a StationAgent shared state system.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools import ToolRuntime
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StationMiddleware(AgentMiddleware):
    """Middleware for syncing tool outputs to StationAgent shared state.
    
    This middleware runs AFTER a tool completes execution and syncs specified
    variables from the tool's output dictionary to a StationAgent instance.
    
    Tools opt-in by adding configuration to their metadata:
    ```python
    tool.metadata = {
        "station_middleware": {
            "variables": ["borrower_names", "loan_data"],
            "station_id": "station-thread-123"
        }
    }
    ```
    
    Environment Variables Required:
        - STATION_TOKEN: Authentication token for SharedState API
        - LANGGRAPH_TOKEN (optional): For pause/unpause functionality
    
    The middleware will:
    1. Check if tool has station_middleware config in metadata
    2. Initialize StationAgent with station_id from config
    3. For each variable in the variables list:
       - Check if it exists as a top-level key in tool output dict
       - If found, sync it to StationAgent using state.set()
       - If not found, skip it (log warning)
    4. If any errors occur (missing env vars, connection failures):
       - Return error message as part of tool output
       - Allow graph execution to continue
    
    Example:
        ```python
        from copilotagent.middleware.station_middleware import StationMiddleware
        from langchain.agents import create_agent
        
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[StationMiddleware()],
            tools=[...],
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize the StationMiddleware."""
        self.name = "StationMiddleware"

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Wrap tool execution to sync outputs to StationAgent after completion.
        
        Args:
            request: The tool call request containing tool name and arguments
            handler: The function that executes the actual tool
            
        Returns:
            ToolMessage or Command with potentially modified output if errors occur
        """
        # First, execute the tool normally
        response = handler(request)
        
        # Get runtime from request
        runtime = request.runtime
        if not runtime:
            return response
        
        # Check if this tool has station_middleware configuration
        tool_metadata = getattr(runtime.tool, "metadata", {})
        station_config = tool_metadata.get("station_middleware")
        
        if not station_config:
            # Tool doesn't use station middleware, return response as-is
            return response
        
        # Tool opted in to station middleware
        logger.info(f"Station middleware activated for tool: {request.name}")
        
        # Extract configuration
        variables_to_sync = station_config.get("variables", [])
        station_id = station_config.get("station_id")
        
        if not station_id:
            error_msg = (
                "ERROR: Station middleware configuration missing 'station_id'. "
                "Please report this error to a human. Tool output may not be synced to shared state."
            )
            logger.error(error_msg)
            # Append error to response output
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        if not variables_to_sync:
            logger.warning(f"Station middleware enabled but no variables specified for tool {request.name}")
            return response
        
        # Check for required environment variables
        station_token = os.getenv("STATION_TOKEN")
        if not station_token:
            error_msg = (
                "ERROR: STATION_TOKEN environment variable not found. "
                "Cannot sync tool outputs to StationAgent shared state. "
                "Please ensure .env file contains STATION_TOKEN. "
                "Report this error to a human."
            )
            logger.error(error_msg)
            # Append error to response output
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        # Initialize StationAgent
        try:
            # Import here to avoid dependency issues if cuteagent not installed
            from cuteagent import StationAgent  # type: ignore[import-not-found]
            
            # Get thread_id from runtime config if available
            config = getattr(runtime, "config", {})
            configurable = config.get("configurable", {})
            graph_thread_id = configurable.get("thread_id", str(uuid.uuid4()))
            
            # Get optional LangGraph token for advanced features
            langgraph_token = os.getenv("LANGGRAPH_TOKEN")
            
            logger.info(f"Initializing StationAgent for station_id: {station_id}")
            
            # Initialize StationAgent (connects to existing shared state)
            station_agent = StationAgent(
                station_thread_id=station_id,
                graph_thread_id=graph_thread_id,
                token=station_token,
                initial_state=None,  # Connect to existing state, don't create new
                langgraph_token=langgraph_token,
                current_graph_url=None,  # Not needed for simple state sync
                current_graph_assistant_id=None,  # Not needed for simple state sync
            )
            
            logger.info("✅ StationAgent connection established")
            
        except ImportError:
            error_msg = (
                "ERROR: cuteagent library not installed. "
                "Cannot use Station middleware. "
                "Install with: pip install 'copilotagent[hitl]' "
                "Report this error to a human."
            )
            logger.error(error_msg)
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        except Exception as e:
            error_msg = (
                f"ERROR: Failed to initialize StationAgent: {str(e)} "
                f"Station ID: {station_id}. "
                "Report this error to a human."
            )
            logger.error(error_msg, exc_info=True)
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        # Parse tool output - it should be a dictionary
        tool_output = response.output
        if not isinstance(tool_output, dict):
            logger.warning(
                f"Tool output is not a dictionary (type: {type(tool_output)}). "
                f"Station middleware requires dict output to sync variables. Skipping sync."
            )
            return response
        
        # Sync variables from tool output to StationAgent
        synced_vars = []
        skipped_vars = []
        
        for var_name in variables_to_sync:
            if var_name in tool_output:
                # Variable exists in tool output - sync it to StationAgent
                var_value = tool_output[var_name]
                try:
                    station_agent.state.set(var_name, var_value)
                    synced_vars.append(var_name)
                    logger.info(f"✅ Synced variable '{var_name}' to StationAgent (value type: {type(var_value).__name__})")
                except Exception as e:
                    error_msg = f"Failed to sync variable '{var_name}': {str(e)}"
                    logger.error(error_msg)
                    skipped_vars.append(f"{var_name} (error: {str(e)})")
            else:
                # Variable not in tool output - skip it
                skipped_vars.append(var_name)
                logger.warning(f"Variable '{var_name}' not found in tool output. Skipping.")
        
        # Log summary
        if synced_vars:
            logger.info(f"Station middleware synced {len(synced_vars)} variables: {synced_vars}")
        if skipped_vars:
            logger.info(f"Station middleware skipped {len(skipped_vars)} variables: {skipped_vars}")
        
        # Add sync summary to response output if it's a string
        if isinstance(response.output, str) and (synced_vars or skipped_vars):
            sync_summary = f"\n\n[Station Sync: {len(synced_vars)} variables updated"
            if skipped_vars:
                sync_summary += f", {len(skipped_vars)} skipped"
            sync_summary += "]"
            response.output = f"{response.output}{sync_summary}"
        
        return response

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Async version of wrap_tool_call.
        
        Args:
            request: The tool call request containing tool name and arguments
            handler: The async function that executes the actual tool
            
        Returns:
            ToolMessage or Command with potentially modified output if errors occur
        """
        # First, execute the tool normally
        response = await handler(request)
        
        # Get runtime from request
        runtime = request.runtime
        if not runtime:
            return response
        
        # Check if this tool has station_middleware configuration
        tool_metadata = getattr(runtime.tool, "metadata", {})
        station_config = tool_metadata.get("station_middleware")
        
        if not station_config:
            # Tool doesn't use station middleware, return response as-is
            return response
        
        # Tool opted in to station middleware
        logger.info(f"Station middleware activated for tool: {request.name}")
        
        # Extract configuration
        variables_to_sync = station_config.get("variables", [])
        station_id = station_config.get("station_id")
        
        if not station_id:
            error_msg = (
                "ERROR: Station middleware configuration missing 'station_id'. "
                "Please report this error to a human. Tool output may not be synced to shared state."
            )
            logger.error(error_msg)
            # Append error to response output
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        if not variables_to_sync:
            logger.warning(f"Station middleware enabled but no variables specified for tool {request.name}")
            return response
        
        # Check for required environment variables
        station_token = os.getenv("STATION_TOKEN")
        if not station_token:
            error_msg = (
                "ERROR: STATION_TOKEN environment variable not found. "
                "Cannot sync tool outputs to StationAgent shared state. "
                "Please ensure .env file contains STATION_TOKEN. "
                "Report this error to a human."
            )
            logger.error(error_msg)
            # Append error to response output
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        # Initialize StationAgent
        try:
            # Import here to avoid dependency issues if cuteagent not installed
            import asyncio
            
            # Import and init cuteagent in a thread to avoid blocking call during import
            # (cuteagent imports huggingface_hub which has blocking file reads)
            def _import_and_init_station_agent(
                station_id: str,
                graph_thread_id: str,
                station_token: str,
                langgraph_token: str | None,
            ):
                from cuteagent import StationAgent  # type: ignore[import-not-found]
                return StationAgent(
                    station_thread_id=station_id,
                    graph_thread_id=graph_thread_id,
                    token=station_token,
                    initial_state=None,  # Connect to existing state, don't create new
                    langgraph_token=langgraph_token,
                    current_graph_url=None,  # Not needed for simple state sync
                    current_graph_assistant_id=None,  # Not needed for simple state sync
                )
            
            # Get thread_id from runtime config if available
            config = getattr(runtime, "config", {})
            configurable = config.get("configurable", {})
            graph_thread_id = configurable.get("thread_id", str(uuid.uuid4()))
            
            # Get optional LangGraph token for advanced features
            langgraph_token = os.getenv("LANGGRAPH_TOKEN")
            
            logger.info(f"Initializing StationAgent for station_id: {station_id}")
            
            # Initialize StationAgent in a thread (includes import to avoid blocking)
            station_agent = await asyncio.to_thread(
                _import_and_init_station_agent,
                station_id=station_id,
                graph_thread_id=graph_thread_id,
                station_token=station_token,
                langgraph_token=langgraph_token,
            )
            
            logger.info("✅ StationAgent connection established")
            
        except ImportError:
            error_msg = (
                "ERROR: cuteagent library not installed. "
                "Cannot use Station middleware. "
                "Install with: pip install 'copilotagent[hitl]' "
                "Report this error to a human."
            )
            logger.error(error_msg)
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        except Exception as e:
            error_msg = (
                f"ERROR: Failed to initialize StationAgent: {str(e)} "
                f"Station ID: {station_id}. "
                "Report this error to a human."
            )
            logger.error(error_msg, exc_info=True)
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\n{error_msg}"
            return response
        
        # Parse tool output - it should be a dictionary
        tool_output = response.output
        if not isinstance(tool_output, dict):
            logger.warning(
                f"Tool output is not a dictionary (type: {type(tool_output)}). "
                f"Station middleware requires dict output to sync variables. Skipping sync."
            )
            return response
        
        # Sync variables from tool output to StationAgent (in thread since it's sync)
        synced_vars = []
        skipped_vars = []
        
        for var_name in variables_to_sync:
            if var_name in tool_output:
                # Variable exists in tool output - sync it to StationAgent
                var_value = tool_output[var_name]
                try:
                    await asyncio.to_thread(station_agent.state.set, var_name, var_value)
                    synced_vars.append(var_name)
                    logger.info(f"✅ Synced variable '{var_name}' to StationAgent (value type: {type(var_value).__name__})")
                except Exception as e:
                    error_msg = f"Failed to sync variable '{var_name}': {str(e)}"
                    logger.error(error_msg)
                    skipped_vars.append(f"{var_name} (error: {str(e)})")
            else:
                # Variable not in tool output - skip it
                skipped_vars.append(var_name)
                logger.warning(f"Variable '{var_name}' not found in tool output. Skipping.")
        
        # Log summary
        if synced_vars:
            logger.info(f"Station middleware synced {len(synced_vars)} variables: {synced_vars}")
        if skipped_vars:
            logger.info(f"Station middleware skipped {len(skipped_vars)} variables: {skipped_vars}")
        
        # Add sync summary to response output if it's a string
        if isinstance(response.output, str) and (synced_vars or skipped_vars):
            sync_summary = f"\n\n[Station Sync: {len(synced_vars)} variables updated"
            if skipped_vars:
                sync_summary += f", {len(skipped_vars)} skipped"
            sync_summary += "]"
            response.output = f"{response.output}{sync_summary}"
        
        return response

