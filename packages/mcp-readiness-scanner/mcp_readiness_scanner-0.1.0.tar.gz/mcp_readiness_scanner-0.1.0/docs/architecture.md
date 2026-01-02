# MCP Readiness Scanner - Architecture

## Overview

MCP Readiness Scanner is a vendor-neutral inspection orchestration layer for analyzing MCP (Model Context Protocol) servers and agentic AI tools for operational readiness. It focuses on production reliability and failure modes, complementing security-focused tools like Cisco's MCP Scanner.

## Design Principles

1. **OSS-First**: Works out of the box with zero vendor API keys
2. **Provider Abstraction**: Pluggable inspection engines for extensibility
3. **Enterprise-Extensible**: Optional commercial providers can be added
4. **CI-Ready**: Outputs designed for pipeline integration

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI                                    │
│                  (Click-based interface)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Layer                           │
│           (TOML/YAML/JSON + Environment Variables)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Scan Orchestrator                             │
│                                                                  │
│  • Provider registration and management                          │
│  • Concurrent provider execution                                 │
│  • Finding aggregation                                          │
│  • Readiness score calculation                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Heuristic   │   │     YARA      │   │      OPA      │
│   Provider    │   │   Provider    │   │   Provider    │
│  (Built-in)   │   │  (Optional)   │   │  (Optional)   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Python      │   │  YARA Rules   │   │ Rego Policies │
│  Heuristics   │   │ (.yar files)  │   │(.rego files)  │
└───────────────┘   └───────────────┘   └───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Report Generators                             │
│                                                                  │
│  ┌─────────┐    ┌───────────┐    ┌─────────┐                   │
│  │  JSON   │    │ Markdown  │    │  SARIF  │                   │
│  │ Report  │    │  Report   │    │ Report  │                   │
│  └─────────┘    └───────────┘    └─────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### Scan Orchestrator (`core/orchestrator.py`)

The central coordination point that:

- Manages provider lifecycle (register, initialize, cleanup)
- Runs providers concurrently using asyncio
- Aggregates findings from all providers
- Calculates readiness scores

### Inspection Providers

#### Heuristic Provider (Always Available)

Zero-dependency provider that analyzes:
- Timeout configuration
- Retry limits
- Capability scope
- Error schemas
- Description quality
- Input validation
- Rate limiting
- Dangerous phrases

#### YARA Provider (Optional)

Pattern matching using YARA rules:
- Scans tool metadata as text
- Detects dangerous phrases
- Identifies missing fields
- Requires `yara-python` package

#### OPA Provider (Optional)

Policy evaluation using Open Policy Agent:
- Creates normalized facts document
- Evaluates Rego policies
- Requires `opa` binary in PATH

#### LLM Judge Provider (Disabled by Default)

Semantic analysis using LLMs:
- Evaluates error message actionability
- Checks failure mode documentation
- Requires explicit configuration

### Models (`core/models.py`)

Pydantic v2 models for:
- `Finding`: Individual issue detected
- `ScanResult`: Aggregated scan output
- `Severity`: Issue severity levels
- `OperationalRiskCategory`: Issue classification

### Report Generators

- **JSON**: Machine-readable for CI pipelines
- **Markdown**: Human-readable for PR comments
- **SARIF**: GitHub Code Scanning integration

## Data Flow

1. User provides tool definition or config file
2. CLI loads configuration and creates orchestrator
3. Orchestrator registers enabled providers
4. Providers analyze input concurrently
5. Findings are aggregated
6. Readiness score is calculated
7. Report is generated in requested format

## Readiness Score Calculation

Score starts at 100 and deducts points per finding:

| Severity | Deduction |
|----------|-----------|
| Critical | -25       |
| High     | -15       |
| Medium   | -10       |
| Low      | -5        |
| Info     | 0         |

Minimum score is 0.

## Extension Points

### Custom Providers

Implement `InspectionProvider` interface:

```python
class MyProvider(InspectionProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    async def analyze_tool(self, tool_definition: dict) -> list[Finding]:
        # Custom analysis logic
        pass

    async def analyze_config(self, config: dict) -> list[Finding]:
        # Custom analysis logic
        pass
```

### Custom YARA Rules

Add `.yar` files to `rules/operational/`:

```yara
rule MyRule {
    meta:
        title = "My Rule"
        category = "silent_failure"
        severity = "medium"
    strings:
        $pattern = "dangerous pattern" nocase
    condition:
        $pattern
}
```

### Custom OPA Policies

Add `.rego` files to `rules/policies/`:

```rego
package mcp.readiness

violation[msg] {
    not input.has_timeout
    msg := "Custom violation message"
}
```
