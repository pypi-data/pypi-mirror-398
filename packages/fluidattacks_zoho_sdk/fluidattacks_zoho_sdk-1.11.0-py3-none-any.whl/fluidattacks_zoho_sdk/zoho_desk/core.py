from __future__ import annotations

from dataclasses import dataclass

from fa_purity import Cmd, FrozenList, Maybe, ResultE
from fa_purity.date_time import DatetimeUTC

from fluidattacks_zoho_sdk.ids import (
    ContactId,
    DeparmentId,
    TeamId,
    TicketId,
    UserId,
)


@dataclass(frozen=True)
class OptionalId:
    id: str


@dataclass(frozen=True)
class UserObj:
    id_user: UserId
    first_name: Maybe[str]
    last_name: str


@dataclass(frozen=True)
class AgentObj:
    user: UserObj
    is_confirmed: bool
    email: str
    profile: str
    role: str
    status: str


@dataclass(frozen=True)
class ContactDates:
    created_time: Maybe[DatetimeUTC]
    modified_time: Maybe[DatetimeUTC]


@dataclass(frozen=True)
class ContactInfo:
    email: Maybe[str]
    facebook: Maybe[str]
    phone: Maybe[str]
    mobile: Maybe[str]
    secondary_email: Maybe[str]


@dataclass(frozen=True)
class ContactAddres:
    city: Maybe[str]
    country: Maybe[str]
    street: Maybe[str]


@dataclass(frozen=True)
class ContactObj:
    contact_id: ContactId
    user: UserObj
    contact_info: ContactInfo
    contact_addres: ContactAddres
    contact_dates: ContactDates
    account_id: Maybe[OptionalId]
    contact_owner: UserId
    crm_id: Maybe[OptionalId]
    description: Maybe[str]
    state: Maybe[str]
    title: Maybe[str]
    type_contact: Maybe[str]
    zip_contact: Maybe[str]


@dataclass(frozen=True)
class TeamObj:
    id_deparment: DeparmentId
    id_team: TeamId
    description: str
    name: str


@dataclass(frozen=True)
class DerivedAgent:
    id_user: UserId


@dataclass(frozen=True)
class TicketDates:
    modified_time: Maybe[DatetimeUTC]
    created_time: Maybe[DatetimeUTC]
    closed_time: Maybe[DatetimeUTC]
    customer_response_time: Maybe[DatetimeUTC]


@dataclass(frozen=True)
class TicketProperties:
    id_ticket: TicketId
    suject: Maybe[str]
    channel: Maybe[str]
    status: Maybe[str]
    category: Maybe[str]
    is_escalated: bool
    priority: Maybe[str]
    resolution: Maybe[str]
    classification: Maybe[str]
    description: Maybe[str]


@dataclass(frozen=True)
class TicketObj:
    account_id: Maybe[OptionalId]
    deparment_id: Maybe[OptionalId]
    team_id: Maybe[OptionalId]
    product_id: Maybe[OptionalId]
    ticket_date: TicketDates
    ticket_properties: TicketProperties
    contact_id: ContactId
    email: Maybe[str]
    phone: Maybe[str]
    onhold_time: Maybe[str]
    stakeholder: Maybe[str]


@dataclass(frozen=True)
class DeskClient:
    get_teams: Cmd[ResultE[FrozenList[tuple[TeamObj, FrozenList[DerivedAgent]]]]]
    # bulk export
    fetch_bulk_agents: Cmd[ResultE[FrozenList[AgentObj]]]
    fetch_bulk_tickets: Cmd[ResultE[FrozenList[TicketObj]]]
    fetch_bulk_contacts: Cmd[ResultE[FrozenList[ContactObj]]]
