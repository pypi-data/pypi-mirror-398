from fa_purity import (
    FrozenList,
    Maybe,
    PureIterFactory,
    Result,
    ResultE,
    ResultTransform,
    Unsafe,
)
from fa_purity.json import JsonObj, JsonPrimitiveUnfolder, JsonUnfolder, Unfolder
from fluidattacks_etl_utils import smash
from fluidattacks_etl_utils.decode import DecodeUtils
from fluidattacks_etl_utils.natural import Natural, NaturalOperations

from fluidattacks_zoho_sdk._decoders import (
    decode_contact_id,
    decode_contact_id_bulk,
    decode_department_id,
    decode_department_id_team,
    decode_id_team,
    decode_list_objs,
    decode_maybe_str,
    decode_opt_date_to_utc,
    decode_optional_id,
    decode_ticket_id,
    decode_user_id,
    decode_user_id_bulk,
)
from fluidattacks_zoho_sdk.ids import AccountId, ProductId, UserId
from fluidattacks_zoho_sdk.zoho_desk.core import (
    AgentObj,
    ContactAddres,
    ContactDates,
    ContactInfo,
    ContactObj,
    DerivedAgent,
    TeamObj,
    TicketDates,
    TicketObj,
    TicketProperties,
    UserObj,
)


def parse_bool(v: str) -> bool:
    lv = v.lower().strip()
    if lv == "true":
        return True
    if lv == "false":
        return False
    msg = f"Invalid boolean string: {v}"
    raise ValueError(msg)


def decode_user(raw: JsonObj) -> ResultE[UserObj]:
    return smash.smash_result_3(
        decode_user_id(raw),
        JsonUnfolder.optional(raw, "firstName", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.require(raw, "lastName", DecodeUtils.to_str),
    ).map(lambda obj: UserObj(*obj))


def decode_user_bulk(raw: JsonObj) -> ResultE[UserObj]:
    return smash.smash_result_3(
        decode_user_id_bulk(raw),
        JsonUnfolder.optional(raw, "First Name", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.require(raw, "Last Name", DecodeUtils.to_str),
    ).map(lambda v: UserObj(*v))


def decode_contact_addres(raw: JsonObj) -> ResultE[ContactAddres]:
    return smash.smash_result_3(
        JsonUnfolder.optional(raw, "City", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda x: x),
        ),
        JsonUnfolder.optional(raw, "Country", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda x: x),
        ),
        JsonUnfolder.optional(raw, "Street", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda x: x),
        ),
    ).map(lambda obj: ContactAddres(*obj))


def decode_contact_dates(raw: JsonObj) -> ResultE[ContactDates]:
    return smash.smash_result_2(
        decode_opt_date_to_utc(raw, "Created Time"),
        decode_opt_date_to_utc(raw, "Modified Time"),
    ).map(lambda obj: ContactDates(*obj))


def decode_contact_info(raw: JsonObj) -> ResultE[ContactInfo]:
    return smash.smash_result_5(
        decode_maybe_str(raw, "Email"),
        decode_maybe_str(raw, "Facebook"),
        decode_maybe_str(raw, "Phone"),
        decode_maybe_str(raw, "Mobile"),
        decode_maybe_str(raw, "Secondary Email"),
    ).map(lambda obj: ContactInfo(*obj))


