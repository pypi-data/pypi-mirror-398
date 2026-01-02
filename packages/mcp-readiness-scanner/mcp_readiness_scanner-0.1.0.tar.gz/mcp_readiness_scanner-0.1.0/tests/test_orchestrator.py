"""Tests for the scan orchestrator."""


import pytest

from mcpreadiness.core.models import (
    Finding,
    OperationalRiskCategory,
    Severity,
)
from mcpreadiness.core.orchestrator import (
    ScanOrchestrator,
)
from mcpreadiness.providers.base import InspectionProvider


class MockProvider(InspectionProvider):
    """Mock provider for testing."""

    def __init__(self, name: str = "mock", findings: list[Finding] | None = None):
        self._name = name
        self._findings = findings or []
        self._available = True

    @property
    def name(self) -> str:
        return self._name

    async def analyze_tool(self, tool_definition: dict) -> list[Finding]:
        return self._findings

    async def analyze_config(self, config: dict) -> list[Finding]:
        return self._findings

    def is_available(self) -> bool:
        return self._available


class TestScanOrchestrator:
    """Tests for ScanOrchestrator."""

    def test_register_provider(self):
        orchestrator = ScanOrchestrator()
        provider = MockProvider("test")
        orchestrator.register_provider(provider)
        assert orchestrator.get_provider("test") is provider

    def test_register_duplicate_provider_raises(self):
        orchestrator = ScanOrchestrator()
        provider1 = MockProvider("test")
        provider2 = MockProvider("test")
        orchestrator.register_provider(provider1)
        with pytest.raises(ValueError, match="already registered"):
            orchestrator.register_provider(provider2)

    def test_unregister_provider(self):
        orchestrator = ScanOrchestrator()
        provider = MockProvider("test")
        orchestrator.register_provider(provider)
        assert orchestrator.unregister_provider("test") is True
        assert orchestrator.get_provider("test") is None

    def test_unregister_nonexistent_provider(self):
        orchestrator = ScanOrchestrator()
        assert orchestrator.unregister_provider("nonexistent") is False

    def test_list_providers(self):
        orchestrator = ScanOrchestrator()
        p1 = MockProvider("p1")
        p2 = MockProvider("p2")
        orchestrator.register_provider(p1)
        orchestrator.register_provider(p2)
        providers = orchestrator.list_providers()
        assert len(providers) == 2

    def test_list_available_providers(self):
        orchestrator = ScanOrchestrator()
        p1 = MockProvider("p1")
        p2 = MockProvider("p2")
        p2._available = False
        orchestrator.register_provider(p1)
        orchestrator.register_provider(p2)
        available = orchestrator.list_available_providers()
        assert len(available) == 1
        assert available[0].name == "p1"

    @pytest.mark.asyncio
    async def test_scan_tool_no_findings(self):
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("test"))

        result = await orchestrator.scan_tool({"name": "my_tool"})

        assert result.target == "my_tool"
        assert result.findings == []
        assert result.readiness_score == 100
        assert "test" in result.providers_used

    @pytest.mark.asyncio
    async def test_scan_tool_with_findings(self):
        finding = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Test finding",
            description="Test",
            provider="test",
        )
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("test", [finding]))

        result = await orchestrator.scan_tool({"name": "my_tool"})

        assert len(result.findings) == 1
        assert result.readiness_score == 85  # 100 - 15 (HIGH)

    @pytest.mark.asyncio
    async def test_scan_tool_multiple_providers(self):
        finding1 = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Finding 1",
            description="Test",
            provider="p1",
        )
        finding2 = Finding(
            category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
            severity=Severity.MEDIUM,
            title="Finding 2",
            description="Test",
            provider="p2",
        )
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("p1", [finding1]))
        orchestrator.register_provider(MockProvider("p2", [finding2]))

        result = await orchestrator.scan_tool({"name": "my_tool"})

        assert len(result.findings) == 2
        assert result.readiness_score == 75  # 100 - 15 - 10

    @pytest.mark.asyncio
    async def test_scan_tool_select_providers(self):
        finding1 = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Finding 1",
            description="Test",
            provider="p1",
        )
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("p1", [finding1]))
        orchestrator.register_provider(MockProvider("p2", []))

        result = await orchestrator.scan_tool(
            {"name": "my_tool"}, providers=["p1"]
        )

        assert len(result.findings) == 1
        assert result.providers_used == ["p1"]

    @pytest.mark.asyncio
    async def test_scan_tool_unknown_provider_raises(self):
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("test"))

        with pytest.raises(ValueError, match="not registered"):
            await orchestrator.scan_tool({"name": "my_tool"}, providers=["unknown"])

    @pytest.mark.asyncio
    async def test_scan_config(self):
        orchestrator = ScanOrchestrator()
        orchestrator.register_provider(MockProvider("test"))

        result = await orchestrator.scan_config({"mcpServers": {}})

        assert result.target == "mcp_config"
        assert "test" in result.providers_used


class TestReadinessScore:
    """Tests for readiness score calculation."""

    def test_no_findings_score_100(self):
        score = ScanOrchestrator.calculate_readiness_score([])
        assert score == 100

    def test_critical_finding_deducts_25(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.CRITICAL,
            title="Critical",
            description="Test",
            provider="test",
        )
        score = ScanOrchestrator.calculate_readiness_score([finding])
        assert score == 75

    def test_high_finding_deducts_15(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.HIGH,
            title="High",
            description="Test",
            provider="test",
        )
        score = ScanOrchestrator.calculate_readiness_score([finding])
        assert score == 85

    def test_medium_finding_deducts_10(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.MEDIUM,
            title="Medium",
            description="Test",
            provider="test",
        )
        score = ScanOrchestrator.calculate_readiness_score([finding])
        assert score == 90

    def test_low_finding_deducts_5(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.LOW,
            title="Low",
            description="Test",
            provider="test",
        )
        score = ScanOrchestrator.calculate_readiness_score([finding])
        assert score == 95

    def test_info_finding_deducts_0(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.INFO,
            title="Info",
            description="Test",
            provider="test",
        )
        score = ScanOrchestrator.calculate_readiness_score([finding])
        assert score == 100

    def test_multiple_findings_cumulative(self):
        findings = [
            Finding(
                category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                severity=Severity.HIGH,  # -15
                title="High",
                description="Test",
                provider="test",
            ),
            Finding(
                category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                severity=Severity.MEDIUM,  # -10
                title="Medium",
                description="Test",
                provider="test",
            ),
            Finding(
                category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
                severity=Severity.LOW,  # -5
                title="Low",
                description="Test",
                provider="test",
            ),
        ]
        score = ScanOrchestrator.calculate_readiness_score(findings)
        assert score == 70  # 100 - 15 - 10 - 5

    def test_score_minimum_is_0(self):
        findings = [
            Finding(
                category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                severity=Severity.CRITICAL,
                title=f"Critical {i}",
                description="Test",
                provider="test",
            )
            for i in range(10)
        ]
        score = ScanOrchestrator.calculate_readiness_score(findings)
        assert score == 0  # Should not go negative
