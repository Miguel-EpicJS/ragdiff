"""Tenant authorization policies for application use cases."""

from ragdiff.application.auth import AuthenticatedPrincipal
from ragdiff.domain.ids import TenantId


class AuthorizationError(PermissionError):
    """Raised when an authenticated principal lacks tenant access."""


def require_tenant_access(
    principal: AuthenticatedPrincipal,
    requested_tenant_id: TenantId,
) -> None:
    """Fail closed unless the server-derived tenant matches the resource tenant."""
    if principal.tenant_id != requested_tenant_id:
        raise AuthorizationError("principal is not authorized for this tenant")
