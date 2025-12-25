from __future__ import (
    annotations,
)

import logging
from collections.abc import Callable
from dataclasses import (
    dataclass,
)
from typing import (
    TypeVar,
)

from fa_purity import Cmd, Coproduct, FrozenDict, FrozenList, Maybe, Result, UnitType
from fa_purity.json import JsonObj, JsonPrimitiveFactory, JsonUnfolder, JsonValue
from fluidattacks_etl_utils.decode import int_to_str
from fluidattacks_etl_utils.smash import bind_chain
from pure_requests import (
    response,
)
from pure_requests import (
    retry as _retry,
)
from pure_requests.basic import Data, Endpoint, HttpClient, HttpClientFactory, Params
from pure_requests.retry import (
    HandledError,
    MaxRetriesReached,
)
from requests import Response

from fluidattacks_zoho_sdk.auth import AuthApiFactory, Credentials, Token
from fluidattacks_zoho_sdk.ids import OrgId

from ._core import (
    HandledErrors,
    HTTPError,
    HttpJsonClient,
    JSONDecodeError,
    RelativeEndpoint,
    RequestException,
    TokenManager,
    UnhandledErrors,
)

LOG = logging.getLogger(__name__)

_S = TypeVar("_S")
_F = TypeVar("_F")
HTTP_UNAUTHORIZED: int = 401


def _refresh_access_token(creds: Credentials) -> Cmd[Token]:
    return AuthApiFactory.auth_api(creds).new_access_token


def _is_404(error: Maybe[HTTPError]) -> tuple[bool, int]:
    status: int = error.map(
        lambda v: v.raw.response.status_code,  # type: ignore[misc]
    ).value_or(0)
    status_is_404: bool = (
        error.map(lambda e: e.raw.response.status_code == HTTP_UNAUTHORIZED).value_or(False)  # type: ignore[misc]
    )
    return (status_is_404, status)


def _extract_http_error(error: HandledError[HandledErrors, UnhandledErrors]) -> Maybe[HTTPError]:
    return error.value.map(
        lambda handled: handled.error.map(
            lambda http_err: Maybe.some(http_err),
            lambda _: Maybe.empty(),
        ),
        lambda _: Maybe.empty(),
    )


def _retry_cmd(
    retry: int,
    item: Result[_S, _F],
    client_zoho: Client,
    make_request: Callable[[HttpClient], Cmd[Result[_S, _F]]],
) -> Cmd[Result[_S, _F]]:
    def handle_401(error: _F) -> Cmd[Result[_S, _F]]:
        is_401 = _is_404(_extract_http_error(error))  # type: ignore[arg-type]
        if is_401[0]:
            return Cmd.wrap_impure(lambda: LOG.info("Refreshing token...")) + _refresh_access_token(
                client_zoho.creds,
            ).bind(
                lambda new_token: client_zoho.update_token(new_token),
            ).bind(
                lambda _: client_zoho.build_headers()
                .map(
                    lambda headers: HttpClientFactory.new_client(
                        None,
                        headers,
                        False,
                    ),  # HttpClient
                )
                .bind(make_request),
            )

        log = Cmd.wrap_impure(
            lambda: LOG.info(
                "retry #%2s waiting... ",
                retry,
            ),
        )
        return _retry.cmd_if_fail(item, log + _retry.sleep_cmd(retry**2))

    return item.map(lambda _: Cmd.wrap_value(item)).alt(handle_401).to_union()


def _http_error_handler(
    error: HTTPError,
) -> HandledError[HandledErrors, UnhandledErrors]:
    err_code: int = error.raw.response.status_code  # type: ignore[misc]
    handled = (
        401,
        429,
    )
    if err_code in range(500, 600) or err_code in handled:
        return HandledError.handled(HandledErrors(Coproduct.inl(error)))
    return HandledError.unhandled(UnhandledErrors(Coproduct.inr(Coproduct.inl(error))))


def _handled_request_exception(
    error: RequestException,
) -> HandledError[HandledErrors, UnhandledErrors]:
    return (
        error.to_chunk_error()
        .map(lambda e: HandledError.handled(HandledErrors(Coproduct.inr(Coproduct.inl(e)))))
        .lash(
            lambda _: error.to_connection_error().map(
                lambda e: HandledError.handled(HandledErrors(Coproduct.inr(Coproduct.inr(e)))),
            ),
        )
        .value_or(HandledError.unhandled(UnhandledErrors(Coproduct.inr(Coproduct.inr(error)))))
    )


def _handled_errors(
    error: Coproduct[JSONDecodeError, Coproduct[HTTPError, RequestException]],
) -> HandledError[HandledErrors, UnhandledErrors]:
    """Classify errors."""
    return error.map(
        lambda _: HandledError.unhandled(UnhandledErrors(error)),
        lambda c: c.map(
            _http_error_handler,
            _handled_request_exception,
        ),
    )


def _handled_errors_response(
    error: Coproduct[HTTPError, RequestException],
) -> HandledError[HandledErrors, UnhandledErrors]:
    return error.map(
        _http_error_handler,
        _handled_request_exception,
    )


def _adjust_unhandled(
    error: UnhandledErrors | MaxRetriesReached,
) -> Coproduct[UnhandledErrors, MaxRetriesReached]:
    return Coproduct.inr(error) if isinstance(error, MaxRetriesReached) else Coproduct.inl(error)


