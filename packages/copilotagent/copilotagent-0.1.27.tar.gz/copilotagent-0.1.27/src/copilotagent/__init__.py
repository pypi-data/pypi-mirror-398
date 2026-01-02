"""CopilotAgent package."""

__author__ = """Harrison Chase"""
__email__ = "harrison@langchain.dev"
__version__ = "0.1.27"

from copilotagent.cloud_subagents import create_remote_subagent
from copilotagent.encompass_connect import (
    APIError,
    EncompassConnect,
    EncompassConnectError,
    TokenRefreshError,
)
from copilotagent.graph import (
    DEFAULT_AGENT_TYPE,
    create_deep_agent,
    get_default_starting_message,
)
from copilotagent.landingai_client import LandingAIClient, LandingAIError
from copilotagent.middleware.dynamic_tools import DynamicToolMiddleware
from copilotagent.middleware.filesystem import FilesystemMiddleware
from copilotagent.middleware.initial_message import InitialMessageMiddleware
from copilotagent.middleware.planning import PlanningMiddleware
from copilotagent.middleware.subagents import CompiledSubAgent, SubAgent, SubAgentMiddleware

__all__ = [
    "APIError",
    "CompiledSubAgent",
    "DEFAULT_AGENT_TYPE",
    "DynamicToolMiddleware",
    "EncompassConnect",
    "EncompassConnectError",
    "FilesystemMiddleware",
    "InitialMessageMiddleware",
    "LandingAIClient",
    "LandingAIError",
    "PlanningMiddleware",
    "SubAgent",
    "SubAgentMiddleware",
    "TokenRefreshError",
    "create_deep_agent",
    "create_remote_subagent",
    "get_default_starting_message",
]
