import inspect
import logging
from getpass import (
    getpass,
)
from urllib.parse import (
    urlencode,
)

from fa_purity import (
    Cmd,
    FrozenDict,
    cast_exception,
)
from fa_purity.json import (
    JsonObj,
    Primitive,
    UnfoldedFactory,
)
from fluidattacks_etl_utils.bug import Bug
from pure_requests.basic import (
    Data,
    Endpoint,
    HttpClientFactory,
    Params,
)

from ._core import (
    RefreshToken,
)
from ._decode import (
    decode_json,
)

ACCOUNTS_URL = "https://accounts.zoho.com"  # for US region
LOG = logging.getLogger(__name__)


def _user_input() -> Cmd[RefreshToken]:
    def _action() -> RefreshToken:
        LOG.info("Refresh token to revoke:")
        return RefreshToken(getpass())

    return Cmd.wrap_impure(_action)


def _revoke_refresh_token(token: RefreshToken) -> Cmd[JsonObj]:
    endpoint = Endpoint(f"{ACCOUNTS_URL}/oauth/v2/token/revoke")
    empty: JsonObj = FrozenDict({})
    raw: dict[str, Primitive] = {
        "token": token.raw_token,
    }
    encoded = urlencode(raw)
    headers: dict[str, Primitive] = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(encoded)),
    }
    client = HttpClientFactory.new_client(None, UnfoldedFactory.from_dict(headers), None)
    return (
        client.post(
            endpoint,
            Params(empty),
            Data(encoded),
        )
        .map(
            lambda r: Bug.assume_success(
                "AuthRevokeError.response",
                inspect.currentframe(),
                (endpoint.raw, str(token)),
                r.alt(cast_exception),
            ),
        )
        .map(
            lambda r: Bug.assume_success(
                "AuthRevokeError.decode",
                inspect.currentframe(),
                (endpoint.raw, str(token), str(r), str(decode_json(r))),
                decode_json(r).alt(
                    lambda e: e.map(
                        cast_exception,
                        lambda x: x.map(cast_exception, cast_exception),
                    ),
                ),
            ),
        )
    )


def revoke_refresh_token() -> Cmd[JsonObj]:
    return (
        _user_input()
        .bind(_revoke_refresh_token)
        .bind(
            lambda j: Cmd.wrap_impure(lambda: LOG.debug("revoke_refresh_token: %s", j)).map(
                lambda _: j,
            ),
        )
    )
