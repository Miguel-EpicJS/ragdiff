"""Command-line evaluation entry point for local and CI regression gates."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ragdiff.domain.comparison import compare_runs
from ragdiff.domain.dataset import EvaluationDataset
from ragdiff.domain.deployment import DeploymentPolicy
from ragdiff.domain.report import ComparisonResult
from ragdiff.domain.retrieval import RetrievalRun


def main(argv: Sequence[str] | None = None) -> int:
    """Compare two retrieval run files and return a deployment-gate exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    dataset = EvaluationDataset.from_dict(_load_json(args.dataset))
    baseline = RetrievalRun.from_dict(_load_json(args.baseline))
    candidate = RetrievalRun.from_dict(_load_json(args.candidate))
    report = ComparisonResult(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        k=args.k,
        queries=compare_runs(dataset, baseline, candidate, args.k),
    )
    decision = DeploymentPolicy().evaluate(report)
    output = {
        "comparison": report.to_dict(),
        "deployment_status": decision.status,
        "deployment_reasons": list(decision.reasons),
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"deployment_status": decision.status, "summary": report.summary}))
    return 0 if decision.allowed else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k", type=int, required=True)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
