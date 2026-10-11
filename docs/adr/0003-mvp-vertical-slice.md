# ADR 0003: Build one complete MVP vertical slice

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

The portfolio objective requires evidence of frontend, API, authentication, multi-tenancy, PostgreSQL/pgvector, ingestion, AWS, observability, deployment blocking, and GitHub integration. Building only a local evaluation library would not prove the intended engineering ability.

## Decision

The MVP will implement one narrow path across every required layer: authenticate a tenant, ingest one supported document format, create revisioned chunks and embeddings, compare baseline and candidate retrieval runs, persist a report, display it in the frontend, emit telemetry, and publish/block a GitHub pull request result.

Each capability may support only one provider or topology initially. Additional providers, formats, scaling modes, and advanced UX are deferred until the vertical slice is measured.

## Alternatives considered

- **CLI-only MVP:** rejected because it omits the deployment and operational abilities the portfolio must demonstrate.
- **Implement every integration broadly:** rejected because breadth would reduce reliability and evidence quality.

## Consequences

- Every layer must have a minimal contract and an end-to-end test path.
- The MVP is portfolio-grade but not a claim of enterprise production maturity.
- Scope decisions must preserve the complete workflow over optional feature breadth.
- Benchmark and case-study work is part of delivery, not a later marketing task.
