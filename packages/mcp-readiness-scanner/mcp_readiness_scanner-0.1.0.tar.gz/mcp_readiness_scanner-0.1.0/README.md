# MCP Readiness Scanner

**Production readiness scanner for MCP servers and agentic AI tools**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/mcp-readiness/scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/mcp-readiness/scanner/actions)

---

> **Note:** For security scanning, see [Cisco's MCP Scanner](https://github.com/cisco/mcp-scanner). This tool focuses on **operational readiness** — whether your MCP tools will behave reliably in production.

---

## What It Does

MCP Readiness Scanner analyzes MCP tool definitions and configurations for operational issues like:

- **Missing timeout guards** — Will operations hang indefinitely?
- **Unsafe retry loops** — Could retries cause resource exhaustion?
- **Silent failure paths** — Are errors properly surfaced?
- **Overloaded tool scope** — Is the tool trying to do too much?
- **Missing error schemas** — Can agents handle failures programmatically?

## Quick Start

```bash
# Install
pip install mcp-readiness-scanner

# Scan a tool definition
mcp-readiness scan-tool --tool my_tool.json

# Scan an MCP config
mcp-readiness scan-config --config-file ~/.config/mcp/config.json

# List available providers
mcp-readiness list-providers
```

**No API keys required.** Works out of the box with zero external dependencies.

## Example Output

```
$ mcp-readiness scan-tool --tool examples/sample_tool_definitions/bad_tool.json --format markdown

# MCP Readiness Scan Report

## Summary
**Target:** `examples/sample_tool_definitions/bad_tool.json`
**Readiness Score:** **25/100** (Critical)
**Production Ready:** No ❌

### Findings Overview
| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟠 High | 1 |
| 🟡 Medium | 4 |
| 🔵 Low | 2 |
| ⚪ Info | 0 |

## Findings

### 🟠 High (1)
#### 1. No timeout configuration
- **Category:** Missing Timeout Guard
- **Location:** `tool.do_everything`

Tool 'do_everything' does not specify a timeout. Operations may hang indefinitely...
```

## Features

### Inspection Providers

| Provider | Status | Dependencies | Description |
|----------|--------|--------------|-------------|
| **Heuristic** | ✅ Always Available | None | Static analysis for common issues |
| **YARA** | Optional | `yara-python` | Pattern matching on metadata |
| **OPA** | Optional | `opa` binary | Policy-based checks with Rego |
| **LLM Judge** | Disabled by default | LiteLLM + model | Semantic analysis |

### Output Formats

- **JSON** — For CI pipelines and programmatic consumption
- **Markdown** — For PR comments and human review
- **SARIF** — For GitHub Code Scanning integration

### Operational Risk Categories

| Category | Description |
|----------|-------------|
| `silent_failure_path` | Tool may fail without surfacing errors |
| `non_deterministic_response` | Response format varies unpredictably |
| `missing_timeout_guard` | Operations may hang indefinitely |
| `no_observability_hooks` | Lacks logging, metrics, or tracing |
| `unsafe_retry_loop` | Retry logic may cause resource exhaustion |
| `overloaded_tool_scope` | Too many capabilities in one tool |
| `no_fallback_contract` | No graceful degradation defined |
| `missing_error_schema` | Error responses lack structure |

## Installation

```bash
# Basic installation
pip install mcp-readiness-scanner

# With YARA support
pip install mcp-readiness-scanner[yara]

# With all optional dependencies
pip install mcp-readiness-scanner[all]
```

### Optional Dependencies

```bash
# For YARA pattern matching
pip install yara-python

# For OPA policy checks
brew install opa  # macOS
# or download from https://www.openpolicyagent.org/

# For LLM semantic analysis
pip install litellm
export MCP_READINESS_LLM_MODEL=ollama/llama2  # or gpt-4, claude-3-sonnet, etc.
```

## CI/CD Integration

### GitHub Actions

```yaml
name: MCP Readiness Check
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install mcp-readiness-scanner
      - run: mcp-readiness scan-tool --tool tool.json --format sarif -o results.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (no critical/high findings) |
| 1 | High severity findings found |
| 2 | Critical findings found |

## Configuration

Create `.mcp-readiness.toml` in your project:

```toml
[scan]
fail_on_critical = true
fail_on_high = false
min_score = 70

[heuristic]
max_capabilities = 10

[yara]
enabled = true

[llm]
enabled = false  # Disabled by default
model = "ollama/llama2"
```

Or use environment variables:

```bash
export MCP_READINESS_SCAN_FAIL_ON_CRITICAL=true
export MCP_READINESS_SCAN_MIN_SCORE=70
```

## Programmatic Usage

```python
import asyncio
from mcpreadiness import ScanOrchestrator
from mcpreadiness.providers import HeuristicProvider

async def main():
    orchestrator = ScanOrchestrator()
    orchestrator.register_provider(HeuristicProvider())

    result = await orchestrator.scan_tool({
        "name": "my_tool",
        "description": "Does something useful",
        "timeout": 30000,
    })

    print(f"Score: {result.readiness_score}/100")
    print(f"Ready: {result.is_production_ready}")

asyncio.run(main())
```

## Documentation

- [Architecture](docs/architecture.md) — System design and components
- [Taxonomy](docs/taxonomy.md) — Operational risk categories explained
- [Providers](docs/providers.md) — How to use and create providers
- [Usage](docs/usage.md) — Detailed CLI and configuration guide

## Contributing

Contributions are welcome! Please see our contributing guidelines.

```bash
# Development setup
git clone https://github.com/mcp-readiness/scanner
cd scanner
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check mcpreadiness tests
```

## License

Apache-2.0 — See [LICENSE](LICENSE) for details.

---

**MCP Readiness Scanner** — Because production reliability matters.
