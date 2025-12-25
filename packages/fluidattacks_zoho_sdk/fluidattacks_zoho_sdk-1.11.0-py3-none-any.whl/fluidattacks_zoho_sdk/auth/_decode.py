from typing import (
    TypeVar,
)

from fa_purity import (
    Coproduct,
    CoproductFactory,
    FrozenList,
    Result,
    ResultE,
    ResultFactory,
)
from fa_purity.json import (
    JsonObj,
)
from pure_requests.response import (
    handle_status,
    json_decode,
)
from requests import (
    HTTPError,
    JSONDecodeError,
    Response,
)

_T = TypeVar("_T")


def decode_json(
    response: Response,
) -> Result[JsonObj, Coproduct[HTTPError, Coproduct[JSONDecodeError, TypeError]]]:
    _factory: CoproductFactory[HTTPError, Coproduct[JSONDecodeError, TypeError]] = (
        CoproductFactory()
    )
    _factory_2: CoproductFactory[JSONDecodeError, TypeError] = CoproductFactory()
    _factory_3: ResultFactory[
        JsonObj,
        Coproduct[HTTPError, Coproduct[JSONDecodeError, TypeError]],
    ] = ResultFactory()
    return (
        handle_status(response)
        .alt(lambda x: _factory.inl(x))
        .bind(
            lambda r: json_decode(r)
            .alt(lambda e: _factory.inr(_factory_2.inl(e)))
            .bind(
                lambda c: c.map(
                    lambda j: _factory_3.success(j),
                    lambda _: _factory_3.failure(
                        _factory.inr(_factory_2.inr(TypeError("Expected non-list"))),
                    ),
                ),
            ),
        )
    )


def require_index(items: FrozenList[_T], index: int) -> ResultE[_T]:
    try:
        return Result.success(items[index])
    except IndexError as err:
        return Result.failure(Exception(err))
