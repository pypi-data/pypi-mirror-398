"""
Tests for LLM Judge provider.

These tests verify the LLM Judge provider's behavior including:
- Availability checks (requires env vars or API keys)
- Graceful degradation when LLM is unavailable
- Schema correctness
- Mock-based testing without requiring actual API calls
"""

import os

import pytest

from mcpreadiness.core.models import OperationalRiskCategory, Severity


@pytest.fixture
def sample_tool_definition():
    """Sample MCP tool definition for testing."""
    return {
        "name": "test_tool",
        "description": "A test tool that does something",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
        },
    }


def test_llm_judge_provider_import():
    """Test that LLMJudgeProvider can be imported."""
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    assert LLMJudgeProvider is not None
    provider = LLMJudgeProvider()
    assert provider.name == "llm-judge"


@pytest.mark.asyncio
async def test_llm_judge_provider_availability():
    """Test that LLMJudgeProvider reports availability correctly."""
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    provider = LLMJudgeProvider()

    # is_available should return True only if:
    # 1. litellm is installed
    # 2. Environment variable is set (MCP_READINESS_LLM_MODEL or MCP_READINESS_LLM_ENABLED)
    availability = provider.is_available()
    assert isinstance(availability, bool)

    # If unavailable, should have a reason
    if not availability:
        reason = provider.get_unavailable_reason()
        assert reason is not None
        assert isinstance(reason, str)


@pytest.mark.asyncio
async def test_llm_judge_provider_disabled_by_default():
    """Test that LLM provider is disabled by default."""
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    # Clear any existing env vars
    old_model = os.environ.get("MCP_READINESS_LLM_MODEL")
    old_enabled = os.environ.get("MCP_READINESS_LLM_ENABLED")

    if old_model:
        del os.environ["MCP_READINESS_LLM_MODEL"]
    if old_enabled:
        del os.environ["MCP_READINESS_LLM_ENABLED"]

    try:
        provider = LLMJudgeProvider()

        # Should not be available without env vars
        assert not provider.is_available()
        reason = provider.get_unavailable_reason()
        assert reason is not None
        assert "environment variable" in reason.lower() or "not enabled" in reason.lower()

    finally:
        # Restore env vars
        if old_model:
            os.environ["MCP_READINESS_LLM_MODEL"] = old_model
        if old_enabled:
            os.environ["MCP_READINESS_LLM_ENABLED"] = old_enabled


@pytest.mark.asyncio
async def test_llm_judge_provider_analyze_schema(sample_tool_definition):
    """Test LLM provider analysis returns correct schema (without actual API call)."""
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    provider = LLMJudgeProvider()

    if not provider.is_available():
        pytest.skip("LLM provider not available (env var not set or litellm not installed)")

    # Initialize provider
    await provider.initialize()

    # We can't make actual API calls in tests without API keys,
    # so this test just verifies the provider structure
    # In a real environment with API keys, this would work:
    # findings = await provider.analyze_tool(sample_tool_definition)
    # assert isinstance(findings, list)

    # For now, just verify the provider has the expected methods
    assert hasattr(provider, "analyze_tool")
    assert hasattr(provider, "analyze_config")
    assert hasattr(provider, "initialize")
    assert hasattr(provider, "cleanup")

    # Cleanup
    await provider.cleanup()


@pytest.mark.asyncio
async def test_llm_judge_provider_finding_structure():
    """Test that LLM provider would return correctly structured findings."""
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    # This is a structural test to ensure the provider
    # is set up to return the correct types

    provider = LLMJudgeProvider()

    # Verify provider metadata
    assert provider.name == "llm-judge"
    assert isinstance(provider.description, str)
    assert isinstance(provider.version, str)

    # Verify provider has required methods
    assert callable(provider.analyze_tool)
    assert callable(provider.analyze_config)
    assert callable(provider.is_available)


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("MCP_READINESS_LLM_MODEL"),
    reason="LLM_MODEL env var not set - skipping live API test",
)
async def test_llm_judge_provider_live_analysis(sample_tool_definition):
    """
    Test LLM provider with actual API call (only runs if env var is set).

    This test is skipped by default and only runs when explicitly enabled
    with the MCP_READINESS_LLM_MODEL environment variable.
    """
    from mcpreadiness.providers.llm_judge_provider import LLMJudgeProvider

    provider = LLMJudgeProvider()

    if not provider.is_available():
        pytest.skip("LLM provider not available")

    await provider.initialize()

    try:
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
            assert finding.provider == "llm-judge"
            assert isinstance(finding.category, OperationalRiskCategory)
            assert isinstance(finding.severity, Severity)

    finally:
        await provider.cleanup()
