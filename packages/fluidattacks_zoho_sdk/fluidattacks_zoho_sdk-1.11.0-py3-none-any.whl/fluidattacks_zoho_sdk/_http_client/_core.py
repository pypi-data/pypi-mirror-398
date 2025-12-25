from __future__ import (
    annotations,
)

from collections.abc import Callable
from dataclasses import (
    dataclass,
    field,
)

from fa_purity import Cmd, Coproduct, FrozenList, Result, ResultE, UnitType, unit
from fa_purity.json import (
    JsonObj,
)
from pure_requests.retry import (
    MaxRetriesReached,
)
from requests import Response
from requests.exceptions import (
    ChunkedEncodingError as RawChunkedEncodingError,
)
from requests.exceptions import (
    ConnectionError as RawConnectionError,
)
from requests.exceptions import (
    HTTPError as RawHTTPError,
)
from requests.exceptions import (
    JSONDecodeError as RawJSONDecodeError,
)
from requests.exceptions import (
    RequestException as RawRequestException,
)

from fluidattacks_zoho_sdk.auth import Token


@dataclass(frozen=True)
class UnhandledErrors:
    error: Coproduct[JSONDecodeError, Coproduct[HTTPError, RequestException]]


@dataclass(frozen=True)
class HandledErrors:
    error: Coproduct[
        HTTPError,
        Coproduct[ChunkedEncodingError, RequestsConnectionError],
    ]


@dataclass(frozen=True)
class _Private:
    pass


@dataclass(frozen=True)
class HTTPError:
    raw: RawHTTPError


@dataclass(frozen=True)
class JSONDecodeError:
    raw: RawJSONDecodeError


@dataclass(frozen=True)
class ChunkedEncodingError:
    _private: _Private = field(repr=False, hash=False, compare=False)
    raw: RawChunkedEncodingError


@dataclass(frozen=True)
class RequestsConnectionError:
    _private: _Private = field(repr=False, hash=False, compare=False)
    raw: RawConnectionError


@dataclass(frozen=True)
class RequestException:
    raw: RawRequestException

    def to_chunk_error(self) -> ResultE[ChunkedEncodingError]:
        if isinstance(self.raw, RawChunkedEncodingError):
            return Result.success(ChunkedEncodingError(_Private(), self.raw))
        return Result.failure(ValueError("Not a ChunkedEncodingError"))

    def to_connection_error(self) -> ResultE[RequestsConnectionError]:
        if isinstance(self.raw, RawConnectionError):
            return Result.success(RequestsConnectionError(_Private(), self.raw))
        return Result.failure(ValueError("Not a RequestsConnectionError"))


@dataclass(frozen=True)
class RelativeEndpoint:
    paths: FrozenList[str]

    @staticmethod
    def new(*args: str) -> RelativeEndpoint:
        return RelativeEndpoint(tuple(args))


@dataclass(frozen=True)
class HttpJsonClient:
    get: Callable[
        [RelativeEndpoint, JsonObj],  # Token
        Cmd[
            Result[
                Coproduct[JsonObj, FrozenList[JsonObj]],
                Coproduct[UnhandledErrors, MaxRetriesReached],
            ]
        ],
    ]
    post: Callable[
        [RelativeEndpoint, JsonObj],
        Cmd[
            Result[
                Coproduct[JsonObj, FrozenList[JsonObj]],
                Coproduct[UnhandledErrors, MaxRetriesReached],
            ]
        ],
    ]

    get_response: Callable[
        [RelativeEndpoint, JsonObj],
        Cmd[Result[Response, Coproduct[UnhandledErrors, MaxRetriesReached]]],
    ]


@dataclass(frozen=True)
class TokenManager:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: TokenManager._Private = field(repr=False, hash=False, compare=False)
    _inner: dict[UnitType, Token]

    @staticmethod
    def new(token: Token) -> Cmd[TokenManager]:
        return Cmd.wrap_impure(lambda: TokenManager(TokenManager._Private(), {unit: token}))

    @property
    def get(self) -> Cmd[Token]:
        return Cmd.wrap_impure(lambda: self._inner[unit])

    def update(self, token: Token) -> Cmd[UnitType]:
        def _action() -> UnitType:
            self._inner[unit] = token
            return unit

        return Cmd.wrap_impure(_action)
