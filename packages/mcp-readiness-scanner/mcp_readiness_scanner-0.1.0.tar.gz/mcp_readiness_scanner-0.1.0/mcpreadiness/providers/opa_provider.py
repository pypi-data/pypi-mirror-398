"""
OPA Provider - Policy-based checks using Open Policy Agent.

Evaluates MCP tool definitions and configurations against Rego policies.
The provider creates a normalized "facts" JSON document and runs OPA
against it with policies from the rules/policies/ directory.
"""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from mcpreadiness.core.models import Finding, OperationalRiskCategory, Severity
from mcpreadiness.providers.base import InspectionProvider

# Default policies directory (relative to this file)
DEFAULT_POLICIES_DIR = Path(__file__).parent.parent / "rules" / "policies"


# Mapping from policy violation types to categories
POLICY_CATEGORY_MAP: dict[str, OperationalRiskCategory] = {
    "timeout": OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
    "retry": OperationalRiskCategory.UNSAFE_RETRY_LOOP,
    "error": OperationalRiskCategory.MISSING_ERROR_SCHEMA,
    "capabilities": OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
    "description": OperationalRiskCategory.SILENT_FAILURE_PATH,
    "fallback": OperationalRiskCategory.NO_FALLBACK_CONTRACT,
    "observability": OperationalRiskCategory.NO_OBSERVABILITY_HOOKS,
    "deterministic": OperationalRiskCategory.NON_DETERMINISTIC_RESPONSE,
}


