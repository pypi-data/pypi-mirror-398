"""
Acton Agent Tools - Tool Collection for LLM Agent Framework

This package provides FunctionTool-based tools for interacting with various APIs
including Radarr and Sonarr for media management.

Usage:
    from acton_agent_tools import get_radarr_toolset, get_sonarr_toolset

    # Get toolsets with configuration
    radarr_toolset = get_radarr_toolset(
        base_url="http://localhost:7878",
        api_key="your_radarr_api_key"
    )
    sonarr_toolset = get_sonarr_toolset(
        base_url="http://localhost:8989",
        api_key="your_sonarr_api_key"
    )

    # Use with agent
    agent.register_toolset(radarr_toolset)
    agent.register_toolset(sonarr_toolset)
"""

from .radarr_tools import get_radarr_toolset
from .sonarr_tools import get_sonarr_toolset


__all__ = [
    "get_radarr_toolset",
    "get_sonarr_toolset",
]

__version__ = "0.0.1"
