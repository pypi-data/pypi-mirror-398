from datetime import UTC, datetime
from pathlib import Path

from fa_purity import FrozenList, Maybe, Unsafe
from fa_purity.date_time import DatetimeUTC
from fa_purity.json import JsonObj, JsonValueFactory, Unfolder
from fluidattacks_etl_utils.natural import NaturalOperations

from fluidattacks_zoho_sdk.ids import (
    ContactId,
    DeparmentId,
    TeamId,
    TicketId,
    UserId,
)
from fluidattacks_zoho_sdk.zoho_desk._decode import (
    decode_agent_obj,
    decode_contact_obj,
    decode_teams,
    decode_ticket_obj,
)
from fluidattacks_zoho_sdk.zoho_desk.core import (
    AgentObj,
    ContactAddres,
    ContactDates,
    ContactInfo,
    ContactObj,
    DerivedAgent,
    OptionalId,
    TeamObj,
    TicketDates,
    TicketObj,
    TicketProperties,
    UserObj,
)


def read_json(name_file: str) -> JsonObj:
    raw_data_contact = Path(__file__).parent / name_file
    return (
        JsonValueFactory.load(raw_data_contact.open(encoding="utf=8"))
        .bind(Unfolder.to_json)
        .alt(Unsafe.raise_exception)
        .to_union()
    )


def _assert_utc(date_time: datetime) -> DatetimeUTC:
    return DatetimeUTC.assert_utc(date_time).alt(Unsafe.raise_exception).to_union()


def test_decode_agent() -> None:
    agent_expected = AgentObj(
        UserObj(
            UserId(NaturalOperations.absolute(1892000000056007)),
            Maybe.some("Arnol"),
            "case",
        ),
        True,
        "case@zylker.com",
        "Administrator",
        "CEO",
        "ACTIVE",
    )

    file_name = "data_agent.json"

    decode_data = decode_agent_obj(read_json(file_name)).alt(Unsafe.raise_exception).to_union()
    assert agent_expected == decode_data


def test_decode_contact() -> None:
    expected_data = ContactObj(
        ContactId(NaturalOperations.absolute(3263000000064001)),
        UserObj(
            UserId(NaturalOperations.absolute(3263000000064001)),
            Maybe.some("Jade"),
            "Smith",
        ),
        ContactInfo(
            Maybe.some("lawrence@zylker.com"),
            Maybe.empty(),
            Maybe.some("123 99 888 23"),
            Maybe.empty(),
            Maybe.empty(),
        ),
        ContactAddres(
            Maybe.empty(),
            Maybe.empty(),
            Maybe.empty(),
        ),
        ContactDates(
            Maybe.some(_assert_utc(datetime(2015, 2, 16, 14, 46, 24, tzinfo=UTC))),
            Maybe.some(_assert_utc(datetime(2015, 3, 2, 14, 49, 32, tzinfo=UTC))),
        ),
        Maybe.some(OptionalId("123456")),
        UserId(NaturalOperations.absolute(3263000000057001)),
        Maybe.some(OptionalId("5000000014010")),
        Maybe.empty(),
        Maybe.empty(),
        Maybe.empty(),
        Maybe.empty(),
        Maybe.empty(),
    )
    path_file = "data_contact.json"
    decode_data = decode_contact_obj(read_json(path_file)).alt(Unsafe.raise_exception).to_union()
    assert expected_data == decode_data


def test_decode_ticket() -> None:
    expected_data = TicketObj(
        Maybe.some(OptionalId("1892000000975382")),
        Maybe.some(OptionalId("1892000000006907")),
        Maybe.some(OptionalId("8920000000069071")),
        Maybe.empty(),
        TicketDates(
            Maybe.some(_assert_utc(datetime(2016, 6, 21, 13, 16, 14, 0, tzinfo=UTC))),
            Maybe.some(_assert_utc(datetime(2013, 11, 4, 11, 21, 7, 0, tzinfo=UTC))),
            Maybe.empty(),
            Maybe.some(_assert_utc(datetime(2013, 11, 4, 11, 21, 7, 0, tzinfo=UTC))),
        ),
        TicketProperties(
            TicketId(NaturalOperations.absolute(1892000000042034)),
            Maybe.some(
                "Hi. There is a sudden delay in the processing of the orders. Check this with high priority",  # noqa: E501
            ),
            Maybe.some("Email"),
            Maybe.some("Open"),
            Maybe.some("general"),
            False,
            Maybe.some("High"),
            Maybe.empty(),
            Maybe.some("Low"),
            Maybe.some(
                "Hi. There is a sudden delay in the processing of the orders. Check this with high priority",  # noqa: E501
            ),
        ),
        ContactId(NaturalOperations.absolute(1892000000042032)),
        Maybe.some("carol@zylker.com"),
        Maybe.some("1 888 900 9646"),
        Maybe.empty(),
        Maybe.some("Internal"),
    )
    path_file = "data_ticket.json"
    decode_data = decode_ticket_obj(read_json(path_file)).alt(Unsafe.raise_exception).to_union()
    assert expected_data == decode_data


def test_decode_teams() -> None:
    expected_agents: FrozenList[DerivedAgent] = (
        DerivedAgent(UserId(NaturalOperations.absolute(1234567))),
        DerivedAgent(UserId(NaturalOperations.absolute(987654))),
    )

    expected_team: tuple[TeamObj, FrozenList[DerivedAgent]] = (
        TeamObj(
            DeparmentId(NaturalOperations.absolute(17000000007253)),
            TeamId(NaturalOperations.absolute(17000000013003)),
            "Sales teams for winning customers.",
            "Sales Reps.",
        ),
        expected_agents,
    )

    expected_data: FrozenList[tuple[TeamObj, FrozenList[DerivedAgent]]] = (expected_team,)

    path_file = "data_team.json"
    decode_data = decode_teams(read_json(path_file)).alt(Unsafe.raise_exception).to_union()
    assert expected_data == decode_data
