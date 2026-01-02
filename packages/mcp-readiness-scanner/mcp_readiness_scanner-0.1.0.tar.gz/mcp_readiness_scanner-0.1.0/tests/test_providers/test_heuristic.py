"""Tests for the heuristic provider."""

import pytest

from mcpreadiness.core.models import OperationalRiskCategory, Severity
from mcpreadiness.providers.heuristic_provider import HeuristicProvider


@pytest.fixture
def provider():
    return HeuristicProvider()


class TestHeuristicProvider:
    """Tests for HeuristicProvider."""

    def test_provider_name(self, provider):
        assert provider.name == "heuristic"

    def test_provider_is_available(self, provider):
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_good_tool_minimal_findings(self, provider):
        """A well-configured tool should have minimal findings."""
        good_tool = {
            "name": "file_reader",
            "description": "Reads files from the filesystem with proper error handling and timeout protection.",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            "errorSchema": {
                "type": "object",
                "properties": {"code": {"type": "string"}, "message": {"type": "string"}},
            },
            "timeout": 30000,
            "maxRetries": 3,
            "rateLimit": {"requests": 100, "period": "minute"},
        }

        findings = await provider.analyze_tool(good_tool)

        # Good tool should have no high/critical findings
        high_critical = [
            f for f in findings if f.severity in (Severity.HIGH, Severity.CRITICAL)
        ]
        assert len(high_critical) == 0

    @pytest.mark.asyncio
    async def test_missing_timeout(self, provider):
        tool = {"name": "test_tool", "description": "A test tool"}
        findings = await provider.analyze_tool(tool)

        timeout_findings = [
            f
            for f in findings
            if f.category == OperationalRiskCategory.MISSING_TIMEOUT_GUARD
        ]
        assert len(timeout_findings) > 0
        assert any(f.severity == Severity.HIGH for f in timeout_findings)

    @pytest.mark.asyncio
    async def test_zero_timeout(self, provider):
        tool = {"name": "test_tool", "description": "A test tool", "timeout": 0}
        findings = await provider.analyze_tool(tool)

        timeout_findings = [
            f
            for f in findings
            if f.category == OperationalRiskCategory.MISSING_TIMEOUT_GUARD
        ]
        # Should detect zero timeout as invalid
        assert len(timeout_findings) > 0
        # At least one finding should mention the zero/invalid timeout
        assert any("0" in f.description or "invalid" in f.title.lower() for f in timeout_findings)

    @pytest.mark.asyncio
    async def test_missing_retry_limit(self, provider):
        tool = {"name": "test_tool", "description": "A test tool", "timeout": 30000}
        findings = await provider.analyze_tool(tool)

        retry_findings = [
            f for f in findings if f.category == OperationalRiskCategory.UNSAFE_RETRY_LOOP
        ]
        assert len(retry_findings) > 0

    @pytest.mark.asyncio
    async def test_excessive_capabilities(self, provider):
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "timeout": 30000,
            "capabilities": [f"cap_{i}" for i in range(15)],
        }
        findings = await provider.analyze_tool(tool)

        scope_findings = [
            f
            for f in findings
            if f.category == OperationalRiskCategory.OVERLOADED_TOOL_SCOPE
        ]
        assert len(scope_findings) > 0

    @pytest.mark.asyncio
    async def test_missing_error_schema(self, provider):
        tool = {"name": "test_tool", "description": "A test tool", "timeout": 30000}
        findings = await provider.analyze_tool(tool)

        error_findings = [
            f
            for f in findings
            if f.category == OperationalRiskCategory.MISSING_ERROR_SCHEMA
        ]
        assert len(error_findings) > 0

    @pytest.mark.asyncio
    async def test_missing_description(self, provider):
        tool = {"name": "test_tool", "timeout": 30000}
        findings = await provider.analyze_tool(tool)

        desc_findings = [f for f in findings if "description" in f.title.lower()]
        assert len(desc_findings) > 0
        assert any(f.severity == Severity.HIGH for f in desc_findings)

    @pytest.mark.asyncio
    async def test_short_description(self, provider):
        tool = {"name": "test_tool", "description": "Short", "timeout": 30000}
        findings = await provider.analyze_tool(tool)

        desc_findings = [f for f in findings if "vague" in f.title.lower()]
        assert len(desc_findings) > 0

    @pytest.mark.asyncio
    async def test_missing_input_schema(self, provider):
        tool = {"name": "test_tool", "description": "A test tool", "timeout": 30000}
        findings = await provider.analyze_tool(tool)

        schema_findings = [f for f in findings if "input" in f.title.lower()]
        assert len(schema_findings) > 0

    @pytest.mark.asyncio
    async def test_dangerous_phrases_best_effort(self, provider):
        tool = {
            "name": "test_tool",
            "description": "This tool uses best effort semantics",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        phrase_findings = [
            f for f in findings if "dangerous phrase" in f.title.lower()
        ]
        assert len(phrase_findings) > 0

    @pytest.mark.asyncio
    async def test_dangerous_phrases_ignore_error(self, provider):
        tool = {
            "name": "test_tool",
            "description": "This tool will ignore errors when possible",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        phrase_findings = [
            f for f in findings if "dangerous phrase" in f.title.lower()
        ]
        assert len(phrase_findings) > 0

    @pytest.mark.asyncio
    async def test_dangerous_phrases_fire_and_forget(self, provider):
        tool = {
            "name": "test_tool",
            "description": "This is a fire and forget operation",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        phrase_findings = [
            f for f in findings if "dangerous phrase" in f.title.lower()
        ]
        assert len(phrase_findings) > 0

    @pytest.mark.asyncio
    async def test_config_missing_server_timeout(self, provider):
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "node",
                    "args": ["server.js"],
                }
            }
        }
        findings = await provider.analyze_config(config)

        timeout_findings = [
            f
            for f in findings
            if f.category == OperationalRiskCategory.MISSING_TIMEOUT_GUARD
        ]
        assert len(timeout_findings) > 0

    @pytest.mark.asyncio
    async def test_config_missing_command(self, provider):
        config = {"mcpServers": {"test_server": {"args": ["--help"]}}}
        findings = await provider.analyze_config(config)

        command_findings = [f for f in findings if "command" in f.title.lower()]
        assert len(command_findings) > 0

    @pytest.mark.asyncio
    async def test_config_sensitive_env_vars(self, provider):
        config = {
            "mcpServers": {
                "test_server": {
                    "command": "node",
                    "env": {"API_KEY": "secret123"},
                }
            }
        }
        findings = await provider.analyze_config(config)

        env_findings = [f for f in findings if "environment" in f.title.lower()]
        assert len(env_findings) > 0

    @pytest.mark.asyncio
    async def test_missing_output_schema(self, provider):
        """Test that tools without output schema are flagged."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        output_findings = [f for f in findings if "output schema" in f.title.lower()]
        assert len(output_findings) > 0
        assert any(f.rule_id == "HEUR-016" for f in output_findings)

    @pytest.mark.asyncio
    async def test_missing_authentication(self, provider):
        """Test that tools mentioning external APIs without auth config are flagged."""
        tool = {
            "name": "api_caller",
            "description": "Calls an external REST API endpoint to fetch data",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        auth_findings = [f for f in findings if "authentication" in f.title.lower()]
        assert len(auth_findings) > 0
        assert any(f.rule_id == "HEUR-017" for f in auth_findings)

    @pytest.mark.asyncio
    async def test_blocking_operations(self, provider):
        """Test that blocking operation indicators are detected."""
        tool = {
            "name": "blocker",
            "description": "This operation blocks until the file is ready",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        blocking_findings = [f for f in findings if "blocking" in f.title.lower()]
        assert len(blocking_findings) > 0
        assert any(f.rule_id == "HEUR-018" for f in blocking_findings)

    @pytest.mark.asyncio
    async def test_missing_idempotency(self, provider):
        """Test that state-changing operations without idempotency docs are flagged."""
        tool = {
            "name": "updater",
            "description": "Updates the user record in the database",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        idempotency_findings = [f for f in findings if "idempotency" in f.title.lower()]
        assert len(idempotency_findings) > 0
        assert any(f.rule_id == "HEUR-019" for f in idempotency_findings)

    @pytest.mark.asyncio
    async def test_missing_version(self, provider):
        """Test that tools without version info are flagged."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        version_findings = [f for f in findings if "version" in f.title.lower()]
        assert len(version_findings) > 0
        assert any(f.rule_id == "HEUR-020" for f in version_findings)

    @pytest.mark.asyncio
    async def test_deprecated_tool(self, provider):
        """Test that deprecated tools are flagged."""
        tool = {
            "name": "old_tool",
            "description": "This tool is deprecated and will be removed soon",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        unstable_findings = [
            f for f in findings if "unstable" in f.title.lower() or "deprecated" in f.title.lower()
        ]
        assert len(unstable_findings) > 0
        assert any(f.rule_id == "HEUR-021" for f in unstable_findings)

    @pytest.mark.asyncio
    async def test_experimental_tool(self, provider):
        """Test that experimental tools are flagged."""
        tool = {
            "name": "new_tool",
            "description": "This is an experimental feature",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        unstable_findings = [
            f for f in findings if "unstable" in f.title.lower() or "deprecated" in f.title.lower()
        ]
        assert len(unstable_findings) > 0
        assert any(f.rule_id == "HEUR-021" for f in unstable_findings)

    @pytest.mark.asyncio
    async def test_missing_resource_cleanup(self, provider):
        """Test that tools using resources without cleanup docs are flagged."""
        tool = {
            "name": "connector",
            "description": "Opens a database connection to fetch records",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        cleanup_findings = [f for f in findings if "cleanup" in f.title.lower()]
        assert len(cleanup_findings) > 0
        assert any(f.rule_id == "HEUR-022" for f in cleanup_findings)

    @pytest.mark.asyncio
    async def test_bulk_operation_without_safeguards(self, provider):
        """Test that bulk operations without safeguards are flagged."""
        tool = {
            "name": "bulk_deleter",
            "description": "Performs batch delete operations on matching records",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        bulk_findings = [f for f in findings if "bulk" in f.title.lower()]
        assert len(bulk_findings) > 0
        assert any(f.rule_id == "HEUR-023" for f in bulk_findings)

    @pytest.mark.asyncio
    async def test_missing_circuit_breaker(self, provider):
        """Test that tools calling external services without circuit breakers are flagged."""
        tool = {
            "name": "api_tool",
            "description": "Makes HTTP requests to an external API service",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        circuit_findings = [f for f in findings if "circuit breaker" in f.title.lower()]
        assert len(circuit_findings) > 0
        assert any(f.rule_id == "HEUR-024" for f in circuit_findings)

    @pytest.mark.asyncio
    async def test_missing_observability(self, provider):
        """Test that tools without observability config are flagged."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "timeout": 30000,
        }
        findings = await provider.analyze_tool(tool)

        obs_findings = [f for f in findings if "observability" in f.title.lower()]
        assert len(obs_findings) > 0
        assert any(f.rule_id == "HEUR-025" for f in obs_findings)
