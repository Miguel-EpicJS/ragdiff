import json
from pathlib import Path

from ragdiff.cli import main

FIXTURES = Path("examples/evaluation")


def test_cli_writes_allowed_report(tmp_path: Path) -> None:
    output = tmp_path / "report.json"

    exit_code = main(
        [
            "--dataset",
            str(FIXTURES / "dataset.json"),
            "--baseline",
            str(FIXTURES / "baseline.json"),
            "--candidate",
            str(FIXTURES / "candidate.json"),
            "--output",
            str(output),
            "--k",
            "10",
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text())["deployment_status"] == "allowed"


def test_cli_returns_blocked_exit_code(tmp_path: Path) -> None:
    candidate = json.loads((FIXTURES / "candidate.json").read_text())
    candidate["queries"][1]["items"] = []
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate))
    output = tmp_path / "report.json"

    exit_code = main(
        [
            "--dataset",
            str(FIXTURES / "dataset.json"),
            "--baseline",
            str(FIXTURES / "baseline.json"),
            "--candidate",
            str(candidate_path),
            "--output",
            str(output),
            "--k",
            "10",
        ]
    )

    assert exit_code == 1
    assert json.loads(output.read_text())["deployment_status"] == "blocked"
