"""
YARA Provider - Pattern matching on tool metadata and descriptions.

Uses YARA rules to detect operational readiness patterns in tool
definitions. YARA rules target METADATA (names, descriptions, schemas),
NOT source code AST.
"""

import json
from pathlib import Path
from typing import Any

from mcpreadiness.core.models import Finding, OperationalRiskCategory, Severity
from mcpreadiness.providers.base import InspectionProvider

# Try to import yara-python
_yara_available = False
_yara_import_error: str | None = None

try:
    import yara

    _yara_available = True
except ImportError as e:
    _yara_import_error = str(e)
    yara = None  # type: ignore


# Default rules directory (relative to this file)
DEFAULT_RULES_DIR = Path(__file__).parent.parent / "rules" / "operational"


# Mapping from YARA rule metadata to operational risk categories
RULE_CATEGORY_MAP: dict[str, OperationalRiskCategory] = {
    "silent_failure": OperationalRiskCategory.SILENT_FAILURE_PATH,
    "non_deterministic": OperationalRiskCategory.NON_DETERMINISTIC_RESPONSE,
    "missing_timeout": OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
    "no_observability": OperationalRiskCategory.NO_OBSERVABILITY_HOOKS,
    "unsafe_retry": OperationalRiskCategory.UNSAFE_RETRY_LOOP,
    "overloaded_scope": OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
    "no_fallback": OperationalRiskCategory.NO_FALLBACK_CONTRACT,
    "missing_error_schema": OperationalRiskCategory.MISSING_ERROR_SCHEMA,
}


# Mapping from YARA rule metadata to severity
RULE_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}


