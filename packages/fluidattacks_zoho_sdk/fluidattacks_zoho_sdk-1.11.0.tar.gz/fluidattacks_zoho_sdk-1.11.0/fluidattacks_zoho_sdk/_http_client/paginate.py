from collections.abc import Callable
from typing import NewType, TypeVar

from fa_purity import Cmd, FrozenList, Maybe, Result, ResultE
from fa_purity._core.utils import raise_exception

from ._core import HttpJsonClient

_T = TypeVar("_T")
FromIndex = NewType("FromIndex", int)
Limit = NewType("Limit", int)


def validate_next_page(
    from_index: FromIndex,
    items: FrozenList[_T],
    limit: Limit,
) -> ResultE[tuple[FrozenList[_T], Maybe[FromIndex]]]:
    return Result.success(
        (items, Maybe.some(FromIndex(from_index + limit)) if len(items) > 0 else Maybe.empty()),
    )


def get_page(
    client: HttpJsonClient,
    from_index: Maybe[FromIndex],
    limit: Limit,
    get_endpoint: Callable[
        [HttpJsonClient, Maybe[FromIndex], Limit],
        Cmd[ResultE[tuple[FrozenList[_T], Maybe[FromIndex]]]],
    ],
) -> Cmd[tuple[FrozenList[_T], Maybe[FromIndex]]]:
    return get_endpoint(client, from_index, limit).map(
        lambda r: r.alt(raise_exception).to_union(),
    )
