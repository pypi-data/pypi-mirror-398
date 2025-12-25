import inspect
import logging

from fa_purity import Cmd, FrozenList, ResultE, cast_exception
from fa_purity.json import Primitive, UnfoldedFactory
from fluidattacks_etl_utils.bug import Bug

from fluidattacks_zoho_sdk._decoders import assert_single
from fluidattacks_zoho_sdk._http_client import HttpJsonClient, RelativeEndpoint
from fluidattacks_zoho_sdk.bulk_export import BulkClient, BulkEndpoint, FileName, ModuleName

from ._decode import decode_agents, decode_contacts, decode_teams, decode_tickets
from .core import AgentObj, ContactObj, DerivedAgent, TeamObj, TicketObj

LOG = logging.getLogger(__name__)


def fetch_bulk_contacts(
    client: BulkClient,
) -> Cmd[ResultE[FrozenList[ContactObj]]]:
    endpoint_bulk = BulkEndpoint("bulkExport")
    module_name = ModuleName("contacts")
    file_name = FileName("Contacts__1.csv")

    return client.fetch_bulk(module_name, endpoint_bulk, file_name).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(
                    Bug.new("_generate_bulk_export_contacts", inspect.currentframe(), e, ()),
                ),
            ).bind(decode_contacts)
        ),
    )


def fetch_bulk_export_tickets(
    client: BulkClient,
) -> Cmd[ResultE[FrozenList[TicketObj]]]:
    endpoint_bulk = BulkEndpoint("bulkExport")
    module_name = ModuleName("tickets")
    file_name = FileName("Cases__1.csv")

    return client.fetch_bulk(module_name, endpoint_bulk, file_name).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(
                    Bug.new("_generate_bulk_export_tickets", inspect.currentframe(), e, ()),
                ),
            ).bind(decode_tickets)
        ),
    )


def get_teams(
    client: HttpJsonClient,
) -> Cmd[ResultE[FrozenList[tuple[TeamObj, FrozenList[DerivedAgent]]]]]:
    endpoint = RelativeEndpoint.new("teams")
    params: dict[str, Primitive] = {}
    return client.get(
        endpoint,
        UnfoldedFactory.from_dict(params),
    ).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(Bug.new("_get_teams", inspect.currentframe(), e, ())),
            )
            .bind(assert_single)
            .bind(lambda teams: decode_teams(teams))
        ),
    )


def fetch_bulk_export_agents(
    client: BulkClient,
) -> Cmd[ResultE[FrozenList[AgentObj]]]:
    endpoint_bulk = BulkEndpoint("bulkExport")
    module_name = ModuleName("agents")
    file_name = FileName("Agents__1.csv")

    return client.fetch_bulk(module_name, endpoint_bulk, file_name).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(
                    Bug.new("_generate_bulk_export_agent", inspect.currentframe(), e, ()),
                ),
            ).bind(decode_agents)
        ),
    )
