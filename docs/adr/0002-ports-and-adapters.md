# ADR 0002: Use ports and adapters at infrastructure boundaries

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

RAGDiff depends on PostgreSQL/pgvector, an embedding provider, authentication, GitHub, OpenTelemetry, and AWS. These integrations change independently and should not determine the behavior of metric calculation, provenance, or deployment policy.

## Decision

Domain logic depends only on explicit application-owned interfaces. Adapters implement persistence, vector search, embeddings, authentication, GitHub, telemetry, and external provider behavior. FastAPI routes orchestrate application use cases and do not contain business rules.

## Alternatives considered

- **Direct SDK usage throughout the codebase:** rejected because it couples domain behavior to vendors and complicates deterministic tests.
- **Large generic abstraction framework:** rejected because it adds indirection without a current product need.

## Consequences

- The comparison engine can be tested without network services.
- Adapter contract tests are required for external integrations.
- Provider-specific metadata must be preserved at the boundary without leaking vendor types into the domain.
- Interfaces should be introduced only where a real integration or substitution exists.
