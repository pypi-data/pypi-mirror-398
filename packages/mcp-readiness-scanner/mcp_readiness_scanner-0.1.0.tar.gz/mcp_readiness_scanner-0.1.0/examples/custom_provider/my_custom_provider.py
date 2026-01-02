"""
Example custom provider for MCP Readiness Scanner.

This demonstrates how to create and register a custom inspection provider
using the plugin system.
"""

from typing import Any

from mcpreadiness.core.models import Finding, Severity
from mcpreadiness.providers.base import InspectionProvider


class ExampleCustomProvider(InspectionProvider):
    """
    Example custom provider that checks for custom organization-specific rules.

    This provider demonstrates:
    - Inheriting from InspectionProvider
    - Implementing required abstract methods
    - Returning custom findings
    """

    def __init__(self) -> None:
        """Initialize the custom provider."""
        super().__init__(
            name="example-custom",
            description="Example custom provider for organization-specific checks",
            version="1.0.0",
        )

    def is_available(self) -> bool:
        """
        Check if this provider is available.

        Returns:
            True if provider can run (always true for this example)
        """
        return True

    def get_unavailable_reason(self) -> str | None:
        """
        Get reason why provider is unavailable.

        Returns:
            None since this provider is always available
        """
        return None

    async def initialize(self) -> None:
        """
        Initialize provider resources.

        Called before scanning begins. Use this to:
        - Load configuration
        - Initialize connections
        - Compile rules
        """
        pass

    async def cleanup(self) -> None:
        """
        Cleanup provider resources.

        Called after scanning completes. Use this to:
        - Close connections
        - Release resources
        """
        pass

    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP tool definition.

        Args:
            tool_definition: The tool definition dictionary

        Returns:
            List of findings (issues detected)
        """
        findings: list[Finding] = []

        # Example check: Ensure tool names follow organizational naming convention
        tool_name = tool_definition.get("name", "")
        if not tool_name.startswith("org_"):
            findings.append(
                Finding(
                    category="overloaded_tool_scope",
                    severity=Severity.LOW,
                    title="Tool name doesn't follow naming convention",
                    description=(
                        f"Tool '{tool_name}' should start with 'org_' prefix "
                        "to follow organizational naming standards"
                    ),
                    location="tool.name",
                    provider=self.name,
                    remediation=f"Rename tool to 'org_{tool_name}'",
                    rule_id="CUSTOM-001",
                )
            )

        # Example check: Require specific metadata fields
        metadata = tool_definition.get("metadata", {})
        if "owner_team" not in metadata:
            findings.append(
                Finding(
                    category="no_observability_hooks",
                    severity=Severity.MEDIUM,
                    title="Missing owner team metadata",
                    description="Tools must specify an 'owner_team' in metadata for accountability",
                    location="tool.metadata.owner_team",
                    provider=self.name,
                    remediation="Add 'metadata': {'owner_team': 'your-team-name'} to the tool definition",
                    rule_id="CUSTOM-002",
                )
            )

        # Example check: Require SLA documentation
        if "sla" not in tool_definition:
            findings.append(
                Finding(
                    category="no_fallback_contract",
                    severity=Severity.MEDIUM,
                    title="Missing SLA definition",
                    description="Production tools must document expected SLA/performance characteristics",
                    location="tool.sla",
                    provider=self.name,
                    evidence={"has_sla": False},
                    remediation="Add an 'sla' field documenting expected latency, availability, etc.",
                    rule_id="CUSTOM-003",
                )
            )

        return findings

    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration.

        Args:
            config: The MCP configuration dictionary

        Returns:
            List of findings (issues detected)
        """
        findings: list[Finding] = []

        # Example: Check for required configuration fields
        if "environment" not in config:
            findings.append(
                Finding(
                    category="silent_failure_path",
                    severity=Severity.HIGH,
                    title="Missing environment specification",
                    description="MCP configurations must specify the target environment (dev, staging, prod)",
                    location="config.environment",
                    provider=self.name,
                    remediation="Add 'environment': 'production' (or 'dev', 'staging') to the config",
                    rule_id="CUSTOM-004",
                )
            )

        return findings

