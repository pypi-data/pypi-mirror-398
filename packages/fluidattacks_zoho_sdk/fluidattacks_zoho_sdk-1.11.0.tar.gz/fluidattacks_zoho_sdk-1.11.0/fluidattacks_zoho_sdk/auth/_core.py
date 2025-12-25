import hashlib
from dataclasses import (
    dataclass,
)

ACCOUNTS_URL = "https://accounts.zoho.com"  # for US region


@dataclass(frozen=True)
class Token:
    raw_token: str

    def __repr__(self) -> str:
        return "[masked]"


@dataclass(frozen=True)
class RefreshToken:
    raw_token: str

    def __repr__(self) -> str:
        signature = hashlib.sha256(self.raw_token.encode("utf-8")).hexdigest()[:128]
        return f"[masked] signature={signature}"


@dataclass(frozen=True)
class Credentials:
    client_id: str
    client_secret: str
    refresh_token: str
    scopes: frozenset[str]

    def __repr__(self) -> str:
        return f"Creds(client_id={self.client_id}, scopes={self.scopes})"


__all__ = [
    "Token",
]
