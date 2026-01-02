"""
Scan Orchestrator - The brain of MCP Readiness Scanner.

Coordinates inspection providers, aggregates findings, and calculates
readiness scores.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mcpreadiness.core.models import Finding, ScanResult, Severity
from mcpreadiness.providers.base import InspectionProvider

# Severity deduction points for readiness score calculation
SEVERITY_DEDUCTIONS: dict[Severity, int] = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 10,
    Severity.LOW: 5,
    Severity.INFO: 0,
}


class ScanOrchestrator:
    """
    Orchestrates scanning across multiple inspection providers.

    The orchestrator:
    - Manages registered providers
    - Runs scans across all (or selected) providers
    - Aggregates findings from all providers
    - Calculates readiness scores
    """

    def __init__(self) -> None:
        """Initialize the orchestrator with no providers."""
        self._providers: dict[str, InspectionProvider] = {}

    def register_provider(self, provider: InspectionProvider) -> None:
        """
        Register an inspection provider.

        Args:
            provider: Provider instance to register

        Raises:
            ValueError: If a provider with the same name is already registered
        """
        if provider.name in self._providers:
            raise ValueError(
                f"Provider '{provider.name}' is already registered. "
                "Use unregister_provider first to replace it."
            )
        self._providers[provider.name] = provider

    def unregister_provider(self, name: str) -> bool:
        """
        Unregister a provider by name.

        Args:
            name: Name of the provider to unregister

        Returns:
            True if provider was unregistered, False if not found
        """
        if name in self._providers:
            del self._providers[name]
            return True
        return False

    def get_provider(self, name: str) -> InspectionProvider | None:
        """
        Get a provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(name)

    def list_providers(self) -> list[InspectionProvider]:
        """
        List all registered providers.

        Returns:
            List of all registered provider instances
        """
        return list(self._providers.values())

    def list_available_providers(self) -> list[InspectionProvider]:
        """
        List providers that are available to run.

        Returns:
            List of available provider instances
        """
        return [p for p in self._providers.values() if p.is_available()]

    def _select_providers(
        self, provider_names: list[str] | None
    ) -> list[InspectionProvider]:
        """
        Select providers to use for a scan.

        Args:
            provider_names: List of provider names, or None for all available

        Returns:
            List of provider instances to use

        Raises:
            ValueError: If a specified provider is not registered or unavailable
        """
        if provider_names is None:
            return self.list_available_providers()

        providers = []
        for name in provider_names:
            provider = self._providers.get(name)
            if provider is None:
                raise ValueError(
                    f"Provider '{name}' is not registered. "
                    f"Available: {list(self._providers.keys())}"
                )
            if not provider.is_available():
                reason = provider.get_unavailable_reason() or "Unknown reason"
                raise ValueError(f"Provider '{name}' is not available: {reason}")
            providers.append(provider)

        return providers

    @staticmethod
    def calculate_readiness_score(findings: list[Finding]) -> int:
        """
        Calculate readiness score based on findings.

        Starts at 100 and deducts points per finding based on severity:
        - CRITICAL: -25
        - HIGH: -15
        - MEDIUM: -10
        - LOW: -5
        - INFO: 0

        Args:
            findings: List of findings from all providers

        Returns:
            Readiness score from 0-100
        """
        score = 100
        for finding in findings:
            score -= SEVERITY_DEDUCTIONS.get(finding.severity, 0)
        return max(0, score)

    async def _run_provider_tool_analysis(
        self,
        provider: InspectionProvider,
        tool_definition: dict[str, Any],
    ) -> list[Finding]:
        """Run tool analysis for a single provider with error handling."""
        try:
            return await provider.analyze_tool(tool_definition)
        except Exception as e:
            # Return a finding about the provider failure
            return [
                Finding(
                    category="silent_failure_path",
                    severity=Severity.INFO,
                    title=f"Provider '{provider.name}' failed",
                    description=f"Error during analysis: {str(e)}",
                    provider=provider.name,
                    evidence={"error_type": type(e).__name__, "error_message": str(e)},
                )
            ]

    async def _run_provider_config_analysis(
        self,
        provider: InspectionProvider,
        config: dict[str, Any],
    ) -> list[Finding]:
        """Run config analysis for a single provider with error handling."""
        try:
            return await provider.analyze_config(config)
        except Exception as e:
            return [
                Finding(
                    category="silent_failure_path",
                    severity=Severity.INFO,
                    title=f"Provider '{provider.name}' failed",
                    description=f"Error during analysis: {str(e)}",
                    provider=provider.name,
                    evidence={"error_type": type(e).__name__, "error_message": str(e)},
                )
            ]

    async def scan_tool(
        self,
        tool_definition: dict[str, Any],
        providers: list[str] | None = None,
        target_name: str | None = None,
    ) -> ScanResult:
        """
        Scan a single MCP tool definition.

        Args:
            tool_definition: Dictionary containing the tool definition
            providers: List of provider names to use, or None for all available
            target_name: Optional name for the target (defaults to tool name)

        Returns:
            ScanResult with aggregated findings and readiness score
        """
        start_time = time.time()

        selected_providers = self._select_providers(providers)

        # Initialize providers
        await asyncio.gather(*(p.initialize() for p in selected_providers))

        try:
            # Run all providers concurrently
            tasks = [
                self._run_provider_tool_analysis(p, tool_definition)
                for p in selected_providers
            ]
            results = await asyncio.gather(*tasks)

            # Flatten findings
            all_findings: list[Finding] = []
            for finding_list in results:
                all_findings.extend(finding_list)

            # Determine target name
            target = target_name or tool_definition.get("name", "unknown_tool")

            # Calculate score and build result
            score = self.calculate_readiness_score(all_findings)
            duration_ms = int((time.time() - start_time) * 1000)

            return ScanResult(
                target=target,
                findings=all_findings,
                readiness_score=score,
                timestamp=datetime.utcnow(),
                providers_used=[p.name for p in selected_providers],
                scan_duration_ms=duration_ms,
                metadata={"scan_type": "tool"},
            )
        finally:
            # Cleanup providers
            await asyncio.gather(*(p.cleanup() for p in selected_providers))

    async def scan_config(
        self,
        config: dict[str, Any],
        providers: list[str] | None = None,
        target_name: str | None = None,
    ) -> ScanResult:
        """
        Scan an MCP configuration.

        Args:
            config: Dictionary containing the MCP configuration
            providers: List of provider names to use, or None for all available
            target_name: Optional name for the target (defaults to "mcp_config")

        Returns:
            ScanResult with aggregated findings and readiness score
        """
        start_time = time.time()

        selected_providers = self._select_providers(providers)

        # Initialize providers
        await asyncio.gather(*(p.initialize() for p in selected_providers))

        try:
            # Run all providers concurrently
            tasks = [
                self._run_provider_config_analysis(p, config)
                for p in selected_providers
            ]
            results = await asyncio.gather(*tasks)

            # Flatten findings
            all_findings: list[Finding] = []
            for finding_list in results:
                all_findings.extend(finding_list)

            # Determine target name
            target = target_name or "mcp_config"

            # Calculate score and build result
            score = self.calculate_readiness_score(all_findings)
            duration_ms = int((time.time() - start_time) * 1000)

            return ScanResult(
                target=target,
                findings=all_findings,
                readiness_score=score,
                timestamp=datetime.utcnow(),
                providers_used=[p.name for p in selected_providers],
                scan_duration_ms=duration_ms,
                metadata={"scan_type": "config"},
            )
        finally:
            # Cleanup providers
            await asyncio.gather(*(p.cleanup() for p in selected_providers))

    async def scan_config_file(
        self,
        path: Path | str,
        providers: list[str] | None = None,
    ) -> ScanResult:
        """
        Scan an MCP configuration file.

        Args:
            path: Path to the configuration file
            providers: List of provider names to use, or None for all available

        Returns:
            ScanResult with aggregated findings and readiness score

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file isn't valid JSON
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, encoding="utf-8") as f:
            config = json.load(f)

        return await self.scan_config(
            config=config,
            providers=providers,
            target_name=str(path),
        )

    async def scan_tool_file(
        self,
        path: Path | str,
        providers: list[str] | None = None,
    ) -> ScanResult:
        """
        Scan an MCP tool definition file.

        Args:
            path: Path to the tool definition file
            providers: List of provider names to use, or None for all available

        Returns:
            ScanResult with aggregated findings and readiness score

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file isn't valid JSON
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Tool definition file not found: {path}")

        with open(path, encoding="utf-8") as f:
            tool_definition = json.load(f)

        return await self.scan_tool(
            tool_definition=tool_definition,
            providers=providers,
            target_name=str(path),
        )


def create_default_orchestrator() -> ScanOrchestrator:
    """
    Create an orchestrator with all available default providers.

    Returns:
        ScanOrchestrator with registered providers
    """
    from mcpreadiness.providers import get_default_providers

    orchestrator = ScanOrchestrator()
    for provider in get_default_providers():
        orchestrator.register_provider(provider)

    return orchestrator
