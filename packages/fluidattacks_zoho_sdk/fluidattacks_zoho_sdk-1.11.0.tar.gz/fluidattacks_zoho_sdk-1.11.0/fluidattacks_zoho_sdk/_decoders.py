from collections.abc import Callable
from datetime import UTC, datetime
from typing import (
    IO,
    TypeVar,
)

from fa_purity import (
    Coproduct,
    FrozenList,
    Maybe,
    PureIterFactory,
    Result,
    ResultE,
    ResultTransform,
    Unsafe,
)
from fa_purity.date_time import DatetimeUTC
from fa_purity.json import (
    JsonObj,
    JsonPrimitiveUnfolder,
    JsonUnfolder,
    JsonValueFactory,
    UnfoldedFactory,
    Unfolder,
)
from fluidattacks_etl_utils.decode import DecodeUtils
from fluidattacks_etl_utils.natural import Natural

from fluidattacks_zoho_sdk.auth import Credentials
from fluidattacks_zoho_sdk.ids import (
    AccountId,
    ContactId,
    CrmId,
    DeparmentId,
    ProductId,
    ProfileId,
    RoleId,
    TeamId,
    TicketId,
    UserId,
)
from fluidattacks_zoho_sdk.zoho_desk.core import OptionalId

_T = TypeVar("_T")


def decode_list_objs(
    items: FrozenList[JsonObj],
    transaform: Callable[[JsonObj], ResultE[_T]],
) -> ResultE[FrozenList[_T]]:
    if not items:
        return Result.failure(ValueError("Expected a list"))

    return ResultTransform.all_ok(
        PureIterFactory.from_list(items).map(lambda v: transaform(v)).to_list(),
    )


def _decode_zoho_creds(raw: JsonObj) -> ResultE[Credentials]:
    client_id = JsonUnfolder.require(raw, "client_id", Unfolder.to_primitive).bind(
        JsonPrimitiveUnfolder.to_str,
    )
    client_secret = JsonUnfolder.require(raw, "client_secret", Unfolder.to_primitive).bind(
        JsonPrimitiveUnfolder.to_str,
    )
    refresh_token = JsonUnfolder.require(raw, "refresh_token", Unfolder.to_primitive).bind(
        JsonPrimitiveUnfolder.to_str,
    )
    scopes_result = JsonUnfolder.require(
        raw,
        "scopes",
        lambda i: Unfolder.to_list_of(
            i,
            lambda x: Unfolder.to_primitive(x).bind(JsonPrimitiveUnfolder.to_str),
        ),
    )
    return client_id.bind(
        lambda cid: client_secret.bind(
            lambda secret: refresh_token.bind(
                lambda token: scopes_result.map(
                    lambda scopes: Credentials(cid, secret, token, frozenset(scopes)),
                ),
            ),
        ),
    )


def get_sub_json(raw: JsonObj, key: str) -> JsonObj:
    return (
        JsonUnfolder.require(raw, key, lambda v: Unfolder.to_json(v))
        .alt(Unsafe.raise_exception)
        .to_union()
    )


def decode_optional_date(raw: JsonObj, key: str) -> ResultE[Maybe[DatetimeUTC]]:
    return JsonUnfolder.optional(raw, key, DecodeUtils.to_opt_date_time).map(
        lambda v: v.bind(lambda j: j),
    )


def decode_datetime_assume_utc(s: str) -> ResultE[Maybe[DatetimeUTC]]:
    try:
        if not s or not s.strip():
            return Result.success(Maybe.empty())

        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        return DecodeUtils.to_opt_date_time(JsonValueFactory.from_unfolded(str(dt)))

    except ValueError as e:
        return Result.failure(e)


def flatten_decoder_date(
    y: Result[Maybe[ResultE[Maybe[DatetimeUTC]]], Exception],
) -> ResultE[Maybe[DatetimeUTC]]:
    return y.bind(lambda maybe_inner: maybe_inner.value_or(Result.success(Maybe.empty())))


def decode_opt_date_to_utc(raw: JsonObj, key: str) -> ResultE[Maybe[DatetimeUTC]]:
    date = JsonUnfolder.optional(raw, key, DecodeUtils.to_opt_str).map(
        lambda maybe_str: maybe_str.bind(lambda j: j).map(lambda v: decode_datetime_assume_utc(v)),
    )
    return flatten_decoder_date(date)


