"""
Scan result diff utilities for baseline comparison.

Enables tracking regressions by comparing current scan results
against a baseline, showing only new or fixed findings.
"""

from typing import Any

from mcpreadiness.core.models import Finding, ScanResult, Severity


class ScanDiff:
    """
    Represents the difference between two scan results.

    Tracks new findings, fixed findings, and unchanged findings.
    """

    def __init__(self, baseline: ScanResult, current: ScanResult) -> None:
        """
        Create a diff between baseline and current scan results.

        Args:
            baseline: The baseline (previous) scan result
            current: The current scan result to compare
        """
        self.baseline = baseline
        self.current = current

        # Compute differences
        self.new_findings: list[Finding] = []
        self.fixed_findings: list[Finding] = []
        self.unchanged_findings: list[Finding] = []

        self._compute_diff()

    def _compute_diff(self) -> None:
        """Compute the difference between baseline and current findings."""
        baseline_keys = {self._finding_key(f): f for f in self.baseline.findings}
        current_keys = {self._finding_key(f): f for f in self.current.findings}

        # Find new findings (in current but not in baseline)
        for key, finding in current_keys.items():
            if key not in baseline_keys:
                self.new_findings.append(finding)
            else:
                self.unchanged_findings.append(finding)

        # Find fixed findings (in baseline but not in current)
        for key, finding in baseline_keys.items():
            if key not in current_keys:
                self.fixed_findings.append(finding)

    @staticmethod
    def _finding_key(finding: Finding) -> str:
        """
        Generate a unique key for a finding.

        Uses rule_id, category, title, and location to identify findings.
        """
        parts = [
            finding.rule_id or "",
            finding.category.value,
            finding.title,
            finding.location or "",
        ]
        return "|".join(parts)

    @property
    def has_regressions(self) -> bool:
        """Check if there are new findings (regressions)."""
        return len(self.new_findings) > 0

    @property
    def has_improvements(self) -> bool:
        """Check if there are fixed findings (improvements)."""
        return len(self.fixed_findings) > 0

    @property
    def has_critical_regressions(self) -> bool:
        """Check if any new findings are critical."""
        return any(f.severity == Severity.CRITICAL for f in self.new_findings)

    @property
    def has_high_regressions(self) -> bool:
        """Check if any new findings are high severity."""
        return any(f.severity == Severity.HIGH for f in self.new_findings)

    def get_new_findings_by_severity(self) -> dict[str, int]:
        """Get count of new findings by severity."""
        counts = {s.value: 0 for s in Severity}
        for finding in self.new_findings:
            counts[finding.severity.value] += 1
        return counts

    def get_fixed_findings_by_severity(self) -> dict[str, int]:
        """Get count of fixed findings by severity."""
        counts = {s.value: 0 for s in Severity}
        for finding in self.fixed_findings:
            counts[finding.severity.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Convert diff to a dictionary."""
        return {
            "baseline_target": self.baseline.target,
            "current_target": self.current.target,
            "baseline_score": self.baseline.readiness_score,
            "current_score": self.current.readiness_score,
            "score_delta": self.current.readiness_score - self.baseline.readiness_score,
            "new_findings_count": len(self.new_findings),
            "fixed_findings_count": len(self.fixed_findings),
            "unchanged_findings_count": len(self.unchanged_findings),
            "new_findings": [f.model_dump(mode="json") for f in self.new_findings],
            "fixed_findings": [f.model_dump(mode="json") for f in self.fixed_findings],
            "has_regressions": self.has_regressions,
            "has_improvements": self.has_improvements,
            "new_by_severity": self.get_new_findings_by_severity(),
            "fixed_by_severity": self.get_fixed_findings_by_severity(),
        }

