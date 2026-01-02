# MCP Readiness Scanner - Providers Guide

This document explains how to use, configure, and create custom inspection providers.

## Built-in Providers

### Heuristic Provider

**Status:** Always Available (no external dependencies)

The heuristic provider performs static analysis using Python code. It's the default provider and runs without any additional installation.

#### Checks Performed

| Check | Severity | Rule ID |
|-------|----------|---------|
| Missing timeout configuration | High | HEUR-001 |
| Zero/invalid timeout value | High | HEUR-002 |
| Missing retry limit | Medium | HEUR-003 |
| Negative retry limit | High | HEUR-004 |
| High retry limit (>10) | Medium | HEUR-005 |
| Excessive capabilities (>10) | Medium | HEUR-006 |
| Many input parameters (>15) | Low | HEUR-007 |
| Missing error schema | Medium | HEUR-008 |
| Missing description | High | HEUR-009 |
| Short/vague description | Low | HEUR-010 |
| Missing input schema | Medium | HEUR-011 |
| No required fields | Low | HEUR-012 |
| Missing rate limit | Low | HEUR-013 |
| Dangerous phrases | Medium | HEUR-014 |
| Non-deterministic indicators | Info | HEUR-015 |

#### Configuration

```toml
[heuristic]
enabled = true
max_capabilities = 10
min_description_length = 20
```

### YARA Provider

**Status:** Optional (requires `yara-python`)

Pattern matching on tool metadata using YARA rules.

#### Installation

```bash
pip install yara-python
```

#### Configuration

```toml
[yara]
enabled = true
rules_dir = "custom/rules"  # Optional, defaults to built-in rules
```

#### Custom Rules

Add `.yar` files to `rules/operational/` or specify a custom directory:

```yara
rule CustomRule
{
    meta:
        title = "Custom pattern detected"
        description = "Detailed description"
        category = "silent_failure"
        severity = "medium"
        remediation = "How to fix"

    strings:
        $pattern = "dangerous pattern" nocase

    condition:
        $pattern
}
```

Supported meta fields:
- `title`: Short title for finding
- `description`: Detailed description
- `category`: One of the taxonomy categories
- `severity`: critical, high, medium, low, info
- `remediation`: Fix suggestion

### OPA Provider

**Status:** Optional (requires `opa` binary)

Policy evaluation using Open Policy Agent and Rego.

#### Installation

Download from: https://www.openpolicyagent.org/docs/latest/#running-opa

```bash
# macOS
brew install opa

# Linux
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static
chmod +x opa
sudo mv opa /usr/local/bin/
```

#### Configuration

```toml
[opa]
enabled = true
policies_dir = "custom/policies"  # Optional
opa_binary = "opa"  # Optional, path to OPA binary
```

#### Custom Policies

Add `.rego` files to `rules/policies/`:

```rego
package mcp.readiness

# Violation for missing feature
violation[msg] {
    not input.has_feature
    msg := sprintf("Tool '%s' is missing feature", [input.tool_name])
}

# Violation with threshold
violation[msg] {
    input.value > 100
    msg := sprintf("Value %d exceeds threshold", [input.value])
}
```

The provider creates a facts document with:

```json
{
  "type": "tool",
  "tool_name": "...",
  "has_timeout": true,
  "timeout_value": 30000,
  "has_error_schema": false,
  "capabilities_count": 5,
  "has_retry_limit": true,
  "retry_limit": 3,
  "has_input_schema": true,
  "input_properties_count": 4,
  "has_required_fields": true,
  "has_description": true,
  "description_length": 150,
  "has_rate_limit": false,
  "raw": { /* full tool definition */ }
}
```

### LLM Judge Provider

**Status:** Disabled by Default

Semantic analysis using LLMs for questions that are difficult to check statically.

#### Enabling

```bash
# Set environment variable
export MCP_READINESS_LLM_MODEL=ollama/llama2

# Or in config
```

```toml
[llm]
enabled = true
model = "ollama/llama2"  # Or gpt-4, claude-3-sonnet, etc.
api_base = "http://localhost:11434"  # For Ollama
temperature = 0.1
max_tokens = 1024
```

#### Supported Models

Uses LiteLLM, supporting:
- **Local (no API key):** `ollama/llama2`, `ollama/mistral`
- **OpenAI:** `gpt-4`, `gpt-3.5-turbo`
- **Anthropic:** `claude-3-opus`, `claude-3-sonnet`
- **Azure:** `azure/gpt-4`

#### Evaluations Performed

1. **Actionable Errors**: Are error messages useful for debugging?
2. **Clear Failure Modes**: Does documentation explain what can go wrong?
3. **Scope Clarity**: Is the tool's purpose well-defined?

## Creating Custom Providers

### Provider Interface

```python
from mcpreadiness.providers.base import InspectionProvider
from mcpreadiness.core.models import Finding, OperationalRiskCategory, Severity

class MyProvider(InspectionProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    @property
    def description(self) -> str:
        return "Description of what this provider does"

    def is_available(self) -> bool:
        # Check if dependencies are available
        return True

    def get_unavailable_reason(self) -> str | None:
        if not self.is_available():
            return "Reason why provider is unavailable"
        return None

    async def initialize(self) -> None:
        # Called before analysis (e.g., load rules)
        pass

    async def analyze_tool(self, tool_definition: dict) -> list[Finding]:
        findings = []

        # Your analysis logic here
        if some_condition:
            findings.append(Finding(
                category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                severity=Severity.HIGH,
                title="Issue found",
                description="Detailed description",
                location="tool.name.field",
                evidence={"key": "value"},
                provider=self.name,
                remediation="How to fix",
                rule_id="MY-001",
            ))

        return findings

    async def analyze_config(self, config: dict) -> list[Finding]:
        # Similar to analyze_tool
        return []

    async def cleanup(self) -> None:
        # Called after analysis
        pass
```

### Registering Custom Providers

```python
from mcpreadiness.core.orchestrator import ScanOrchestrator
from my_provider import MyProvider

orchestrator = ScanOrchestrator()
orchestrator.register_provider(MyProvider())

result = await orchestrator.scan_tool(tool_definition)
```

### Provider Best Practices

1. **Be deterministic**: Same input should produce same findings
2. **Handle errors gracefully**: Don't crash on malformed input
3. **Include rule IDs**: Make findings traceable
4. **Provide remediation**: Help users fix issues
5. **Check availability**: Verify dependencies before running
6. **Use appropriate severities**: Follow the severity guidelines

## Provider Selection

By default, all available providers run. To select specific providers:

### CLI

```bash
mcp-readiness scan-tool --tool tool.json --providers heuristic,yara
```

### Configuration

```toml
[scan]
providers = ["heuristic", "opa"]
```

### Programmatic

```python
result = await orchestrator.scan_tool(
    tool_definition,
    providers=["heuristic", "yara"]
)
```