def decode_require_date(raw: JsonObj, key: str) -> ResultE[DatetimeUTC]:
    return JsonUnfolder.require(raw, key, DecodeUtils.to_date_time)


def decode_maybe_str(raw: JsonObj, key: str) -> ResultE[Maybe[str]]:
    return JsonUnfolder.optional(raw, key, DecodeUtils.to_opt_str).map(
        lambda v: v.bind(lambda j: j),
    )


def decode_zoho_creds(auth_file: IO[str]) -> ResultE[Credentials]:
    return UnfoldedFactory.load(auth_file).bind(_decode_zoho_creds)


def decode_user_id(raw: JsonObj) -> ResultE[UserId]:
    return (
        JsonUnfolder.require(raw, "id", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(UserId)
    )


def decode_rol_id(raw: JsonObj) -> ResultE[RoleId]:
    return (
        JsonUnfolder.require(raw, "roleId", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(RoleId)
    )


def decode_profile_id(raw: JsonObj) -> ResultE[ProfileId]:
    return (
        JsonUnfolder.require(raw, "profileId", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(ProfileId)
    )


def decode_account_id_bulk(raw: JsonObj) -> ResultE[AccountId]:
    return JsonUnfolder.require(raw, "Account ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(AccountId),
    )


def decode_account_id(raw: JsonObj) -> ResultE[AccountId]:
    return (
        JsonUnfolder.require(raw, "Account ID", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(AccountId)
    )


def decode_crm_id(raw: JsonObj) -> ResultE[CrmId]:
    return JsonUnfolder.require(raw, "CRM ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(CrmId),
    )


def decode_department_id(raw: JsonObj) -> ResultE[DeparmentId]:
    return (
        JsonUnfolder.require(raw, "Department", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(DeparmentId)
    )


def decode_department_id_team(raw: JsonObj) -> ResultE[DeparmentId]:
    return (
        JsonUnfolder.require(raw, "departmentId", DecodeUtils.to_str)
        .bind(lambda v: Natural.from_int(int(v)))
        .map(DeparmentId)
    )


def decode_require_product_id(raw: JsonObj) -> ResultE[ProductId]:
    return JsonUnfolder.require(raw, "Product ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: ProductId(obj)),
    )


def decode_team_id(raw: JsonObj) -> ResultE[TeamId]:
    return JsonUnfolder.require(raw, "Team Id", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: TeamId(obj)),
    )


def decode_ticket_id(raw: JsonObj) -> ResultE[TicketId]:
    return JsonUnfolder.require(raw, "ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: TicketId(obj)),
    )


def decode_contact_id(raw: JsonObj) -> ResultE[ContactId]:
    return JsonUnfolder.require(raw, "Contact ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: ContactId(obj)),
    )


def decode_contact_id_bulk(raw: JsonObj) -> ResultE[ContactId]:
    return JsonUnfolder.require(raw, "ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: ContactId(obj)),
    )


def decode_id_team(raw: JsonObj) -> ResultE[TeamId]:
    return JsonUnfolder.require(raw, "id", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(lambda obj: TeamId(obj)),
    )


def decode_user_id_bulk(raw: JsonObj) -> ResultE[UserId]:
    return JsonUnfolder.require(raw, "ID", DecodeUtils.to_str).bind(
        lambda v: Natural.from_int(int(v)).map(UserId),
    )


def decode_optional_id(raw: JsonObj, key: str) -> ResultE[Maybe[OptionalId]]:
    return JsonUnfolder.optional(raw, key, DecodeUtils.to_opt_str).map(
        lambda v: v.bind(lambda x: x).map(lambda j: OptionalId(j)),
    )


def assert_single(item: Coproduct[JsonObj, FrozenList[JsonObj]]) -> ResultE[JsonObj]:
    return item.map(
        Result.success,
        lambda _: Result.failure(ValueError("Expected a json not a list")),
    )


def assert_multiple(item: Coproduct[JsonObj, FrozenList[JsonObj]]) -> ResultE[FrozenList[JsonObj]]:
    return item.map(
        lambda _: Result.failure(ValueError("Expected a json list not a single json")),
        Result.success,
    )
