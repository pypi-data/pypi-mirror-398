"""
Tests for OPA (Open Policy Agent) provider.

These tests verify the OPA provider's behavior including:
- Availability checks
- Graceful degradation when OPA is unavailable
- Schema correctness
"""

import pytest

from mcpreadiness.core.models import OperationalRiskCategory, Severity


@pytest.fixture
def sample_tool_definition():
    """Sample MCP tool definition for testing."""
    return {
        "name": "test_tool",
        "description": "A test tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
        },
    }


def test_opa_provider_import():
    """Test that OpaProvider can be imported or is None if unavailable."""
    try:
        from mcpreadiness.providers.opa_provider import OpaProvider

        assert OpaProvider is not None
        provider = OpaProvider()
        assert provider.name == "opa"
    except ImportError:
        # OPA provider is optional, so this is acceptable
        from mcpreadiness.providers import OpaProvider

        assert OpaProvider is None


@pytest.mark.asyncio
async def test_opa_provider_availability():
    """Test that OpaProvider reports availability correctly."""
    try:
        from mcpreadiness.providers.opa_provider import OpaProvider

        provider = OpaProvider()

        # is_available should return True if opa binary is in PATH
        availability = provider.is_available()
        assert isinstance(availability, bool)

        # If unavailable, should have a reason
        if not availability:
            reason = provider.get_unavailable_reason()
            assert reason is not None
            assert isinstance(reason, str)

    except ImportError:
        pytest.skip("OPA provider not installed")


@pytest.mark.asyncio
async def test_opa_provider_analyze(sample_tool_definition):
    """Test OPA provider analysis."""
    try:
        from mcpreadiness.providers.opa_provider import OpaProvider

        provider = OpaProvider()

        if not provider.is_available():
            pytest.skip("OPA provider not available")

        # Initialize provider
        await provider.initialize()

        # Analyze tool
        findings = await provider.analyze_tool(sample_tool_definition)

        # Findings should be a list
        assert isinstance(findings, list)

        # Each finding should have required fields
        for finding in findings:
            assert hasattr(finding, "category")
            assert hasattr(finding, "severity")
            assert hasattr(finding, "title")
            assert hasattr(finding, "description")
            assert hasattr(finding, "provider")
            assert finding.provider == "opa"
            assert isinstance(finding.category, OperationalRiskCategory)
            assert isinstance(finding.severity, Severity)

        # Cleanup
        await provider.cleanup()

    except ImportError:
        pytest.skip("OPA provider not installed")


@pytest.mark.asyncio
async def test_opa_provider_analyze_config():
    """Test OPA provider config analysis."""
    try:
        from mcpreadiness.providers.opa_provider import OpaProvider

        provider = OpaProvider()

        if not provider.is_available():
            pytest.skip("OPA provider not available")

        sample_config = {
            "mcpServers": {
                "test": {
                    "command": "python",
                    "args": ["-m", "test_server"],
                }
            }
        }

        # Initialize provider
        await provider.initialize()

        # Analyze config
        findings = await provider.analyze_config(sample_config)

        # Findings should be a list (may be empty)
        assert isinstance(findings, list)

        # Cleanup
        await provider.cleanup()

    except ImportError:
        pytest.skip("OPA provider not installed")
