from dataclasses import dataclass

from fluidattacks_zoho_sdk.auth import Credentials
from fluidattacks_zoho_sdk.ids import OrgId

from ._client import Client
from ._core import HttpJsonClient, RelativeEndpoint, TokenManager


@dataclass(frozen=True)
class ClientFactory:
    @staticmethod
    def new(creds: Credentials, org_id: OrgId, token_manager: TokenManager) -> HttpJsonClient:
        return Client.new(creds, org_id, token_manager).client


__all__ = ["Client", "HttpJsonClient", "RelativeEndpoint", "TokenManager"]
