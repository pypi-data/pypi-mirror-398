from dataclasses import dataclass

from fluidattacks_etl_utils.natural import Natural


@dataclass(frozen=True)
class OrgId:
    org_id: Natural


@dataclass(frozen=True)
class UserId:
    user_id: Natural


@dataclass(frozen=True)
class AccountId:
    account_id: Natural


@dataclass(frozen=True)
class CrmId:
    crm_id: Natural


@dataclass(frozen=True)
class DeparmentId:
    id_deparment: Natural


@dataclass(frozen=True)
class TeamId:
    id_team: Natural


@dataclass(frozen=True)
class AgentId:
    agent_id: Natural


@dataclass(frozen=True)
class ProfileId:
    id_profile: Natural


@dataclass(frozen=True)
class RoleId:
    id_role: Natural


@dataclass(frozen=True)
class ProductId:
    id_product: Natural


@dataclass(frozen=True)
class TicketId:
    id_ticket: Natural


@dataclass(frozen=True)
class ContactId:
    id_contact: Natural