class OpaProvider(InspectionProvider):
    """
    Open Policy Agent-based inspection provider.

    Creates a "facts" JSON document from tool/config definitions and
    evaluates Rego policies against it. Policies are loaded from
    rules/policies/*.rego files.

    Example facts document:
    {
        "tool_name": "my_tool",
        "has_timeout": false,
        "timeout_value": null,
        "has_error_schema": false,
        "capabilities_count": 5,
        "has_retry_limit": true,
        "retry_limit": 3,
        ...
    }
    """

    def __init__(
        self,
        policies_dir: Path | str | None = None,
        opa_binary: str = "opa",
    ) -> None:
        """
        Initialize the OPA provider.

        Args:
            policies_dir: Directory containing Rego policy files
            opa_binary: Path or name of the OPA binary
        """
        self.policies_dir = Path(policies_dir) if policies_dir else DEFAULT_POLICIES_DIR
        self.opa_binary = opa_binary
        self._opa_path: str | None = None

    @property
    def name(self) -> str:
        return "opa"

    @property
    def description(self) -> str:
        return "Policy-based checks using Open Policy Agent (Rego)"

    def is_available(self) -> bool:
        """Check if OPA binary is available in PATH."""
        self._opa_path = shutil.which(self.opa_binary)
        return self._opa_path is not None

    def get_unavailable_reason(self) -> str | None:
        if not self.is_available():
            return (
                f"OPA binary '{self.opa_binary}' not found in PATH. "
                "Install OPA: https://www.openpolicyagent.org/docs/latest/#running-opa"
            )
        return None

    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze a tool definition using OPA policies.

        Creates a facts document from the tool definition and evaluates
        all policies against it.
        """
        if not self.is_available():
            return []

        findings: list[Finding] = []
        tool_name = tool_definition.get("name", "unknown")

        # Create facts document
        facts = self._create_tool_facts(tool_definition)

        # Run OPA evaluation
        violations = await self._evaluate_policies(facts)

        # Convert violations to findings
        for violation in violations:
            finding = self._violation_to_finding(violation, tool_name)
            if finding:
                findings.append(finding)

        return findings

    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration using OPA policies.

        Each server is analyzed separately with its own facts document.
        """
        if not self.is_available():
            return []

        findings: list[Finding] = []
        mcp_servers = config.get("mcpServers", {})

        for server_name, server_config in mcp_servers.items():
            facts = self._create_config_facts(server_name, server_config)
            violations = await self._evaluate_policies(facts)

            for violation in violations:
                finding = self._violation_to_finding(
                    violation, server_name, is_config=True
                )
                if finding:
                    findings.append(finding)

        return findings

    def _create_tool_facts(self, tool_definition: dict[str, Any]) -> dict[str, Any]:
        """
        Create a normalized facts document from a tool definition.

        The facts document extracts key information in a consistent
        format that policies can easily evaluate.
        """
        # Check for timeout fields
        timeout_fields = ["timeout", "timeoutMs", "timeout_ms", "timeoutSeconds"]
        timeout_value = None
        has_timeout = False
        for field in timeout_fields:
            if field in tool_definition:
                has_timeout = True
                timeout_value = tool_definition[field]
                break
            if "config" in tool_definition and field in tool_definition["config"]:
                has_timeout = True
                timeout_value = tool_definition["config"][field]
                break

        # Check for retry fields
        retry_fields = ["retries", "maxRetries", "max_retries", "retryLimit"]
        retry_value = None
        has_retry_limit = False
        for field in retry_fields:
            if field in tool_definition:
                has_retry_limit = True
                retry_value = tool_definition[field]
                break
            if "config" in tool_definition and field in tool_definition["config"]:
                has_retry_limit = True
                retry_value = tool_definition["config"][field]
                break

        # Check for capabilities
        capabilities = tool_definition.get("capabilities", [])
        capabilities_count = len(capabilities) if isinstance(capabilities, list) else 0

        # Check for error schema
        error_schema_fields = ["errorSchema", "error_schema", "errors"]
        has_error_schema = any(f in tool_definition for f in error_schema_fields)

        # Check for input schema
        input_schema = tool_definition.get("inputSchema", {})
        has_input_schema = bool(input_schema)
        input_properties_count = len(input_schema.get("properties", {}))
        has_required_fields = "required" in input_schema

        # Check for description
        description = tool_definition.get("description", "")
        has_description = bool(description)
        description_length = len(description)

        # Check for rate limiting
        rate_limit_fields = ["rateLimit", "rate_limit", "throttle"]
        has_rate_limit = any(f in tool_definition for f in rate_limit_fields)

        return {
            "type": "tool",
            "tool_name": tool_definition.get("name", "unknown"),
            "has_timeout": has_timeout,
            "timeout_value": timeout_value,
            "has_retry_limit": has_retry_limit,
            "retry_limit": retry_value,
            "capabilities_count": capabilities_count,
            "has_error_schema": has_error_schema,
            "has_input_schema": has_input_schema,
            "input_properties_count": input_properties_count,
            "has_required_fields": has_required_fields,
            "has_description": has_description,
            "description_length": description_length,
            "has_rate_limit": has_rate_limit,
            # Include raw definition for advanced policies
            "raw": tool_definition,
        }

    def _create_config_facts(
        self, server_name: str, server_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a normalized facts document from a server configuration."""
        # Check for timeout
        has_timeout = "timeout" in server_config
        timeout_value = server_config.get("timeout")

        # Check command
        has_command = "command" in server_config
        command = server_config.get("command", "")

        # Check args
        args = server_config.get("args", [])
        args_count = len(args) if isinstance(args, list) else 0

        # Check env
        env_vars = server_config.get("env", {})
        env_count = len(env_vars)

        return {
            "type": "config",
            "server_name": server_name,
            "has_timeout": has_timeout,
            "timeout_value": timeout_value,
            "has_command": has_command,
            "command": command,
            "args_count": args_count,
            "env_count": env_count,
            "raw": server_config,
        }

    async def _evaluate_policies(self, facts: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Evaluate all Rego policies against the facts document.

        Returns a list of violation dictionaries.
        """
        if not self.policies_dir.exists():
            return []

        violations: list[dict[str, Any]] = []

        # Find all policy files
        policy_files = list(self.policies_dir.glob("*.rego"))
        if not policy_files:
            return []

        # Create temporary files for input
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as input_file:
            json.dump(facts, input_file)
            input_path = input_file.name

        try:
            # Run OPA for each policy file
            for policy_file in policy_files:
                policy_violations = await self._run_opa(policy_file, input_path)
                violations.extend(policy_violations)
        finally:
            # Clean up temp file
            Path(input_path).unlink(missing_ok=True)

        return violations

    async def _run_opa(
        self, policy_path: Path, input_path: str
    ) -> list[dict[str, Any]]:
        """
        Run OPA evaluation for a single policy file.

        Returns a list of violations from the policy.
        """
        violations: list[dict[str, Any]] = []

        try:
            # Run OPA eval command
            cmd = [
                self._opa_path or "opa",
                "eval",
                "--input",
                input_path,
                "--data",
                str(policy_path),
                "--format",
                "json",
                "data.mcp.readiness.violation",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30.0
            )

            if process.returncode == 0:
                result = json.loads(stdout.decode("utf-8"))

                # Extract violations from OPA result
                if "result" in result and result["result"]:
                    expressions = result["result"]
                    for expr in expressions:
                        value = expr.get("value", [])
                        if isinstance(value, list):
                            for msg in value:
                                violations.append(
                                    {
                                        "message": msg if isinstance(msg, str) else str(msg),
                                        "policy": policy_path.stem,
                                    }
                                )
                        elif isinstance(value, str):
                            violations.append(
                                {
                                    "message": value,
                                    "policy": policy_path.stem,
                                }
                            )

        except TimeoutError:
            violations.append(
                {
                    "message": f"OPA evaluation timed out for {policy_path.name}",
                    "policy": policy_path.stem,
                    "is_error": True,
                }
            )
        except Exception as e:
            violations.append(
                {
                    "message": f"OPA evaluation failed: {str(e)}",
                    "policy": policy_path.stem,
                    "is_error": True,
                }
            )

        return violations

    def _violation_to_finding(
        self,
        violation: dict[str, Any],
        target_name: str,
        is_config: bool = False,
    ) -> Finding | None:
        """Convert an OPA violation to a Finding."""
        message = violation.get("message", "Policy violation")
        policy = violation.get("policy", "unknown")
        is_error = violation.get("is_error", False)

        # Determine category from policy name
        category = OperationalRiskCategory.SILENT_FAILURE_PATH
        for key, cat in POLICY_CATEGORY_MAP.items():
            if key in policy.lower():
                category = cat
                break

        # Errors get INFO severity, violations get MEDIUM by default
        severity = Severity.INFO if is_error else Severity.MEDIUM

        # Adjust severity based on message content
        msg_lower = message.lower()
        if "must" in msg_lower or "required" in msg_lower:
            severity = Severity.HIGH
        elif "should" in msg_lower or "recommended" in msg_lower:
            severity = Severity.MEDIUM
        elif "may" in msg_lower or "consider" in msg_lower:
            severity = Severity.LOW

        location_prefix = "mcpServers" if is_config else "tool"
        return Finding(
            category=category,
            severity=severity,
            title=f"Policy violation: {policy}",
            description=message,
            location=f"{location_prefix}.{target_name}",
            evidence={"policy_file": policy, "raw_violation": violation},
            provider=self.name,
            rule_id=f"OPA-{policy}",
        )
