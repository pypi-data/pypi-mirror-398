"""Tests for report generators."""

import json
from datetime import datetime

import pytest

from mcpreadiness.core.models import (
    Finding,
    OperationalRiskCategory,
    ScanResult,
    Severity,
)
from mcpreadiness.reports.json_report import render_json, render_json_summary
from mcpreadiness.reports.markdown_report import render_markdown, render_pr_comment
from mcpreadiness.reports.sarif import render_sarif


@pytest.fixture
def sample_result():
    """Create a sample scan result for testing."""
    findings = [
        Finding(
            category=OperationalRiskCategory.MISSING_TIMEOUT_GUARD,
            severity=Severity.HIGH,
            title="No timeout configured",
            description="Tool lacks timeout configuration",
            location="tool.test_tool",
            provider="heuristic",
            rule_id="HEUR-001",
            remediation="Add timeout configuration",
        ),
        Finding(
            category=OperationalRiskCategory.MISSING_ERROR_SCHEMA,
            severity=Severity.MEDIUM,
            title="No error schema",
            description="Tool lacks error schema",
            provider="heuristic",
            rule_id="HEUR-008",
        ),
    ]
    return ScanResult(
        target="test_tool.json",
        findings=findings,
        readiness_score=75,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        providers_used=["heuristic"],
        scan_duration_ms=50,
    )


@pytest.fixture
def empty_result():
    """Create an empty scan result."""
    return ScanResult(
        target="good_tool.json",
        findings=[],
        readiness_score=100,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        providers_used=["heuristic"],
    )


class TestJsonReport:
    """Tests for JSON report generator."""

    def test_render_json_valid(self, sample_result):
        output = render_json(sample_result)
        data = json.loads(output)
        assert data["target"] == "test_tool.json"
        assert data["readiness_score"] == 75
        assert len(data["findings"]) == 2

    def test_render_json_compact(self, sample_result):
        output = render_json(sample_result, indent=None)
        assert "\n" not in output

    def test_render_json_indented(self, sample_result):
        output = render_json(sample_result, indent=2)
        assert "\n" in output

    def test_render_json_summary(self, sample_result):
        output = render_json_summary(sample_result)
        data = json.loads(output)
        assert data["readiness_score"] == 75
        assert data["findings_count"] == 2
        assert data["has_high"] is True

    def test_render_json_empty_result(self, empty_result):
        output = render_json(empty_result)
        data = json.loads(output)
        assert data["findings"] == []
        assert data["readiness_score"] == 100


class TestMarkdownReport:
    """Tests for Markdown report generator."""

    def test_render_markdown_contains_header(self, sample_result):
        output = render_markdown(sample_result)
        assert "# MCP Readiness Scan Report" in output

    def test_render_markdown_contains_target(self, sample_result):
        output = render_markdown(sample_result)
        assert "test_tool.json" in output

    def test_render_markdown_contains_score(self, sample_result):
        output = render_markdown(sample_result)
        assert "75/100" in output

    def test_render_markdown_contains_findings(self, sample_result):
        output = render_markdown(sample_result)
        assert "No timeout configured" in output
        assert "No error schema" in output

    def test_render_markdown_empty_result(self, empty_result):
        output = render_markdown(empty_result)
        assert "No issues found" in output

    def test_render_markdown_severity_sections(self, sample_result):
        output = render_markdown(sample_result)
        assert "High" in output
        assert "Medium" in output

    def test_render_pr_comment_passed(self, empty_result):
        output = render_pr_comment(empty_result)
        assert "✅" in output
        assert "Passed" in output

    def test_render_pr_comment_failed(self, sample_result):
        output = render_pr_comment(sample_result)
        assert "❌" in output
        assert "Failed" in output


class TestSarifReport:
    """Tests for SARIF report generator."""

    def test_render_sarif_valid_json(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        assert data["version"] == "2.1.0"
        assert "$schema" in data

    def test_render_sarif_has_runs(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        assert len(data["runs"]) == 1

    def test_render_sarif_has_tool_info(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        driver = data["runs"][0]["tool"]["driver"]
        assert driver["name"] == "mcp-readiness-scanner"
        assert "rules" in driver

    def test_render_sarif_has_results(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        results = data["runs"][0]["results"]
        assert len(results) == 2

    def test_render_sarif_result_has_rule_id(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        result = data["runs"][0]["results"][0]
        assert result["ruleId"] == "missing_timeout_guard"

    def test_render_sarif_result_has_level(self, sample_result):
        output = render_sarif(sample_result)
        data = json.loads(output)
        result = data["runs"][0]["results"][0]
        assert result["level"] == "error"  # HIGH maps to error

    def test_render_sarif_empty_result(self, empty_result):
        output = render_sarif(empty_result)
        data = json.loads(output)
        results = data["runs"][0]["results"]
        assert len(results) == 0
