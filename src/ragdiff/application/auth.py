"""Authentication boundary and tenant-safe request context."""

import hashlib
import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from ragdiff.domain.ids import TenantId


class AuthenticationError(ValueError):
    """Raised when a bearer credential is absent, invalid, or expired."""


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Identity and tenant context established by authentication."""

    subject: str
    tenant_id: TenantId
    scopes: frozenset[str]


@dataclass(frozen=True, slots=True)
class TokenRecord:
    """Runtime token metadata supplied by a secret-backed provider."""

    principal: AuthenticatedPrincipal
    expires_at: datetime


class BearerAuthenticator:
    """Authenticate bearer tokens without storing raw token values."""

    def __init__(self, token_records: Mapping[str, TokenRecord]) -> None:
        self._records_by_hash = {
            _hash_token(token): record for token, record in token_records.items()
        }

    def authenticate(self, authorization_header: str | None) -> AuthenticatedPrincipal:
        if authorization_header is None:
            raise AuthenticationError("authorization is required")
        scheme, separator, token = authorization_header.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token:
            raise AuthenticationError("authorization must use a bearer token")

        token_hash = _hash_token(token)
        record = next(
            (
                candidate
                for stored_hash, candidate in self._records_by_hash.items()
                if hmac.compare_digest(stored_hash, token_hash)
            ),
            None,
        )
        if record is None:
            raise AuthenticationError("invalid bearer token")
        if record.expires_at.tzinfo is None:
            raise ValueError("token expiry must include timezone information")
        if record.expires_at <= datetime.now(UTC):
            raise AuthenticationError("bearer token has expired")
        return record.principal


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
