# ADR 0001: Start with a modular monolith

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

RAGDiff must demonstrate an end-to-end workflow across ingestion, retrieval evaluation, provenance analysis, API, frontend, GitHub automation, and deployment. The project is initially maintained by a small team and needs fast feedback, simple local execution, and strong integration tests.

## Decision

Implement the MVP as a modular monolith with explicit internal boundaries. Keep domain and application logic separate from API, persistence, vector search, authentication, GitHub, telemetry, and infrastructure adapters.

## Alternatives considered

- **Microservices:** rejected for the MVP because operational complexity would obscure the product evidence and slow integration.
- **Unstructured single module:** rejected because it would make boundaries, testing, and future extraction unclear.

## Consequences

- One deployable service is simpler to run and observe.
- Modules must not bypass application contracts or access infrastructure directly.
- A later service split remains possible if measured scaling or ownership pressure justifies it.
- Integration tests must cover the complete workflow inside the monolith.
