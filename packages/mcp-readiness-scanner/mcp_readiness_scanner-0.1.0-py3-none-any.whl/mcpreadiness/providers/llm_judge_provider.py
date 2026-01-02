"""
LLM Judge Provider - Semantic analysis using LLMs.

DISABLED BY DEFAULT - requires explicit configuration via environment
variables or config file. This provider uses LLMs to evaluate semantic
questions about tool definitions that are difficult to check with
static analysis.

Supports:
- OpenAI-compatible APIs (OpenAI, Azure OpenAI, etc.)
- Anthropic
- Local models via Ollama (recommended for OSS/no-API-key path)
"""

import os
from typing import Any

from mcpreadiness.core.models import Finding, OperationalRiskCategory, Severity
from mcpreadiness.providers.base import InspectionProvider

# Try to import litellm
_litellm_available = False
_litellm_import_error: str | None = None

try:
    import litellm

    _litellm_available = True
except ImportError as e:
    _litellm_import_error = str(e)
    litellm = None  # type: ignore


# Environment variables that enable the LLM provider
ENABLE_ENV_VARS = [
    "MCP_READINESS_LLM_MODEL",
    "MCP_READINESS_LLM_ENABLED",
]

# Prompts for semantic evaluation
SEMANTIC_EVALUATIONS = [
    {
        "id": "actionable_error",
        "question": "Does this tool's error handling provide actionable information for users and agents?",
        "category": OperationalRiskCategory.MISSING_ERROR_SCHEMA,
        "prompt_template": """Analyze the following MCP tool definition and evaluate if its error handling is actionable.

Tool Definition:
{tool_json}

Questions to consider:
1. Does the tool define clear error types or codes?
2. Are error messages specific enough to diagnose issues?
3. Can an AI agent programmatically handle different error cases?
4. Are retry-able vs permanent errors distinguished?

Respond with JSON:
{{
  "is_actionable": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "suggestions": ["list of improvement suggestions"]
}}
""",
    },
    {
        "id": "clear_failure_modes",
        "question": "Does this tool description clearly explain its failure modes?",
        "category": OperationalRiskCategory.SILENT_FAILURE_PATH,
        "prompt_template": """Analyze the following MCP tool definition's description for clarity about failure modes.

Tool Definition:
{tool_json}

Questions to consider:
1. Does the description mention what can go wrong?
2. Are edge cases or limitations documented?
3. Would an AI agent know what to expect when the tool fails?
4. Are there ambiguous phrases like "may fail" without specifics?

Respond with JSON:
{{
  "failure_modes_clear": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "missing_information": ["list of failure modes that should be documented"]
}}
""",
    },
    {
        "id": "scope_clarity",
        "question": "Is the tool's scope clearly defined and appropriately narrow?",
        "category": OperationalRiskCategory.OVERLOADED_TOOL_SCOPE,
        "prompt_template": """Analyze the following MCP tool definition for scope clarity and appropriateness.

Tool Definition:
{tool_json}

Questions to consider:
1. Does the tool do one thing well, or many things?
2. Is the description focused or does it mention many unrelated capabilities?
3. Would an AI agent know exactly when to use this tool vs others?
4. Are the input parameters coherent or do they suggest multiple purposes?

Respond with JSON:
{{
  "scope_appropriate": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "scope_issues": ["list of scope concerns"]
}}
""",
    },
]


