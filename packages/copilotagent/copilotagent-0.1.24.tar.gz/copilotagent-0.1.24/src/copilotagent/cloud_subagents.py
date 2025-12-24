"""Cloud subagents using LangGraph Cloud deployed services.

This module provides factory functions for creating CompiledSubAgent instances
that connect to deployed LangGraph Cloud services via LangGraph SDK client.
"""

import logging
import os
from typing import Any, TypedDict

from langchain_core.runnables import Runnable
from langgraph_sdk import get_client

# Set up logging
logger = logging.getLogger(__name__)


class RemoteGraphRunnable(Runnable):
    """Wrapper to make LangGraph SDK client work as a Runnable.
    
    This adapter allows the new LangGraph SDK client API to work with
    the existing Runnable interface expected by SubAgentMiddleware.
    """
    
    def __init__(
        self, 
        url: str, 
        api_key: str, 
        graph_id: str,
        middleware_config: dict[str, Any] | None = None,
    ):
        """Initialize the remote graph runnable.
        
        Args:
            url: The URL of the deployed LangGraph service
            api_key: The API key for authentication
            graph_id: The graph ID to use (assistant_id)
            middleware_config: Optional middleware configuration for coordinating the remote subagent.
                This config is NOT sent to the remote graph. Middleware runs in the PARENT agent.
                
                Configuration example:
                {
                    "station": {
                        "variables": ["borrower_names", "reason_code"],
                        "station_id": "my-session-station"  # Explicit, calculated in parent
                    },
                    "server": {
                        "server_id": "princetonProd",  # Shared coordination station
                        "checkpoint": "Chrome",
                        "server_index": 0
                    }
                }
                
                How it works:
                - Server coordination happens in parent BEFORE/AFTER subagent invocation
                - Station syncing happens in parent AFTER subagent completes
                - Remote graph receives clean input without middleware config
        """
        self.url = url
        self.api_key = api_key
        self.graph_id = graph_id
        self.middleware_config = middleware_config or {}
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of the client."""
        if self._client is None:
            self._client = get_client(url=self.url, api_key=self.api_key)
        return self._client
    
    def invoke(self, input: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Synchronously invoke the remote graph.
        
        Args:
            input: The input state dictionary
            config: Optional configuration
            
        Returns:
            The final state from the remote graph execution
        """
        import asyncio
        return asyncio.run(self.ainvoke(input, config))
    
    async def ainvoke(self, input: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Asynchronously invoke the remote graph.
        
        Args:
            input: The input state dictionary
            config: Optional configuration
            
        Returns:
            The final state from the remote graph execution, including subagent metadata
        """
        # Note: middleware_config is NOT sent to remote graph
        # All middleware (server coordination, station syncing) happens in the PARENT agent
        # The remote graph just executes its logic normally
        
        # Create a thread first so we can capture the thread_id
        thread = await self.client.threads.create()
        thread_id = thread.get("thread_id") if isinstance(thread, dict) else getattr(thread, "thread_id", None)
        
        logger.info(f"[RemoteSubagent] Created thread {thread_id} for graph {self.graph_id}")
        
        # Use the runs.wait method to execute and wait for completion
        result = await self.client.runs.wait(
            thread_id=thread_id,  # Use the created thread
            assistant_id=self.graph_id,
            input=input,  # Send original input without middleware config
        )
        
        # Add subagent metadata to the result
        # This allows the parent agent to know which thread/subagent produced this result
        if isinstance(result, dict):
            result["_subagent_metadata"] = {
                "thread_id": thread_id,
                "graph_id": self.graph_id,
                "url": self.url,
            }
            logger.info(f"[RemoteSubagent] Completed. thread_id={thread_id}, graph_id={self.graph_id}")
        
        # Return the final state from the result
        return result


class CompiledSubAgent(TypedDict):
    """A pre-compiled agent spec."""

    name: str
    """The name of the agent."""

    description: str
    """The description of the agent."""

    runnable: Runnable
    """The Runnable to use for the agent."""


def create_remote_subagent(
    name: str,
    url: str,
    graph_id: str,
    description: str,
    api_key: str | None = None,
    middleware_config: dict[str, Any] | None = None,
) -> CompiledSubAgent:
    """Create a remote subagent that connects to a LangGraph Cloud service.
    
    This is a generic factory function that allows you to create custom cloud subagents
    without hardcoding them in the package. You can use this to connect to any
    LangGraph Cloud deployed service.
    
    Args:
        name: The name of the subagent (e.g., "my-custom-agent")
        url: The URL of the deployed LangGraph Cloud service
        graph_id: The graph ID to use (assistant_id)
        description: Description shown to the main agent for deciding when to call this subagent
        api_key: Optional API key. If not provided, will try to get from environment
            variables: LANGCHAIN_API_KEY, LANGSMITH_API_KEY, or LANGGRAPH_API_KEY
        middleware_config: Optional middleware configuration for coordinating the remote subagent.
            This config is NOT sent to the remote graph. Instead, the middleware runs in the
            PARENT agent (before/after invoking the remote subagent).
            
            Configuration supports:
            - "station": Station middleware for syncing subagent results
            - "server": Server middleware for coordinating exclusive server access
            
            Example configuration:
            {
                "station": {
                    "variables": ["borrower_names", "reason_code"],
                    "station_id": "my-session-station"  # Must be explicit
                },
                "server": {
                    "server_id": "princetonProd",  # Shared server coordination station
                    "checkpoint": "Chrome",
                    "server_index": 0
                }
            }
            
            How it works:
            - Server coordination: Runs BEFORE subagent (loads server) and AFTER (unloads)
            - Station syncing: Runs AFTER subagent (syncs result variables)
            - All happens in parent agent, not in remote graph
    
    Returns:
        CompiledSubAgent dictionary with RemoteGraph runnable.
        
    Raises:
        ValueError: If API key is not provided and cannot be found in environment.
        
    Example:
        ```python
        from copilotagent import create_deep_agent, create_remote_subagent
        
        # Create a custom cloud subagent
        my_subagent = create_remote_subagent(
            name="data-processor",
            url="https://my-service.us.langgraph.app",
            graph_id="myGraphId",
            description="Processes data from external systems"
        )
        
        # Use it in your agent
        agent = create_deep_agent(
            agent_type="ITP-Princeton",
            subagents=[my_subagent],
        )
        ```
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = (
            os.getenv("LANGCHAIN_API_KEY") or 
            os.getenv("LANGSMITH_API_KEY") or 
            os.getenv("LANGGRAPH_API_KEY")
        )
    
    if not api_key:
        msg = (
            "API key is required for cloud subagents. "
            "Either provide api_key parameter or set one of: "
            "LANGCHAIN_API_KEY, LANGSMITH_API_KEY, or LANGGRAPH_API_KEY environment variable."
        )
        logger.error(msg)
        raise ValueError(msg)
    
    logger.info(f"Creating remote subagent '{name}' at {url}")
    
    if middleware_config:
        logger.info(f"Middleware config provided for '{name}': {middleware_config}")
    
    client = RemoteGraphRunnable(
        url=url,
        api_key=api_key,
        graph_id=graph_id,
        middleware_config=middleware_config,
    )
    
    return {
        "name": name,
        "description": description,
        "runnable": client,
    }



