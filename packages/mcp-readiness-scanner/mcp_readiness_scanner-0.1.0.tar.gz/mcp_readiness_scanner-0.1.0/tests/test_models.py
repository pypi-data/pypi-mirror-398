"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from mcpreadiness.core.models import (
    Finding,
    OperationalRiskCategory,
    ScanResult,
    Severity,
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_from_string(self):
        assert Severity("critical") == Severity.CRITICAL
        assert Severity("high") == Severity.HIGH


class TestOperationalRiskCategory:
    """Tests for OperationalRiskCategory enum."""

    def test_category_values(self):
        assert OperationalRiskCategory.SILENT_FAILURE_PATH.value == "silent_failure_path"
        assert OperationalRiskCategory.MISSING_TIMEOUT_GUARD.value == "missing_timeout_guard"

    def test_all_categories_defined(self):
        expected = [
            "silent_failure_path",
            "non_deterministic_response",
            "missing_timeout_guard",
            "no_observability_hooks",
            "unsafe_retry_loop",
            "overloaded_tool_scope",
            "no_fallback_contract",
            "missing_error_schema",
        ]
        actual = [c.value for c in OperationalRiskCategory]
        assert actual == expected


class TestFinding:
    """Tests for Finding model."""

    def test_minimal_finding(self):
        finding = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Test finding",
            description="Test description",
            provider="test",
        )
        assert finding.category == OperationalRiskCategory.MISSING_TIMEOUT_GUARD
        assert finding.severity == Severity.HIGH
        assert finding.location is None
        assert finding.evidence is None

    def test_full_finding(self):
        finding = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.CRITICAL,
            title="Critical issue",
            description="Something is very wrong",
            location="tool.my_tool.config",
            evidence={"key": "value"},
            provider="heuristic",
            remediation="Fix it",
            rule_id="HEUR-001",
        )
        assert finding.location == "tool.my_tool.config"
        assert finding.evidence == {"key": "value"}
        assert finding.rule_id == "HEUR-001"

    def test_finding_json_serialization(self):
        finding = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Test",
            description="Test",
            provider="test",
        )
        json_data = finding.model_dump(mode="json")
        assert json_data["category"] == "missing_timeout_guard"
        assert json_data["severity"] == "high"

    def test_finding_from_dict(self):
        data = {
            "category": "missing_timeout_guard",
            "severity": "high",
            "title": "Test",
            "description": "Test",
            "provider": "test",
        }
        finding = Finding.model_validate(data)
        assert finding.category == OperationalRiskCategory.MISSING_TIMEOUT_GUARD


class TestScanResult:
    """Tests for ScanResult model."""

    def test_minimal_scan_result(self):
        result = ScanResult(
            target="test_tool",
            readiness_score=85,
        )
        assert result.target == "test_tool"
        assert result.readiness_score == 85
        assert result.findings == []
        assert result.providers_used == []

    def test_scan_result_with_findings(self):
        finding = Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="Test",
            description="Test",
            provider="test",
        )
        result = ScanResult(
            target="test_tool",
            findings=[finding],
            readiness_score=85,
            providers_used=["heuristic"],
        )
        assert len(result.findings) == 1
        assert result.providers_used == ["heuristic"]

    def test_score_validation(self):
        """Scores must be within 0-100 range."""
        # Valid scores work
        result = ScanResult(target="test", readiness_score=100)
        assert result.readiness_score == 100

        result = ScanResult(target="test", readiness_score=0)
        assert result.readiness_score == 0

        # Invalid scores raise ValidationError
        with pytest.raises(ValidationError):
            ScanResult(target="test", readiness_score=150)

        with pytest.raises(ValidationError):
            ScanResult(target="test", readiness_score=-10)

    def test_has_critical_findings(self):
        critical = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.CRITICAL,
            title="Critical",
            description="Critical issue",
            provider="test",
        )
        result = ScanResult(target="test", findings=[critical], readiness_score=50)
        assert result.has_critical_findings is True

        non_critical = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.HIGH,
            title="High",
            description="High issue",
            provider="test",
        )
        result = ScanResult(target="test", findings=[non_critical], readiness_score=70)
        assert result.has_critical_findings is False

    def test_has_high_findings(self):
        high = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.HIGH,
            title="High",
            description="High issue",
            provider="test",
        )
        result = ScanResult(target="test", findings=[high], readiness_score=70)
        assert result.has_high_findings is True

    def test_finding_counts_by_severity(self):
        findings = [
            Finding(
                category=OperationalRiskCategory.SILENT_FAILURE_PATH,
                severity=Severity.HIGH,
                title="High 1",
                description="Issue",
                provider="test",
            ),
            Finding(
                category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
                severity=Severity.HIGH,
                title="High 2",
                description="Issue",
                provider="test",
            ),
            Finding(
                category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
                severity=Severity.MEDIUM,
                title="Medium",
                description="Issue",
                provider="test",
            ),
        ]
        result = ScanResult(target="test", findings=findings, readiness_score=60)
        counts = result.finding_counts_by_severity
        assert counts["high"] == 2
        assert counts["medium"] == 1
        assert counts["critical"] == 0

    def test_is_production_ready(self):
        # Production ready: score >= 80, no critical, no high
        result = ScanResult(target="test", findings=[], readiness_score=85)
        assert result.is_production_ready is True

        # Not ready: score < 80
        result = ScanResult(target="test", findings=[], readiness_score=75)
        assert result.is_production_ready is False

        # Not ready: has high findings
        high = Finding(
            category=OperationalRiskCategory.SILENT_FAILURE_PATH,
            severity=Severity.HIGH,
            title="High",
            description="Issue",
            provider="test",
        )
        result = ScanResult(target="test", findings=[high], readiness_score=85)
        assert result.is_production_ready is False

    def test_json_serialization(self):
        result = ScanResult(
            target="test_tool",
            readiness_score=85,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
        )
        json_data = result.model_dump(mode="json")
        assert json_data["target"] == "test_tool"
        assert "timestamp" in json_data
