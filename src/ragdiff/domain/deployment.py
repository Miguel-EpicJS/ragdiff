"""Fail-closed deployment decisions for comparison reports."""

from dataclasses import dataclass
from typing import Literal

from ragdiff.domain.report import ComparisonResult

DeploymentStatus = Literal["allowed", "blocked"]


@dataclass(frozen=True, slots=True)
class DeploymentDecision:
    """Deterministic decision and evidence used by a deployment gate."""

    status: DeploymentStatus
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.status == "allowed"


@dataclass(frozen=True, slots=True)
class DeploymentPolicy:
    """Block incomplete or materially worse reports by default."""

    max_regressions: int = 0
    max_recall_drop: float = 0.0

    def __post_init__(self) -> None:
        if self.max_regressions < 0:
            raise ValueError("max_regressions must be non-negative")
        if self.max_recall_drop < 0:
            raise ValueError("max_recall_drop must be non-negative")

    def evaluate(self, report: ComparisonResult) -> DeploymentDecision:
        """Return an allow/block decision without side effects."""
        summary = report.summary
        reasons: list[str] = []
        if summary["incomplete"]:
            reasons.append(f"incomplete_queries={summary['incomplete']}")
        if summary["regressions"] > self.max_regressions:
            reasons.append(
                f"regressions={summary['regressions']} exceeds max={self.max_regressions}"
            )
        for query in report.queries:
            if query.recall_delta is not None and query.recall_delta < -self.max_recall_drop:
                reasons.append(f"query={query.query_id} recall_delta={query.recall_delta:.6f}")
        return DeploymentDecision("blocked" if reasons else "allowed", tuple(reasons))