class YaraProvider(InspectionProvider):
    """
    YARA-based pattern matching provider.

    Scans tool metadata (name, description, schema as JSON) for patterns
    that indicate operational readiness issues. Rules are loaded from
    .yar files in the rules/operational/ directory.

    Example patterns detected:
    - Dangerous phrases: "ignore errors", "best effort", "fire and forget"
    - Missing fields indicated by patterns
    - Overly broad capability keywords
    """

    def __init__(
        self,
        rules_dir: Path | str | None = None,
        additional_rules: list[str] | None = None,
    ) -> None:
        """
        Initialize the YARA provider.

        Args:
            rules_dir: Directory containing YARA rule files (.yar)
            additional_rules: Additional YARA rule strings to compile
        """
        self.rules_dir = Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR
        self.additional_rules = additional_rules or []
        self._compiled_rules: Any = None  # Will be yara.Rules if available

    @property
    def name(self) -> str:
        return "yara"

    @property
    def description(self) -> str:
        return "Pattern matching on tool metadata using YARA rules"

    def is_available(self) -> bool:
        """Check if yara-python is installed."""
        return _yara_available

    def get_unavailable_reason(self) -> str | None:
        if not _yara_available:
            return f"yara-python not installed: {_yara_import_error}"
        return None

    async def initialize(self) -> None:
        """Load and compile YARA rules."""
        if not self.is_available():
            return

        rules_sources: dict[str, str] = {}

        # Load rules from files
        if self.rules_dir.exists():
            for rule_file in self.rules_dir.glob("*.yar"):
                try:
                    rules_sources[rule_file.stem] = rule_file.read_text()
                except Exception:
                    # Skip invalid rule files
                    pass

        # Add additional rules
        for i, rule_string in enumerate(self.additional_rules):
            rules_sources[f"additional_{i}"] = rule_string

        # Compile all rules
        if rules_sources:
            try:
                self._compiled_rules = yara.compile(sources=rules_sources)
            except yara.Error:
                # Fall back to compiling rules individually
                for _name, source in rules_sources.items():
                    try:
                        if self._compiled_rules is None:
                            self._compiled_rules = yara.compile(source=source)
                        # Note: yara doesn't support merging compiled rules
                        # For production, consider pre-compiling into a single file
                    except yara.Error:
                        pass

    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze a tool definition using YARA rules.

        The tool definition is converted to a text representation for
        YARA matching, including:
        - Tool name
        - Description
        - Input schema as JSON
        - Any other string fields
        """
        if not self.is_available() or self._compiled_rules is None:
            return []

        findings: list[Finding] = []
        tool_name = tool_definition.get("name", "unknown")

        # Create text representation for YARA scanning
        text_content = self._tool_to_text(tool_definition)

        # Run YARA rules
        matches = self._compiled_rules.match(data=text_content.encode("utf-8"))

        for match in matches:
            finding = self._match_to_finding(match, tool_name, tool_definition)
            if finding:
                findings.append(finding)

        return findings

    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration using YARA rules.

        Each server configuration is scanned separately.
        """
        if not self.is_available() or self._compiled_rules is None:
            return []

        findings: list[Finding] = []

        mcp_servers = config.get("mcpServers", {})

        for server_name, server_config in mcp_servers.items():
            text_content = self._config_to_text(server_name, server_config)
            matches = self._compiled_rules.match(data=text_content.encode("utf-8"))

            for match in matches:
                finding = self._match_to_finding(
                    match,
                    server_name,
                    server_config,
                    is_config=True,
                )
                if finding:
                    findings.append(finding)

        return findings

    def _tool_to_text(self, tool_definition: dict[str, Any]) -> str:
        """Convert a tool definition to text for YARA scanning."""
        parts = []

        # Add tool name
        if "name" in tool_definition:
            parts.append(f"tool_name: {tool_definition['name']}")

        # Add description
        if "description" in tool_definition:
            parts.append(f"description: {tool_definition['description']}")

        # Add input schema as JSON
        if "inputSchema" in tool_definition:
            parts.append(f"input_schema: {json.dumps(tool_definition['inputSchema'])}")

        # Add error schema if present
        if "errorSchema" in tool_definition:
            parts.append(f"error_schema: {json.dumps(tool_definition['errorSchema'])}")

        # Add capabilities
        if "capabilities" in tool_definition:
            caps = tool_definition["capabilities"]
            if isinstance(caps, list):
                parts.append(f"capabilities: {', '.join(str(c) for c in caps)}")

        # Add full JSON for comprehensive matching
        parts.append(f"full_definition: {json.dumps(tool_definition)}")

        return "\n".join(parts)

    def _config_to_text(
        self, server_name: str, server_config: dict[str, Any]
    ) -> str:
        """Convert a server configuration to text for YARA scanning."""
        parts = [
            f"server_name: {server_name}",
            f"full_config: {json.dumps(server_config)}",
        ]

        if "command" in server_config:
            parts.append(f"command: {server_config['command']}")

        if "args" in server_config:
            args = server_config["args"]
            if isinstance(args, list):
                parts.append(f"args: {' '.join(str(a) for a in args)}")

        return "\n".join(parts)

    def _match_to_finding(
        self,
        match: Any,  # yara.Match
        target_name: str,
        definition: dict[str, Any],
        is_config: bool = False,
    ) -> Finding | None:
        """Convert a YARA match to a Finding."""
        # Extract metadata from rule
        meta = match.meta if hasattr(match, "meta") else {}

        # Get category from metadata or default
        category_str = meta.get("category", "silent_failure")
        category = RULE_CATEGORY_MAP.get(
            category_str, OperationalRiskCategory.SILENT_FAILURE_PATH
        )

        # Get severity from metadata or default
        severity_str = meta.get("severity", "medium")
        severity = RULE_SEVERITY_MAP.get(severity_str, Severity.MEDIUM)

        # Get title and description from metadata
        title = meta.get("title", f"YARA rule matched: {match.rule}")
        description = meta.get(
            "description",
            f"Pattern '{match.rule}' detected in {'configuration' if is_config else 'tool'} '{target_name}'",
        )

        # Get remediation from metadata
        remediation = meta.get("remediation")

        # Collect evidence
        evidence: dict[str, Any] = {
            "rule_name": match.rule,
            "tags": list(match.tags) if hasattr(match, "tags") else [],
        }

        # Add matched strings if available
        if hasattr(match, "strings") and match.strings:
            evidence["matched_strings"] = [
                {"offset": s[0], "identifier": s[1], "data": s[2].decode("utf-8", errors="replace")}
                for s in match.strings[:5]  # Limit to first 5 matches
            ]

        location_prefix = "mcpServers" if is_config else "tool"
        return Finding(
            category=category,
            severity=severity,
            title=title,
            description=description,
            location=f"{location_prefix}.{target_name}",
            evidence=evidence,
            provider=self.name,
            remediation=remediation,
            rule_id=f"YARA-{match.rule}",
        )
