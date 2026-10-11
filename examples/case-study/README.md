# Case study: a document update broke retrieval

This fixture uses synthetic maintenance text only. The candidate document removes the green-valve inspection step. The candidate retrieval run then returns an unrelated chunk for the inspection query.

Run from the repository root:

```bash
uv run --locked ragdiff \
  --dataset examples/case-study/dataset.json \
  --baseline examples/case-study/baseline.json \
  --candidate examples/case-study/candidate.json \
  --output /tmp/ragdiff-case-study-report.json \
  --k 10
```

The command exits with `1` because the deployment policy blocks one regression. The report measures:

- `q-blue-torque`: unchanged, Recall@10 remains 1.0.
- `q-green-inspection`: regression, Recall@10 changes from 1.0 to 0.0.
- plausible cause: `chunk-green-valve` is the changed chunk associated with the regressed query.

The provenance file records this as a plausible cause, not a proof of causality.