class LLMJudgeProvider(InspectionProvider):
    """
    LLM-based semantic analysis provider.

    DISABLED BY DEFAULT - requires MCP_READINESS_LLM_MODEL environment
    variable to be set.

    Uses LLMs to evaluate semantic questions about tool definitions:
    - "Is this error message actionable by a human?"
    - "Does this tool description clearly explain failure modes?"
    - "Is the tool's scope appropriately narrow?"

    Supports any model via LiteLLM:
    - Local: ollama/llama2, ollama/mistral
    - OpenAI: gpt-4, gpt-3.5-turbo
    - Anthropic: claude-3-opus, claude-3-sonnet
    - Azure: azure/gpt-4
    """

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        enabled_evaluations: list[str] | None = None,
    ) -> None:
        """
        Initialize the LLM judge provider.

        Args:
            model: LiteLLM model identifier (default: from MCP_READINESS_LLM_MODEL env)
            api_base: Optional API base URL for self-hosted models
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
            enabled_evaluations: List of evaluation IDs to run (default: all)
        """
        self.model = model or os.environ.get("MCP_READINESS_LLM_MODEL")
        self.api_base = api_base or os.environ.get("MCP_READINESS_LLM_API_BASE")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enabled_evaluations = enabled_evaluations

    @property
    def name(self) -> str:
        return "llm-judge"

    @property
    def description(self) -> str:
        return (
            "Semantic analysis using LLMs to evaluate error handling, "
            "failure mode documentation, and scope clarity"
        )

    def is_available(self) -> bool:
        """
        Check if LLM provider is available.

        DISABLED by default - requires:
        1. litellm package installed
        2. MCP_READINESS_LLM_MODEL environment variable set
        """
        if not _litellm_available:
            return False

        # Check for explicit enable
        if os.environ.get("MCP_READINESS_LLM_ENABLED", "").lower() in ("true", "1", "yes"):
            return bool(self.model)

        # Check for model configured
        return bool(self.model)

    def get_unavailable_reason(self) -> str | None:
        if not _litellm_available:
            return f"litellm not installed: {_litellm_import_error}"

        if not self.model:
            return (
                "LLM provider disabled by default. Set MCP_READINESS_LLM_MODEL "
                "environment variable to enable (e.g., 'ollama/llama2' for local, "
                "'gpt-4' for OpenAI)"
            )

        return None

    async def analyze_tool(self, tool_definition: dict[str, Any]) -> list[Finding]:
        """
        Analyze a tool definition using LLM semantic evaluation.

        Runs each configured evaluation prompt against the tool definition
        and converts LLM responses to findings.
        """
        if not self.is_available():
            return []

        findings: list[Finding] = []
        tool_name = tool_definition.get("name", "unknown")

        import json

        tool_json = json.dumps(tool_definition, indent=2)

        # Run each evaluation
        evaluations_to_run = SEMANTIC_EVALUATIONS
        if self.enabled_evaluations:
            evaluations_to_run = [
                e for e in SEMANTIC_EVALUATIONS
                if e["id"] in self.enabled_evaluations
            ]

        for evaluation in evaluations_to_run:
            try:
                result = await self._run_evaluation(evaluation, tool_json)
                finding = self._result_to_finding(
                    evaluation, result, tool_name
                )
                if finding:
                    findings.append(finding)
            except Exception as e:
                # Log evaluation failure but continue with others
                findings.append(
                    Finding(
                        category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                        severity=Severity.INFO,
                        title=f"LLM evaluation failed: {evaluation['id']}",
                        description=str(e),
                        location=f"tool.{tool_name}",
                        provider=self.name,
                        rule_id=f"LLM-{evaluation['id']}-error",
                    )
                )

        return findings

    async def analyze_config(self, config: dict[str, Any]) -> list[Finding]:
        """
        Analyze an MCP configuration.

        Currently only performs semantic analysis on server descriptions
        if present. Most config-level checks are better handled by
        heuristic or OPA providers.
        """
        # Config analysis not implemented for LLM provider
        # Most config checks don't benefit from semantic analysis
        return []

    async def _run_evaluation(
        self,
        evaluation: dict[str, Any],
        tool_json: str,
    ) -> dict[str, Any]:
        """Run a single LLM evaluation."""
        prompt = evaluation["prompt_template"].format(tool_json=tool_json)

        # Use litellm for the API call
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at evaluating MCP tool definitions "
                        "for production readiness. Respond only with valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_base=self.api_base,
        )

        # Parse response
        import json

        content = response.choices[0].message.content
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": content}

    def _result_to_finding(
        self,
        evaluation: dict[str, Any],
        result: dict[str, Any],
        tool_name: str,
    ) -> Finding | None:
        """Convert an LLM evaluation result to a Finding."""
        eval_id = evaluation["id"]
        category = evaluation["category"]

        # Check for errors
        if "error" in result:
            return Finding(
                category=category,
                severity=Severity.INFO,
                title=f"LLM evaluation inconclusive: {eval_id}",
                description=result.get("error", "Unknown error"),
                location=f"tool.{tool_name}",
                evidence={"raw_response": result.get("raw")},
                provider=self.name,
                rule_id=f"LLM-{eval_id}-error",
            )

        # Determine if this is a finding based on the evaluation type
        is_issue = False
        confidence = result.get("confidence", 0.5)

        if eval_id == "actionable_error" and not result.get("is_actionable", True):
            is_issue = True
        elif eval_id == "clear_failure_modes" and not result.get("failure_modes_clear", True):
            is_issue = True
        elif eval_id == "scope_clarity" and not result.get("scope_appropriate", True):
            is_issue = True

        if not is_issue:
            return None

        # Determine severity based on confidence
        if confidence >= 0.8:
            severity = Severity.MEDIUM
        elif confidence >= 0.6:
            severity = Severity.LOW
        else:
            severity = Severity.INFO

        # Build description from LLM response
        reasoning = result.get("reasoning", "")
        suggestions = result.get("suggestions") or result.get("missing_information") or result.get("scope_issues") or []

        description = f"{evaluation['question']}\n\nLLM Analysis: {reasoning}"
        if suggestions:
            description += "\n\nSuggestions:\n- " + "\n- ".join(suggestions)

        return Finding(
            category=category,
            severity=severity,
            title=f"Semantic issue: {evaluation['question']}",
            description=description,
            location=f"tool.{tool_name}",
            evidence={
                "llm_response": result,
                "confidence": confidence,
                "model": self.model,
            },
            provider=self.name,
            remediation="\n".join(suggestions) if suggestions else None,
            rule_id=f"LLM-{eval_id}",
        )
