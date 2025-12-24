"""Middleware for server coordination using StationAgent from CuteAgent library.

This middleware is called BEFORE and AFTER tool execution to coordinate
server availability and ensure only one task uses a server at a time.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
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


class ServerMiddleware(AgentMiddleware):
    """Middleware for coordinating server access using StationAgent.
    
    This middleware runs BEFORE and AFTER a tool to ensure coordinated server access:
    - BEFORE: Checks server availability, loads server, retries if busy
    - AFTER: Unloads server to make it available for other tasks
    
    Tools opt-in by adding configuration to their metadata:
    ```python
    tool.metadata = {
        "server_middleware": {
            "server_id": "princetonProd",  # This becomes the station_thread_id!
            "checkpoint": "Chrome",         # Optional, defaults to "Chrome"
            "server_index": 0,              # Optional, defaults to 0
            "server_task_type": "GetNames"  # Optional, defaults to tool name
        }
    }
    ```
    
    Environment Variables Required:
        - STATION_TOKEN: Authentication token for SharedState API
        - LANGGRAPH_TOKEN (optional): For pause/unpause functionality
    
    Important: The server_id becomes the station_thread_id for StationAgent initialization.
    This creates a SHARED station (e.g., "princetonProd") where all agents coordinate
    server access via the server arrays (server, serverThread, serverCheckpoint, serverTaskType).
    
    The middleware will:
    1. BEFORE tool execution:
       - Initialize StationAgent with station_thread_id = server_id (creates shared station)
       - Call station_agent.server.load(serverThreadId, serverCheckpoint, serverIndex, serverTaskType)
       - If server is "busy", retry every 30 seconds for up to 10 minutes
       - If other error (wrongCheckpoint, etc.), fail immediately
       - If server loaded successfully, proceed with tool execution
    2. AFTER tool execution:
       - Call station_agent.server.unload(checkpoint, index) to release server
       - Set server status back to idle in the shared station
    3. If errors occur:
       - Return error message as tool output
       - Allow graph execution to continue (agent can report to human)
    
    Example:
        ```python
        from copilotagent.middleware.server_middleware import ServerMiddleware
        from langchain.agents import create_agent
        
        agent = create_agent(
            "openai:gpt-4o",
            middleware=[ServerMiddleware()],
            tools=[...],
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize the ServerMiddleware."""
        self.name = "ServerMiddleware"
        self.max_retries = 20  # 20 attempts * 30 seconds = 10 minutes
        self.retry_interval = 30  # seconds

    def _get_station_agent(self, station_id: str, graph_thread_id: str, station_token: str, langgraph_token: str | None) -> Any:
        """Initialize and return a StationAgent instance.
        
        Args:
            station_id: Station thread ID (the server_id for server coordination)
            graph_thread_id: Graph thread ID
            station_token: Authentication token for SharedState API
            langgraph_token: Optional LangGraph token
            
        Returns:
            StationAgent instance with server arrays initialized if needed
            
        Raises:
            ImportError: If cuteagent not installed
            Exception: If StationAgent initialization fails
        """
        from cuteagent import StationAgent  # type: ignore[import-not-found]
        
        # Initialize server arrays for first-time setup
        # StationAgent will create these if they don't exist
        num_servers = 4  # Default: 4 server slots
        initial_server_state = {
            "server": ["idle"] * num_servers,
            "serverThread": ["idle"] * num_servers,
            "serverCheckpoint": ["Chrome"] * num_servers,
            "serverTaskType": ["taskPlaceholder"] * num_servers,
        }
        
        return StationAgent(
            station_thread_id=station_id,
            graph_thread_id=graph_thread_id,
            token=station_token,
            initial_state=initial_server_state,  # Create station with server arrays if doesn't exist
            langgraph_token=langgraph_token,
            current_graph_url=None,
            current_graph_assistant_id=None,
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Wrap tool execution with server coordination (load before, unload after).
        
        Args:
            request: The tool call request containing tool name and arguments
            handler: The function that executes the actual tool
            
        Returns:
            ToolMessage or Command with potentially modified output if errors occur
        """
        # Get runtime from request
        runtime = request.runtime
        if not runtime:
            print(f"⚠️  [ServerMiddleware] No runtime in request, skipping middleware")
            return handler(request)
        
        # Check if this tool has server_middleware configuration
        tool_metadata = getattr(runtime.tool, "metadata", {})
        server_config = tool_metadata.get("server_middleware")
        
        if not server_config:
            # Tool doesn't use server middleware, execute normally
            print(f"ℹ️  [ServerMiddleware] Tool '{request.name}' has no server_middleware config, skipping")
            return handler(request)
        
        # Tool opted in to server middleware
        print(f"🔧 [ServerMiddleware] ACTIVATED for tool: {request.name}")
        logger.info(f"Server middleware activated for tool: {request.name}")
        
        # Extract configuration with defaults
        server_id = server_config.get("server_id", "BrowserAgent")
        checkpoint = server_config.get("checkpoint", "Chrome")
        server_index = server_config.get("server_index", 0)
        server_task_type = server_config.get("server_task_type", request.name)
        
        # For Server Middleware, the station_thread_id IS the server_id itself
        # This creates a SHARED station where all agents coordinate server access
        # (e.g., all agents access station "princetonProd" to manage server arrays)
        station_id = server_id
        
        logger.info(f"Server middleware using station_thread_id: {station_id} (from server_id)")
        logger.info(f"This creates shared station for server coordination across all agents")
        
        # Check for required environment variables
        station_token = os.getenv("STATION_TOKEN")
        if not station_token:
            error_msg = (
                "ERROR: STATION_TOKEN environment variable not found. "
                "Cannot coordinate server access. "
                "Please ensure .env file contains STATION_TOKEN. "
                "Report this error to a human."
            )
            logger.error(error_msg)
            from langchain_core.messages import ToolMessage
            
            return type(handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # Initialize StationAgent
        try:
            config = getattr(runtime, "config", {})
            configurable = config.get("configurable", {})
            graph_thread_id = configurable.get("thread_id", str(uuid.uuid4()))
            langgraph_token = os.getenv("LANGGRAPH_TOKEN")
            
            print(f"🔌 [ServerMiddleware] Initializing StationAgent...")
            print(f"   - station_thread_id: {station_id}")
            print(f"   - graph_thread_id: {graph_thread_id}")
            logger.info(f"Initializing StationAgent for server coordination (station: {station_id})")
            station_agent = self._get_station_agent(station_id, graph_thread_id, station_token, langgraph_token)
            print(f"✅ [ServerMiddleware] StationAgent connection established")
            logger.info("✅ StationAgent connection established for server coordination")
            
        except ImportError:
            error_msg = (
                "ERROR: cuteagent library not installed. "
                "Cannot use Server middleware. "
                "Install with: pip install 'copilotagent[hitl]' "
                "Report this error to a human."
            )
            logger.error(error_msg)
            from langchain_core.messages import ToolMessage
            
            return type(handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        except Exception as e:
            error_msg = (
                f"ERROR: Failed to initialize StationAgent: {str(e)} "
                f"Station ID: {station_id}. "
                "Report this error to a human."
            )
            logger.error(error_msg, exc_info=True)
            from langchain_core.messages import ToolMessage
            
            return type(handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # BEFORE TOOL: Load server with retry logic
        server_loaded = False
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 [ServerMiddleware] Attempt {attempt + 1}/{self.max_retries} to load server...")
                logger.info(
                    f"Attempt {attempt + 1}/{self.max_retries} to load server "
                    f"(server_id: {server_id}, checkpoint: {checkpoint}, index: {server_index})"
                )
                
                print(f"   Calling station_agent.server.load()")
                print(f"     serverThreadId: {server_id}")
                print(f"     serverCheckpoint: {checkpoint}")
                print(f"     serverIndex: {server_index}")
                print(f"     serverTaskType: {server_task_type}")
                
                # Call server.load() - it expects serverThreadId, serverCheckpoint, serverIndex, serverTaskType
                load_result = station_agent.server.load(
                    serverThreadId=server_id,
                    serverCheckpoint=checkpoint,
                    serverIndex=server_index,
                    serverTaskType=server_task_type,
                )
                
                print(f"   ← Load result: {load_result}")
                
                status = load_result.get("status")
                
                if status == "loaded":
                    print(f"✅ [ServerMiddleware] Server loaded successfully for {server_task_type}")
                    logger.info(f"✅ Server loaded successfully for {server_task_type}")
                    server_loaded = True
                    break
                
                if status == "busy":
                    busy_info = load_result.get("error", "unknown task")
                    print(f"⏳ [ServerMiddleware] Server is BUSY: {busy_info}")
                    print(f"   Waiting {self.retry_interval} seconds before retry...")
                    logger.warning(
                        f"Server is busy: {busy_info}. "
                        f"Waiting {self.retry_interval} seconds before retry..."
                    )
                    time.sleep(self.retry_interval)
                    continue  # Retry on busy status only
                
                # Any other status (error, wrongCheckpoint, etc.) - fail immediately
                error_status = load_result.get("status", "unknown")
                error_message = load_result.get("error", "No error details provided")
                error_msg = (
                    f"ERROR: Server load failed with status '{error_status}': {error_message}. "
                    f"Tool: {request.name}. Report this error to a human and stop proceeding."
                )
                print(f"🚨 [ServerMiddleware] CRITICAL ERROR: {error_msg}")
                logger.error(f"🚨 CRITICAL: {error_msg}")
                from langchain_core.messages import ToolMessage
                
                return type(handler(request))(
                    output=error_msg,
                    tool_call_id=getattr(request, "tool_call_id", None),
                )
                
            except Exception as e:
                error_msg = (
                    f"ERROR: Exception during server load attempt {attempt + 1}: {str(e)}. "
                    f"Report this error to a human."
                )
                logger.error(error_msg, exc_info=True)
                from langchain_core.messages import ToolMessage
                
                return type(handler(request))(
                    output=error_msg,
                    tool_call_id=getattr(request, "tool_call_id", None),
                )
        
        # Check if server was loaded after all retries
        if not server_loaded:
            elapsed_time = self.max_retries * self.retry_interval / 60
            error_msg = (
                f"ERROR: Server remained busy after {self.max_retries} attempts "
                f"({elapsed_time:.1f} minutes). Cannot proceed with tool execution. "
                f"Report this error to a human."
            )
            logger.error(f"🚨 TIMEOUT: {error_msg}")
            from langchain_core.messages import ToolMessage
            
            return type(handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # Server is loaded, execute the tool
        print(f"⚡ [ServerMiddleware] Server loaded, executing tool: {request.name}")
        logger.info(f"Executing tool {request.name} with server coordination...")
        try:
            response = handler(request)
            print(f"✅ [ServerMiddleware] Tool {request.name} completed successfully")
        except Exception as e:
            # Tool execution failed - still need to unload server
            print(f"❌ [ServerMiddleware] Tool execution FAILED: {str(e)}")
            logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            # Attempt to unload server before re-raising
            try:
                print(f"🔄 [ServerMiddleware] Tool failed, attempting to unload server...")
                station_agent.server.unload(checkpoint=checkpoint, index=server_index)
                print(f"✅ [ServerMiddleware] Server unloaded after tool failure")
                logger.info("✅ Server unloaded after tool failure")
            except Exception as unload_error:
                print(f"❌ [ServerMiddleware] Failed to unload server: {str(unload_error)}")
                logger.error(f"Failed to unload server after tool error: {str(unload_error)}")
            raise  # Re-raise the original tool error
        
        # AFTER TOOL: Unload server
        try:
            print(f"🔓 [ServerMiddleware] Unloading server (checkpoint: {checkpoint}, index: {server_index})...")
            logger.info(f"Unloading server (checkpoint: {checkpoint}, index: {server_index})...")
            unload_result = station_agent.server.unload(checkpoint=checkpoint, index=server_index)
            print(f"✅ [ServerMiddleware] Server unloaded: {unload_result}")
            logger.info(f"✅ Server unloaded: {unload_result}")
        except Exception as e:
            logger.error(f"Warning: Failed to unload server: {str(e)}", exc_info=True)
            # Don't fail the tool just because unload failed - log and continue
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\nWarning: Server unload failed: {str(e)}"
        
        return response

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Async version of wrap_tool_call with server coordination.
        
        Args:
            request: The tool call request containing tool name and arguments
            handler: The async function that executes the actual tool
            
        Returns:
            ToolMessage or Command with potentially modified output if errors occur
        """
        # Get runtime from request
        runtime = request.runtime
        if not runtime:
            print(f"⚠️  [ServerMiddleware ASYNC] No runtime in request, skipping middleware")
            return await handler(request)
        
        # Check if this tool has server_middleware configuration
        tool_metadata = getattr(runtime.tool, "metadata", {})
        server_config = tool_metadata.get("server_middleware")
        
        if not server_config:
            # Tool doesn't use server middleware, execute normally
            print(f"ℹ️  [ServerMiddleware ASYNC] Tool '{request.name}' has no server_middleware config, skipping")
            return await handler(request)
        
        # Tool opted in to server middleware
        print(f"🔧 [ServerMiddleware ASYNC] ACTIVATED for tool: {request.name}")
        logger.info(f"Server middleware activated for tool: {request.name}")
        
        # Extract configuration with defaults
        server_id = server_config.get("server_id", "BrowserAgent")
        checkpoint = server_config.get("checkpoint", "Chrome")
        server_index = server_config.get("server_index", 0)
        server_task_type = server_config.get("server_task_type", request.name)
        
        # For Server Middleware, the station_thread_id IS the server_id itself
        # This creates a SHARED station where all agents coordinate server access
        # (e.g., all agents access station "princetonProd" to manage server arrays)
        station_id = server_id
        
        logger.info(f"Server middleware using station_thread_id: {station_id} (from server_id)")
        logger.info(f"This creates shared station for server coordination across all agents")
        
        # Check for required environment variables
        station_token = os.getenv("STATION_TOKEN")
        if not station_token:
            error_msg = (
                "ERROR: STATION_TOKEN environment variable not found. "
                "Cannot coordinate server access. "
                "Please ensure .env file contains STATION_TOKEN. "
                "Report this error to a human."
            )
            logger.error(error_msg)
            from langchain_core.messages import ToolMessage
            
            return type(await handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # Initialize StationAgent (in thread since it's sync)
        try:
            config = getattr(runtime, "config", {})
            configurable = config.get("configurable", {})
            graph_thread_id = configurable.get("thread_id", str(uuid.uuid4()))
            langgraph_token = os.getenv("LANGGRAPH_TOKEN")
            
            print(f"🔌 [ServerMiddleware ASYNC] Initializing StationAgent...")
            print(f"   - station_thread_id: {station_id}")
            print(f"   - graph_thread_id: {graph_thread_id}")
            logger.info(f"Initializing StationAgent for server coordination (station: {station_id})")
            station_agent = await asyncio.to_thread(
                self._get_station_agent, station_id, graph_thread_id, station_token, langgraph_token
            )
            print(f"✅ [ServerMiddleware ASYNC] StationAgent connection established")
            logger.info("✅ StationAgent connection established for server coordination")
            
        except ImportError:
            error_msg = (
                "ERROR: cuteagent library not installed. "
                "Cannot use Server middleware. "
                "Install with: pip install 'copilotagent[hitl]' "
                "Report this error to a human."
            )
            logger.error(error_msg)
            from langchain_core.messages import ToolMessage
            
            return type(await handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        except Exception as e:
            error_msg = (
                f"ERROR: Failed to initialize StationAgent: {str(e)} "
                f"Station ID: {station_id}. "
                "Report this error to a human."
            )
            logger.error(error_msg, exc_info=True)
            from langchain_core.messages import ToolMessage
            
            return type(await handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # BEFORE TOOL: Load server with retry logic (async version)
        server_loaded = False
        for attempt in range(self.max_retries):
            try:
                print(f"🔄 [ServerMiddleware ASYNC] Attempt {attempt + 1}/{self.max_retries} to load server...")
                logger.info(
                    f"Attempt {attempt + 1}/{self.max_retries} to load server "
                    f"(server_id: {server_id}, checkpoint: {checkpoint}, index: {server_index})"
                )
                
                print(f"   Calling station_agent.server.load()")
                print(f"     serverThreadId: {server_id}")
                print(f"     serverCheckpoint: {checkpoint}")
                print(f"     serverIndex: {server_index}")
                print(f"     serverTaskType: {server_task_type}")
                
                # Call server.load() in thread (it's sync)
                load_result = await asyncio.to_thread(
                    station_agent.server.load,
                    serverThreadId=server_id,
                    serverCheckpoint=checkpoint,
                    serverIndex=server_index,
                    serverTaskType=server_task_type,
                )
                
                print(f"   ← Load result: {load_result}")
                
                status = load_result.get("status")
                
                if status == "loaded":
                    print(f"✅ [ServerMiddleware ASYNC] Server loaded successfully for {server_task_type}")
                    logger.info(f"✅ Server loaded successfully for {server_task_type}")
                    server_loaded = True
                    break
                
                if status == "busy":
                    busy_info = load_result.get("error", "unknown task")
                    print(f"⏳ [ServerMiddleware ASYNC] Server is BUSY: {busy_info}")
                    print(f"   Waiting {self.retry_interval} seconds before retry...")
                    logger.warning(
                        f"Server is busy: {busy_info}. "
                        f"Waiting {self.retry_interval} seconds before retry..."
                    )
                    await asyncio.sleep(self.retry_interval)
                    continue  # Retry on busy status only
                
                # Any other status (error, wrongCheckpoint, etc.) - fail immediately
                error_status = load_result.get("status", "unknown")
                error_message = load_result.get("error", "No error details provided")
                error_msg = (
                    f"ERROR: Server load failed with status '{error_status}': {error_message}. "
                    f"Tool: {request.name}. Report this error to a human and stop proceeding."
                )
                logger.error(f"🚨 CRITICAL: {error_msg}")
                from langchain_core.messages import ToolMessage
                
                return type(await handler(request))(
                    output=error_msg,
                    tool_call_id=getattr(request, "tool_call_id", None),
                )
                
            except Exception as e:
                error_msg = (
                    f"ERROR: Exception during server load attempt {attempt + 1}: {str(e)}. "
                    f"Report this error to a human."
                )
                logger.error(error_msg, exc_info=True)
                from langchain_core.messages import ToolMessage
                
                return type(await handler(request))(
                    output=error_msg,
                    tool_call_id=getattr(request, "tool_call_id", None),
                )
        
        # Check if server was loaded after all retries
        if not server_loaded:
            elapsed_time = self.max_retries * self.retry_interval / 60
            error_msg = (
                f"ERROR: Server remained busy after {self.max_retries} attempts "
                f"({elapsed_time:.1f} minutes). Cannot proceed with tool execution. "
                f"Report this error to a human."
            )
            logger.error(f"🚨 TIMEOUT: {error_msg}")
            from langchain_core.messages import ToolMessage
            
            return type(await handler(request))(
                output=error_msg,
                tool_call_id=getattr(request, "tool_call_id", None),
            )
        
        # Server is loaded, execute the tool
        print(f"⚡ [ServerMiddleware ASYNC] Server loaded, executing tool: {request.name}")
        logger.info(f"Executing tool {request.name} with server coordination...")
        try:
            response = await handler(request)
            print(f"✅ [ServerMiddleware ASYNC] Tool {request.name} completed successfully")
        except Exception as e:
            # Tool execution failed - still need to unload server
            print(f"❌ [ServerMiddleware ASYNC] Tool execution FAILED: {str(e)}")
            logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            # Attempt to unload server before re-raising
            try:
                print(f"🔄 [ServerMiddleware ASYNC] Tool failed, attempting to unload server...")
                await asyncio.to_thread(station_agent.server.unload, checkpoint=checkpoint, index=server_index)
                print(f"✅ [ServerMiddleware ASYNC] Server unloaded after tool failure")
                logger.info("✅ Server unloaded after tool failure")
            except Exception as unload_error:
                print(f"❌ [ServerMiddleware ASYNC] Failed to unload server: {str(unload_error)}")
                logger.error(f"Failed to unload server after tool error: {str(unload_error)}")
            raise  # Re-raise the original tool error
        
        # AFTER TOOL: Unload server
        try:
            print(f"🔓 [ServerMiddleware ASYNC] Unloading server (checkpoint: {checkpoint}, index: {server_index})...")
            logger.info(f"Unloading server (checkpoint: {checkpoint}, index: {server_index})...")
            unload_result = await asyncio.to_thread(
                station_agent.server.unload, checkpoint=checkpoint, index=server_index
            )
            print(f"✅ [ServerMiddleware ASYNC] Server unloaded: {unload_result}")
            logger.info(f"✅ Server unloaded: {unload_result}")
        except Exception as e:
            logger.error(f"Warning: Failed to unload server: {str(e)}", exc_info=True)
            # Don't fail the tool just because unload failed - log and continue
            if isinstance(response.output, str):
                response.output = f"{response.output}\n\nWarning: Server unload failed: {str(e)}"
        
        return response

