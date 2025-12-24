"""
Base classes for Daita plugins.

Plugins are infrastructure utilities (databases, APIs, storage) that can
optionally expose their capabilities as agent tools.
"""

from abc import ABC
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.tools import AgentTool


class BasePlugin(ABC):
    """
    Base class for all Daita plugins.

    Plugins provide infrastructure utilities (S3, Slack, REST APIs, etc).
    They can optionally expose their capabilities as agent tools via get_tools().
    """

    def get_tools(self) -> List['AgentTool']:
        """
        Get agent-usable tools from this plugin.

        Override in subclasses to expose plugin capabilities as LLM tools.

        Returns:
            List of AgentTool instances
        """
        return []

    @property
    def has_tools(self) -> bool:
        """Check if plugin exposes any tools"""
        return len(self.get_tools()) > 0
