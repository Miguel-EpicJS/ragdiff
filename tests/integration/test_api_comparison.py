import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from psycopg import connect

from ragdiff.api.app import ComparisonRequest, create_app
from ragdiff.application.auth import AuthenticatedPrincipal, BearerAuthenticator, TokenRecord
from ragdiff.domain.ids import Identifier

_DATABASE_URL = os.environ.get("RAGDIFF_TEST_DATABASE_URL")


@pytest.mark.skipif(_DATABASE_URL is None, reason="RAGDIFF_TEST_DATABASE_URL is not configured")
def test_comparison_api_persists_and_retrieves_blocked_report() -> None:
    assert _DATABASE_URL is not None
    with connect(_DATABASE_URL) as connection:
        for migration in sorted(Path("migrations").glob("*.sql")):
            connection.execute(migration.read_text())
        connection.execute("INSERT INTO tenants (tenant_id) VALUES ('tenant-a')")
        connection.execute(
            """
            INSERT INTO evaluation_runs
                (tenant_id, run_id, dataset_id, dataset_version, pipeline_version)
            VALUES
                ('tenant-a', 'run-base', 'dataset-1', 'v1', 'old'),
                ('tenant-a', 'run-candidate', 'dataset-1', 'v1', 'new')
            """
        )
        connection.execute(
            """
            INSERT INTO evaluation_queries (tenant_id, run_id, query_id, relevant_ids)
            VALUES
                ('tenant-a', 'run-base', 'q-1', '["chunk-a"]'),
                ('tenant-a', 'run-candidate', 'q-1', '["chunk-a"]')
            """
        )
        connection.execute(
            """
            INSERT INTO retrieved_items (tenant_id, run_id, query_id, item_id, rank)
            VALUES
                ('tenant-a', 'run-base', 'q-1', 'chunk-a', 1),
                ('tenant-a', 'run-candidate', 'q-1', 'other', 1)
            """
        )
        principal = AuthenticatedPrincipal("user-1", Identifier("tenant-a"), frozenset())
        app = create_app(
            authenticator=BearerAuthenticator(
                {"secret-token": TokenRecord(principal, datetime.now(UTC) + timedelta(minutes=5))}
            ),
            connection=connection,
        )
        post_endpoint = next(
            route.endpoint
            for route in app.routes
            if isinstance(route, APIRoute) and route.path == "/v1/comparisons"
        )
        get_endpoint = next(
            route.endpoint
            for route in app.routes
            if isinstance(route, APIRoute) and route.path == "/v1/comparisons/{report_id}"
        )
        request = ComparisonRequest(
            report_id="report-1",
            dataset={
                "schema_version": 1,
                "dataset_id": "dataset-1",
                "version": "v1",
                "queries": [{"query_id": "q-1", "relevant_ids": ["chunk-a"]}],
            },
            baseline={
                "schema_version": 1,
                "run_id": "run-base",
                "dataset_id": "dataset-1",
                "dataset_version": "v1",
                "pipeline_version": "old",
                "queries": [{"query_id": "q-1", "items": [{"item_id": "chunk-a", "rank": 1}]}],
            },
            candidate={
                "schema_version": 1,
                "run_id": "run-candidate",
                "dataset_id": "dataset-1",
                "dataset_version": "v1",
                "pipeline_version": "new",
                "queries": [{"query_id": "q-1", "items": [{"item_id": "other", "rank": 1}]}],
            },
            k=1,
        )

        created = post_endpoint(request, "Bearer secret-token")
        retrieved = get_endpoint("report-1", "Bearer secret-token")

        assert created.deployment_status == "blocked"
        assert created.result["comparison"]["summary"]["regressions"] == 1
        assert retrieved.result == created.result
