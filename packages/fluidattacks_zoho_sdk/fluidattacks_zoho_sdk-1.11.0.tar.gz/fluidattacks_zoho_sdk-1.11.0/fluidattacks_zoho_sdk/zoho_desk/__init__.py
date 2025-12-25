from dataclasses import dataclass

from fluidattacks_zoho_sdk._http_client import ClientFactory, HttpJsonClient, TokenManager
from fluidattacks_zoho_sdk.auth import Credentials
from fluidattacks_zoho_sdk.bulk_export import BulkApiFactory
from fluidattacks_zoho_sdk.bulk_export.core import BulkClient
from fluidattacks_zoho_sdk.ids import OrgId

from . import _client
from .core import AgentObj, ContactObj, DeskClient, UserObj


def _bulk_client(creds: Credentials, org_id: OrgId, token_manager: TokenManager) -> BulkClient:
    return BulkApiFactory.new(creds, org_id, token_manager)


def _from_client(
    client: HttpJsonClient,
    creds: Credentials,
    org_id: OrgId,
    token: TokenManager,
) -> DeskClient:
    bulk_client = _bulk_client(creds, org_id, token)

    return DeskClient(
        get_teams=_client.get_teams(client),
        fetch_bulk_agents=_client.fetch_bulk_export_agents(bulk_client),
        fetch_bulk_tickets=_client.fetch_bulk_export_tickets(bulk_client),
        fetch_bulk_contacts=_client.fetch_bulk_contacts(bulk_client),
    )


@dataclass(frozen=True)
class DeskClientFactory:
    @staticmethod
    def new(creds: Credentials, org_id: OrgId, token_manager: TokenManager) -> DeskClient:
        return _from_client(
            ClientFactory.new(creds, org_id, token_manager),
            creds,
            org_id,
            token_manager,
        )


__all__ = [
    "AgentObj",
    "ContactObj",
    "DeskClient",
    "DeskClientFactory",
    "UserObj",
]
