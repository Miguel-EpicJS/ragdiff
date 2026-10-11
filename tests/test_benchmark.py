from pathlib import Path

from ragdiff.benchmark import run_benchmark

FIXTURES = Path("examples/case-study")


def test_benchmark_reports_reproducible_metrics_and_runtime(tmp_path: Path) -> None:
    results = [
        run_benchmark(
            FIXTURES / "dataset.json",
            FIXTURES / "baseline.json",
            FIXTURES / "candidate.json",
            10,
            0.0123,
        )
        for _ in range(2)
    ]

    assert results[0]["benchmark"] == results[1]["benchmark"]
    assert results[0]["metrics"]["regressions"] == 1
    assert results[0]["metrics"]["unchanged"] == 1
    assert results[0]["metrics"]["estimated_cost_usd"] == 0.0123
    assert results[0]["metrics"]["latency_ms"] >= 0
    assert results[1]["metrics"]["latency_ms"] >= 0
    assert results[0]["deployment_status"] == "blocked"
