from __future__ import annotations

from dataclasses import dataclass

from fluidattacks_zoho_sdk._http_client import ClientFactory, HttpJsonClient, TokenManager
from fluidattacks_zoho_sdk.auth import Credentials
from fluidattacks_zoho_sdk.ids import OrgId

from . import _client
from .core import BulkClient, BulkEndpoint, FileName, ModuleName


def _from_client(client: HttpJsonClient) -> BulkClient:
    return BulkClient(
        lambda m, i: _client.create_bulk_export(client, m, i),
        lambda obj: _client.get_status_bulk_export(client, obj),
        lambda b, f: _client.download_bulk(client, b, f),
        lambda m, e, f: _client.fetch_bulk(client, m, e, f),
    )


@dataclass(frozen=True)
class BulkApiFactory:
    @staticmethod
    def new(creds: Credentials, org_id: OrgId, token: TokenManager) -> BulkClient:
        return _from_client(ClientFactory.new(creds, org_id, token))


__all__ = ["BulkApiFactory", "BulkClient", "BulkEndpoint", "FileName", "ModuleName"]
