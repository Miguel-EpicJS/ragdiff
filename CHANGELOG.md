# Changelog

## 0.1.0 — MVP

First publicly shareable RAGDiff portfolio release.

### Included

- typed retrieval comparison and deployment-gate domain contracts;
- document provenance, chunking, embeddings, and PostgreSQL/pgvector adapters;
- bearer authentication, tenant-scoped API routes, FastAPI service, and browser report UI;
- OpenTelemetry request tracing with tenant-safe metadata and no token/body capture;
- Docker API and evaluation-worker runtime;
- Terraform topology for AWS ALB, ECS Fargate, private PostgreSQL, Secrets Manager, and CloudWatch;
- pull-request evaluation, JSON artifact upload, and idempotent PR summaries;
- synthetic regression case study and reproducible quality/latency/cost benchmark.

### Known limitations

- AWS provisioning is not executed by default and requires account/cost approval.
- The container vulnerability scan reports unresolved upstream HIGH/CRITICAL findings; production use requires remediation or an explicit exception.
- Causal attribution is a plausible-cause diagnostic, not proof of causality.
- The hosted service, production secret rotation, and broader benchmark suite remain future work.
