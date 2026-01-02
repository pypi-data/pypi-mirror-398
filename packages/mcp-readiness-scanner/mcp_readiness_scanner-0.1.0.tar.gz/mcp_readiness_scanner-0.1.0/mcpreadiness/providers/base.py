"""
Abstract base class for inspection providers.

All inspection providers must implement this interface to be used
with the ScanOrchestrator.
"""

from abc import ABC, abstractmethod
from typing import Any

from mcpreadiness.core.models import Finding


class InspectionProvider(ABC):
    """
    Abstract base class for inspection providers.

    Inspection providers analyze MCP tool definitions and configurations
    to detect operational readiness issues. Each provider implements a
    specific analysis strategy (heuristic, pattern matching, policy, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider identifier.

        This name is used in findings to identify which provider
        generated them, and can be used to selectively enable/disable
        providers.

        Returns:
            Unique provider name (e.g., "heuristic", "yara", "opa")
        """
        pass

    @property
    def description(self) -> str:
        """
        Human-readable description of what this provider does.

        Returns:
            Description of the provider's analysis approach
        """
        return "Base inspection provider"

    @property
    def version(self) -> str:
        """
        Provider version.

        Returns:
            Version string (e.g., "1.0.0")
        """
        return "0.1.0"

    @abstractmethod
    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze a single MCP tool definition.

        A tool definition typically contains:
        - name: Tool name
        - description: What the tool does
        - inputSchema: JSON Schema for inputs
        - Optionally: timeout, retries, capabilities, error schema, etc.

        Args:
            tool_definition: Dictionary containing the tool definition

        Returns:
            List of findings detected in the tool definition
        """
        pass

    @abstractmethod
    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration file.

        A configuration file typically contains:
        - mcpServers: Dictionary of server configurations
        - Each server may have: command, args, env, etc.

        Args:
            config: Dictionary containing the MCP configuration

        Returns:
            List of findings detected in the configuration
        """
        pass

    def is_available(self) -> bool:
        """
        Check if this provider can run.

        Override this method to check for:
        - Required dependencies (e.g., yara-python installed)
        - Required binaries (e.g., opa in PATH)
        - Required API keys or credentials
        - Required configuration

        Returns:
            True if the provider can run, False otherwise
        """
        return True

    def get_unavailable_reason(self) -> str | None:
        """
        Get the reason why this provider is unavailable.

        Returns:
            Human-readable reason, or None if provider is available
        """
        if self.is_available():
            return None
        return "Provider dependencies not met"

    async def initialize(self) -> None:  # noqa: B027
        """
        Initialize the provider.

        Called before analysis begins. Use this for:
        - Loading rules/policies
        - Establishing connections
        - Warming caches

        Default implementation does nothing.
        """
        pass

    async def cleanup(self) -> None:  # noqa: B027
        """
        Clean up provider resources.

        Called after analysis completes. Use this for:
        - Closing connections
        - Releasing resources

        Default implementation does nothing.
        """
        pass

    def __repr__(self) -> str:
        available = "available" if self.is_available() else "unavailable"
        return f"<{self.__class__.__name__}(name={self.name!r}, {available})>"
