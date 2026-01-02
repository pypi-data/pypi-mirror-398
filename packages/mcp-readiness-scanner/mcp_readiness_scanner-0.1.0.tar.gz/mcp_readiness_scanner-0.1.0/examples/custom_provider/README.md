# Custom Provider Example

This example demonstrates how to create and register a custom inspection provider for MCP Readiness Scanner.

## Creating a Custom Provider

### Step 1: Create Your Provider Class

Create a Python module with a class that inherits from `InspectionProvider`:

```python
from mcpreadiness.providers.base import InspectionProvider
from mcpreadiness.core.models import Finding, Severity

class MyCustomProvider(InspectionProvider):
    def __init__(self):
        super().__init__(
            name="my-custom-provider",
            description="My custom inspection logic",
            version="1.0.0"
        )

    def is_available(self) -> bool:
        return True  # Check dependencies, etc.

    async def analyze_tool(self, tool_definition: dict) -> list[Finding]:
        # Your custom inspection logic here
        findings = []
        # ... analyze tool_definition and create findings ...
        return findings
```

### Step 2: Package Your Provider

Create a `pyproject.toml` for your custom provider package:

```toml
[project]
name = "my-mcp-provider"
version = "1.0.0"
dependencies = [
    "mcp-readiness-scanner>=0.1.0",
]

[project.entry-points."mcp_readiness.providers"]
my_provider = "my_package.providers:MyCustomProvider"
```

### Step 3: Install and Use

```bash
# Install your custom provider
pip install my-mcp-provider

# The scanner will automatically discover and use it
mcp-readiness scan-tool --tool my_tool.json
```

## Example Provider

See `my_custom_provider.py` for a complete example that checks:
- Organizational naming conventions
- Required metadata fields
- SLA documentation requirements
- Environment specifications

## Provider Interface

Your provider must implement:

### Required Methods

```python
def is_available(self) -> bool:
    """Check if provider can run (dependencies installed, etc.)"""

async def analyze_tool(self, tool_definition: dict) -> list[Finding]:
    """Analyze an MCP tool definition"""

async def analyze_config(self, config: dict) -> list[Finding]:
    """Analyze an MCP configuration"""
```

### Optional Methods

```python
async def initialize(self) -> None:
    """Called before scanning (setup resources)"""

async def cleanup(self) -> None:
    """Called after scanning (cleanup resources)"""

def get_unavailable_reason(self) -> str | None:
    """Explain why provider is unavailable"""
```

## Finding Structure

Create findings using the `Finding` model:

```python
Finding(
    category="operational_risk_category",  # See taxonomy
    severity=Severity.HIGH,               # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title="Short description",
    description="Detailed explanation",
    location="tool.field.path",           # Where the issue is
    provider=self.name,
    remediation="How to fix it",
    rule_id="CUSTOM-001",                 # Unique rule identifier
    evidence={"key": "value"}             # Supporting data
)
```

## Testing Your Provider

```python
import asyncio
from my_package.providers import MyCustomProvider

async def test_provider():
    provider = MyCustomProvider()

    tool_def = {
        "name": "my_tool",
        "description": "Does something"
    }

    findings = await provider.analyze_tool(tool_def)

    for finding in findings:
        print(f"{finding.severity}: {finding.title}")

asyncio.run(test_provider())
```

## Best Practices

1. **Clear Rule IDs**: Use a consistent prefix (e.g., `CUSTOM-001`, `ACME-001`)
2. **Actionable Findings**: Always include remediation guidance
3. **Fast Execution**: Keep analysis fast; use async for I/O
4. **Error Handling**: Gracefully handle malformed input
5. **Documentation**: Document your rules and their rationale
6. **Versioning**: Use semantic versioning for your provider

## Real-World Use Cases

Custom providers are useful for:

- **Organization-specific policies**: Naming conventions, required metadata
- **Compliance checks**: Industry-specific regulations (HIPAA, SOC2, etc.)
- **Integration validation**: Ensuring tools work with internal infrastructure
- **Performance requirements**: SLA documentation, timeout policies
- **Security policies**: Authentication, authorization, data handling
- **Team accountability**: Owner tracking, documentation requirements

## Publishing Your Provider

```bash
# Build your package
python -m build

# Publish to PyPI
python -m twine upload dist/*

# Users install with
pip install your-mcp-provider
```