def decode_contact_obj(raw: JsonObj) -> ResultE[ContactObj]:
    first = smash.smash_result_5(
        decode_contact_id_bulk(raw),
        decode_user_bulk(raw),
        decode_contact_info(raw),
        decode_contact_addres(raw),
        decode_contact_dates(raw),
    )

    second = smash.smash_result_5(
        decode_optional_id(raw, "Account ID"),
        JsonUnfolder.require(raw, "Contact Owner", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(lambda j: UserId(j)),
        decode_optional_id(raw, "CRM ID"),
        JsonUnfolder.optional(raw, "Description", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.optional(raw, "State", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
    )

    three = smash.smash_result_3(
        JsonUnfolder.optional(raw, "Title", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.optional(raw, "Type", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
        JsonUnfolder.optional(raw, "Zip", DecodeUtils.to_opt_str).map(
            lambda v: v.bind(lambda j: j),
        ),
    )

    return smash.smash_result_3(first, second, three).map(lambda v: ContactObj(*v[0], *v[1], *v[2]))


def decode_contacts(raws: FrozenList[JsonObj]) -> ResultE[FrozenList[ContactObj]]:
    return decode_list_objs(raws, decode_contact_obj)


def decode_ticket_dates(raw: JsonObj) -> ResultE[TicketDates]:
    return smash.smash_result_4(
        decode_opt_date_to_utc(raw, "Modified Time"),
        decode_opt_date_to_utc(raw, "Created Time"),
        decode_opt_date_to_utc(raw, "Ticket Closed Time"),
        decode_opt_date_to_utc(raw, "Customer Response Time"),
    ).map(lambda v: TicketDates(*v))


def decode_ticket_properties(raw: JsonObj) -> ResultE[TicketProperties]:
    first = smash.smash_result_4(
        decode_ticket_id(raw),
        decode_maybe_str(raw, "Subject"),
        decode_maybe_str(raw, "Channel"),
        decode_maybe_str(raw, "Status"),
    )

    second = smash.smash_result_4(
        decode_maybe_str(raw, "Category"),
        JsonUnfolder.require(raw, "Is Escalated", DecodeUtils.to_str).map(parse_bool),
        decode_maybe_str(raw, "Priority"),
        decode_maybe_str(raw, "Resolution"),
    )

    three = smash.smash_result_2(
        decode_maybe_str(raw, "Classifications"),
        decode_maybe_str(raw, "Description"),
    )
    return smash.smash_result_3(first, second, three).map(
        lambda v: TicketProperties(*v[0], *v[1], *v[2]),
    )


def decode_maybe_account_id(raw: JsonObj) -> ResultE[Maybe[AccountId]]:
    return JsonUnfolder.optional(raw, "Account ID", DecodeUtils.to_opt_str).map(
        lambda v: v.bind(lambda x: x)
        .map(
            lambda j: Natural.from_int(int(j)).alt(Unsafe.raise_exception).to_union(),
        )
        .map(lambda obj: AccountId(obj)),
    )


def decode_maybe_product_id(raw: JsonObj) -> ResultE[Maybe[ProductId]]:
    return JsonUnfolder.optional(raw, "Product ID", DecodeUtils.to_opt_str).map(
        lambda v: v.bind(lambda x: x)
        .map(
            lambda j: Natural.from_int(int(j)).alt(Unsafe.raise_exception).to_union(),
        )
        .map(lambda obj: ProductId(obj)),
    )


def decode_ticket_obj(raw: JsonObj) -> ResultE[TicketObj]:
    first = smash.smash_result_5(
        decode_optional_id(raw, "Account ID"),
        decode_optional_id(raw, "Department"),
        decode_optional_id(raw, "Team ID"),
        decode_optional_id(raw, "Product ID"),
        decode_ticket_dates(raw),
    )

    second = smash.smash_result_4(
        decode_ticket_properties(raw),
        decode_contact_id(raw),
        decode_maybe_str(raw, "Email"),
        decode_maybe_str(raw, "Phone"),
    )

    third = smash.smash_result_2(
        decode_maybe_str(raw, "Ticket On Hold Time"),
        decode_maybe_str(raw, "Stakeholder"),
    )
    return smash.smash_result_3(first, second, third).map(lambda v: TicketObj(*v[0], *v[1], *v[2]))


def decode_tickets(raws: FrozenList[JsonObj]) -> ResultE[FrozenList[TicketObj]]:
    return decode_list_objs(raws, decode_ticket_obj)


def decode_team_obj(raw: JsonObj) -> ResultE[TeamObj]:
    return smash.smash_result_4(
        decode_department_id(raw),
        decode_id_team(raw),
        JsonUnfolder.require(raw, "description", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "name", DecodeUtils.to_str),
    ).map(lambda team: TeamObj(*team))


def decode_derived_agent(
    id_agent: str,
) -> ResultE[DerivedAgent]:
    return Result.success(DerivedAgent(UserId(NaturalOperations.absolute(int(id_agent)))))


def decode_team_obj_with_agents(raw: JsonObj) -> ResultE[tuple[TeamObj, FrozenList[DerivedAgent]]]:
    team_r: ResultE[TeamObj] = smash.smash_result_4(
        decode_department_id_team(raw),
        decode_id_team(raw),
        JsonUnfolder.require(raw, "description", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "name", DecodeUtils.to_str),
    ).map(lambda team: TeamObj(*team))

    derived_agents_json = JsonUnfolder.require(
        raw,
        "derivedAgents",
        lambda v: Unfolder.to_list_of(
            v,
            lambda j: Unfolder.to_primitive(j).bind(lambda j: JsonPrimitiveUnfolder.to_str(j)),
        ),
    )

    list_agents = derived_agents_json.bind(
        lambda agents: ResultTransform.all_ok(
            tuple(PureIterFactory.from_list(agents).map(decode_derived_agent)),
        ),
    )

    return team_r.bind(lambda team: list_agents.map(lambda agents: (team, agents)))


def decode_derived_agents(agents: FrozenList[str]) -> ResultE[FrozenList[DerivedAgent]]:
    if not agents:
        return Result.failure(ValueError("Expected a list wiht elements"))
    return ResultTransform.all_ok(
        PureIterFactory.from_list(agents).map(lambda v: decode_derived_agent(v)).to_list(),
    )


def decode_teams(raw: JsonObj) -> ResultE[FrozenList[tuple[TeamObj, FrozenList[DerivedAgent]]]]:
    return JsonUnfolder.require(
        raw,
        "teams",
        lambda v: Unfolder.to_list_of(
            v,
            lambda j: Unfolder.to_json(j).bind(decode_team_obj_with_agents),
        ),
    )


# DECODERS AGENTS


def decode_agent_obj(raw: JsonObj) -> ResultE[AgentObj]:
    first = smash.smash_result_3(
        decode_user_bulk(raw),
        JsonUnfolder.require(raw, "IsConfirmed", DecodeUtils.to_str).map(parse_bool),
        JsonUnfolder.require(raw, "Email", DecodeUtils.to_str),
    )

    second = smash.smash_result_3(
        JsonUnfolder.require(raw, "Profile", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "Role", DecodeUtils.to_str),
        JsonUnfolder.require(raw, "Status", DecodeUtils.to_str),
    )
    return smash.smash_result_2(first, second).map(lambda v: AgentObj(*v[0], *v[1]))


def decode_agents(raws: FrozenList[JsonObj]) -> ResultE[FrozenList[AgentObj]]:
    return decode_list_objs(raws, decode_agent_obj)
