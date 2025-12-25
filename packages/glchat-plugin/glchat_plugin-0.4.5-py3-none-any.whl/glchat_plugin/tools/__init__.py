"""Tool plugin system for GLLM Agents.

This module provides a plugin system for tools, allowing dynamic marking and preparation of tools
similar to VSCode's extension model. Tools can be decorated with metadata while remaining independent
from the core registration mechanism.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from glchat_plugin.tools.decorators import (
    get_plugin_metadata,
    is_tool_plugin,
    tool_plugin,
)

__all__ = [
    "tool_plugin",
    "is_tool_plugin",
    "get_plugin_metadata",
]
