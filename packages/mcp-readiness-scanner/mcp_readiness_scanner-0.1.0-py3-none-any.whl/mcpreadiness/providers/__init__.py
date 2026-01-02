"""
Inspection providers for MCP Readiness Scanner.

Providers analyze MCP tool definitions and configurations to detect
operational readiness issues.
"""

from mcpreadiness.providers.base import InspectionProvider
from mcpreadiness.providers.heuristic_provider import HeuristicProvider
from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

# Conditional imports for optional providers
_yara_available = False
_opa_available = False

try:
    from mcpreadiness.providers.yara_provider import YaraProvider

    _yara_available = True
except ImportError:
    YaraProvider = None  # type: ignore

try:
    from mcpreadiness.providers.opa_provider import OpaProvider

    _opa_available = True
except ImportError:
    OpaProvider = None  # type: ignore

__all__ = [
    "InspectionProvider",
    "HeuristicProvider",
    "YaraProvider",
    "OpaProvider",
    "LLMJudgeProvider",
]


def get_default_providers() -> list["InspectionProvider"]:
    """
    Get all available providers with default configuration.

    Returns providers that are available (dependencies installed, etc.)
    """
    providers: list[InspectionProvider] = []

    # Heuristic provider is always available (no external deps)
    providers.append(HeuristicProvider())

    # YARA provider if yara-python is installed
    if YaraProvider is not None:
        yara = YaraProvider()
        if yara.is_available():
            providers.append(yara)

    # OPA provider if opa binary is in PATH
    if OpaProvider is not None:
        opa = OpaProvider()
        if opa.is_available():
            providers.append(opa)

    # LLM provider is disabled by default, not included here

    return providers


def get_all_provider_classes() -> list[type]:
    """Get all provider classes (including unavailable ones)."""
    classes: list[type] = [HeuristicProvider]
    if YaraProvider is not None:
        classes.append(YaraProvider)
    if OpaProvider is not None:
        classes.append(OpaProvider)
    classes.append(LLMJudgeProvider)
    return classes
