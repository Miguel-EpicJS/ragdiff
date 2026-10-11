"""Deterministic quality benchmark with explicit latency and cost metadata."""

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

from ragdiff import __version__
from ragdiff.domain.comparison import compare_runs
from ragdiff.domain.dataset import EvaluationDataset
from ragdiff.domain.deployment import DeploymentPolicy
from ragdiff.domain.report import ComparisonResult
from ragdiff.domain.retrieval import RetrievalRun


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--estimated-cost-usd", type=float, default=0.0)
    args = parser.parse_args()
    result = run_benchmark(
        args.dataset,
        args.baseline,
        args.candidate,
        args.k,
        args.estimated_cost_usd,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], sort_keys=True))
    return 0 if result["deployment_status"] == "allowed" else 1


def run_benchmark(
    dataset_path: Path,
    baseline_path: Path,
    candidate_path: Path,
    k: int,
    estimated_cost_usd: float,
) -> dict[str, Any]:
    dataset = EvaluationDataset.from_dict(_load_json(dataset_path))
    baseline = RetrievalRun.from_dict(_load_json(baseline_path))
    candidate = RetrievalRun.from_dict(_load_json(candidate_path))
    started = time.perf_counter()
    report = ComparisonResult(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        k=k,
        queries=compare_runs(dataset, baseline, candidate, k),
    )
    latency_ms = (time.perf_counter() - started) * 1000
    decision = DeploymentPolicy().evaluate(report)
    return {
        "benchmark": {
            "dataset_id": str(dataset.dataset_id),
            "dataset_version": dataset.version,
            "baseline_pipeline_version": baseline.pipeline_version,
            "candidate_pipeline_version": candidate.pipeline_version,
            "k": k,
            "ragdiff_version": __version__,
            "python_version": platform.python_version(),
        },
        "metrics": {
            **report.summary,
            "latency_ms": round(latency_ms, 3),
            "estimated_cost_usd": round(estimated_cost_usd, 8),
        },
        "deployment_status": decision.status,
        "deployment_reasons": list(decision.reasons),
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
