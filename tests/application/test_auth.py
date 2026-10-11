from datetime import UTC, datetime, timedelta

import pytest

from ragdiff.application.auth import (
    AuthenticatedPrincipal,
    AuthenticationError,
    BearerAuthenticator,
    TokenRecord,
)
from ragdiff.domain.ids import Identifier


def authenticator(expires_at: datetime) -> BearerAuthenticator:
    principal = AuthenticatedPrincipal("user-1", Identifier("tenant-a"), frozenset({"read"}))
    return BearerAuthenticator({"secret-token": TokenRecord(principal, expires_at)})


def test_authentication_returns_server_derived_tenant_context() -> None:
    principal = authenticator(datetime.now(UTC) + timedelta(minutes=5)).authenticate(
        "Bearer secret-token"
    )

    assert principal.subject == "user-1"
    assert principal.tenant_id == Identifier("tenant-a")


def test_authentication_rejects_missing_invalid_and_expired_tokens() -> None:
    auth = authenticator(datetime.now(UTC) + timedelta(minutes=5))
    for header in (None, "Basic secret-token", "Bearer wrong-token"):
        with pytest.raises(AuthenticationError):
            auth.authenticate(header)

    expired = authenticator(datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(AuthenticationError, match="expired"):
        expired.authenticate("Bearer secret-token")
