import pytest

from ragdiff.application.auth import AuthenticatedPrincipal
from ragdiff.application.authorization import AuthorizationError, require_tenant_access
from ragdiff.domain.ids import Identifier


def test_authorization_allows_server_derived_tenant() -> None:
    principal = AuthenticatedPrincipal("user-1", Identifier("tenant-a"), frozenset())

    require_tenant_access(principal, Identifier("tenant-a"))


def test_authorization_rejects_cross_tenant_access() -> None:
    principal = AuthenticatedPrincipal("user-1", Identifier("tenant-a"), frozenset())

    with pytest.raises(AuthorizationError):
        require_tenant_access(principal, Identifier("tenant-b"))
