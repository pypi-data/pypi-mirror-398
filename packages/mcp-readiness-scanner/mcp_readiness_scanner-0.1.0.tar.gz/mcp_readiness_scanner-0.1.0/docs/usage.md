# MCP Readiness Scanner - Usage Guide

## Installation

```bash
# Basic installation
pip install mcp-readiness-scanner

# With YARA support
pip install mcp-readiness-scanner[yara]

# With all optional dependencies
pip install mcp-readiness-scanner[all]
```

## Quick Start

### Scan a Tool Definition

```bash
# Scan a tool definition file
mcp-readiness scan-tool --tool my_tool.json

# Output as Markdown
mcp-readiness scan-tool --tool my_tool.json --format markdown

# Pipe JSON from stdin
cat my_tool.json | mcp-readiness scan-tool

# Save to file
mcp-readiness scan-tool --tool my_tool.json --output report.json
```

### Scan an MCP Configuration

```bash
# Scan a config file
mcp-readiness scan-config --config-file ~/.config/mcp/config.json

# Output as Markdown for PR comment
mcp-readiness scan-config --config-file config.json --format markdown
```

### List Available Providers

```bash
mcp-readiness list-providers
```

### List Risk Categories

```bash
mcp-readiness list-categories
```

## Command Reference

### `scan-tool`

Scan an MCP tool definition for operational readiness issues.

```bash
mcp-readiness scan-tool [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--tool`, `-t` | Path to tool definition JSON file |
| `--providers`, `-p` | Comma-separated list of providers |
| `--format`, `-f` | Output format: json, markdown, sarif |
| `--output`, `-o` | Output file path (default: stdout) |

**Examples:**

```bash
# Basic scan
mcp-readiness scan-tool --tool tool.json

# Select providers
mcp-readiness scan-tool --tool tool.json --providers heuristic,yara

# SARIF for GitHub Code Scanning
mcp-readiness scan-tool --tool tool.json --format sarif --output results.sarif
```

### `scan-config`

Scan an MCP configuration file.

```bash
mcp-readiness scan-config [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--config-file`, `-c` | Path to MCP config file (required) |
| `--providers`, `-p` | Comma-separated list of providers |
| `--format`, `-f` | Output format: json, markdown, sarif |
| `--output`, `-o` | Output file path (default: stdout) |

### `list-providers`

Show available inspection providers and their status.

```bash
mcp-readiness list-providers
```

### `list-categories`

Show the operational risk taxonomy.

```bash
# Text output
mcp-readiness list-categories

# JSON output
mcp-readiness list-categories --format json
```

### `init`

Create a configuration file with defaults.

```bash
# Create .mcp-readiness.toml
mcp-readiness init

# Create YAML config
mcp-readiness init --format yaml
```

## Configuration

### Configuration File

Create `.mcp-readiness.toml` in your project root:

```toml
[scan]
fail_on_critical = true
fail_on_high = false
min_score = 70
providers = ["heuristic", "yara"]

[output]
format = "json"
verbose = false

[heuristic]
enabled = true
max_capabilities = 10
min_description_length = 20

[yara]
enabled = true
rules_dir = "custom/rules"

[opa]
enabled = true
policies_dir = "custom/policies"

[llm]
enabled = false
model = "ollama/llama2"
```

### Environment Variables

```bash
# Scan configuration
export MCP_READINESS_SCAN_FAIL_ON_CRITICAL=true
export MCP_READINESS_SCAN_MIN_SCORE=70

# Output configuration
export MCP_READINESS_OUTPUT_FORMAT=markdown

# LLM provider
export MCP_READINESS_LLM_MODEL=gpt-4
export MCP_READINESS_LLM_ENABLED=true
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

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install scanner
        run: pip install mcp-readiness-scanner

      - name: Scan tools
        run: |
          mcp-readiness scan-tool \
            --tool tools/my_tool.json \
            --format sarif \
            --output results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### GitLab CI

```yaml
mcp-readiness:
  image: python:3.11
  script:
    - pip install mcp-readiness-scanner
    - mcp-readiness scan-tool --tool tool.json --format json > report.json
  artifacts:
    reports:
      codequality: report.json
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mcp-readiness
        name: MCP Readiness Check
        entry: mcp-readiness scan-tool --tool
        language: python
        files: \.json$
        additional_dependencies: [mcp-readiness-scanner]
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (no critical/high findings, score above threshold) |
| 1 | High severity findings or score below threshold |
| 2 | Critical findings found |

Control exit behavior with configuration:

```toml
[scan]
fail_on_critical = true  # Exit 2 on critical findings
fail_on_high = true      # Exit 1 on high findings
min_score = 80           # Exit 1 if score below 80
```

## Output Formats

### JSON

Machine-readable format for CI pipelines:

```json
{
  "target": "my_tool.json",
  "findings": [...],
  "readiness_score": 85,
  "is_production_ready": true,
  "providers_used": ["heuristic"]
}
```

### Markdown

Human-readable for PR comments:

```markdown
# MCP Readiness Scan Report

## Summary
**Target:** `my_tool.json`
**Readiness Score:** **85/100** (Good)
**Production Ready:** Yes ✅

## Findings
### 🟡 Medium (1)
#### 1. No rate limit configuration
...
```

### SARIF

GitHub Code Scanning integration:

```json
{
  "version": "2.1.0",
  "runs": [{
    "tool": {"driver": {"name": "mcp-readiness-scanner"}},
    "results": [...]
  }]
}
```

## Programmatic Usage

```python
import asyncio
from mcpreadiness import ScanOrchestrator
from mcpreadiness.providers import HeuristicProvider

async def main():
    # Create orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.register_provider(HeuristicProvider())

    # Define tool
    tool = {
        "name": "my_tool",
        "description": "Does something useful",
        "timeout": 30000,
    }

    # Scan
    result = await orchestrator.scan_tool(tool)

    # Check result
    print(f"Score: {result.readiness_score}")
    print(f"Production Ready: {result.is_production_ready}")

    for finding in result.findings:
        print(f"[{finding.severity.value}] {finding.title}")

asyncio.run(main())
```