@dataclass(frozen=True)
class Client:
    _creds: Credentials
    _max_retries: int
    _org_id: OrgId
    _token: TokenManager

    def _full_endpoint(self, endpoint: RelativeEndpoint) -> Endpoint:
        return Endpoint("/".join(("https://desk.zoho.com/api/v1", *endpoint.paths)))

    @staticmethod
    def new(creds: Credentials, org_id: OrgId, token: TokenManager) -> Client:
        return Client(creds, 3, org_id, token)

    def _headers(self, access_token: Token) -> JsonObj:
        return FrozenDict(
            {
                "orgId": JsonValue.from_primitive(
                    JsonPrimitiveFactory.from_raw(int_to_str(self._org_id.org_id.value)),
                ),
                "Authorization": JsonValue.from_primitive(
                    JsonPrimitiveFactory.from_raw(f"Zoho-oauthtoken {access_token.raw_token}"),
                ),
            },
        )

    def get(
        self,
        endpoint: RelativeEndpoint,
        params: JsonObj,
    ) -> Cmd[
        Result[
            Coproduct[JsonObj, FrozenList[JsonObj]],
            Coproduct[UnhandledErrors, MaxRetriesReached],
        ]
    ]:
        _full = self._full_endpoint(endpoint)
        log = Cmd.wrap_impure(
            lambda: LOG.info("[API] get: %s\nparams = %s", _full, JsonUnfolder.dumps(params)),
        )

        token_manager_cmd = self._token.get
        client_cmd = token_manager_cmd.map(
            lambda token: HttpClientFactory.new_client(None, self._headers(token), False),
        )

        def make_request(
            new_client: HttpClient,
        ) -> Cmd[
            Result[
                Coproduct[JsonObj, FrozenList[JsonObj]],
                HandledError[HandledErrors, UnhandledErrors],
            ]
        ]:
            return (
                new_client.get(_full, Params(params))
                .map(lambda r: r.alt(RequestException))
                .map(lambda r: bind_chain(r, lambda i: response.handle_status(i).alt(HTTPError)))
                .map(
                    lambda r: bind_chain(
                        r,
                        lambda i: response.json_decode(i).alt(JSONDecodeError),
                    ).alt(_handled_errors),
                )
            )

        handled = log + client_cmd.bind(make_request)

        return _retry.retry_cmd(
            handled,
            lambda retry, item: _retry_cmd(retry, item, self, make_request),
            self._max_retries,
        ).map(lambda r: r.alt(_adjust_unhandled))

    def post(
        self,
        endpoint: RelativeEndpoint,
        params: JsonObj,
    ) -> Cmd[
        Result[
            Coproduct[JsonObj, FrozenList[JsonObj]],
            Coproduct[UnhandledErrors, MaxRetriesReached],
        ]
    ]:
        _full = self._full_endpoint(endpoint)
        log = Cmd.wrap_impure(lambda: LOG.info("[API] call (post): %s", _full))

        client_cmd = self._token.get.map(
            lambda t: HttpClientFactory.new_client(
                None,
                self._headers(t),
                False,
            ),
        )

        def make_request(
            new_client: HttpClient,
        ) -> Cmd[
            Result[
                Coproduct[JsonObj, FrozenList[JsonObj]],
                HandledError[HandledErrors, UnhandledErrors],
            ]
        ]:
            return (
                new_client.post(
                    _full,
                    Params(FrozenDict({})),
                    Data(params),
                )
                .map(lambda r: r.alt(RequestException))
                .map(lambda r: bind_chain(r, lambda i: response.handle_status(i).alt(HTTPError)))
                .map(
                    lambda r: bind_chain(
                        r,
                        lambda i: response.json_decode(i).alt(JSONDecodeError),
                    ).alt(_handled_errors),
                )
            )

        handled = log + client_cmd.bind(make_request)

        return _retry.retry_cmd(
            handled,
            lambda retry, item: _retry_cmd(retry, item, self, make_request),
            self._max_retries,
        ).map(lambda r: r.alt(_adjust_unhandled))

    def get_response(
        self,
        endpoint: RelativeEndpoint,
        params: JsonObj,
    ) -> Cmd[Result[Response, Coproduct[UnhandledErrors, MaxRetriesReached]]]:
        _full = self._full_endpoint(endpoint)
        log = Cmd.wrap_impure(
            lambda: LOG.info("[API] get: %s\nparams = %s", _full, JsonUnfolder.dumps(params)),
        )

        client_cmd = self._token.get.map(
            lambda t: HttpClientFactory.new_client(
                None,
                self._headers(t),
                False,
            ),
        )

        def make_request(
            new_client: HttpClient,
        ) -> Cmd[
            Result[
                Response,
                HandledError[HandledErrors, UnhandledErrors],
            ]
        ]:
            return (
                new_client.get(_full, Params(params))
                .map(lambda r: r.alt(RequestException))
                .map(lambda r: bind_chain(r, lambda i: response.handle_status(i).alt(HTTPError)))
                .map(lambda r: r.alt(_handled_errors_response))
            )

        handled = log + client_cmd.bind(make_request)

        return _retry.retry_cmd(
            handled,
            lambda retry, item: _retry_cmd(retry, item, self, make_request),
            self._max_retries,
        ).map(lambda r: r.alt(_adjust_unhandled))

    @property
    def client(self) -> HttpJsonClient:
        return HttpJsonClient(self.get, self.post, self.get_response)

    @property
    def creds(self) -> Credentials:
        return self._creds

    def build_headers(self) -> Cmd[JsonObj]:
        return self._token.get.map(lambda t: self._headers(t))

    def update_token(self, new_token: Token) -> Cmd[UnitType]:
        return self._token.update(new_token)
