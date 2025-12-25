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
    Result,
    ResultE,
    cast_exception,
)
from fa_purity.json import (
    JsonObj,
    JsonPrimitiveUnfolder,
    JsonUnfolder,
    Primitive,
    UnfoldedFactory,
    Unfolder,
)
from fluidattacks_etl_utils.bug import Bug
from pure_requests.basic import (
    Data,
    Endpoint,
    HttpClientFactory,
    Params,
)
from requests import (
    RequestException,
    Response,
)

from ._core import (
    ACCOUNTS_URL,
    Credentials,
    RefreshToken,
)
from ._decode import (
    decode_json,
)

LOG = logging.getLogger(__name__)


def _decode(raw: JsonObj) -> ResultE[RefreshToken]:
    LOG.debug("raw token response: %s", JsonUnfolder.dumps(raw))
    return JsonUnfolder.require(
        raw,
        "refresh_token",
        lambda v: Unfolder.to_primitive(v).bind(JsonPrimitiveUnfolder.to_str),
    ).map(RefreshToken)


def _user_input_code() -> Cmd[str]:
    def _action() -> str:
        LOG.info("Paste grant token:")
        token = getpass()
        LOG.debug(token)
        return token

    return Cmd.wrap_impure(_action)


def _gen_refresh_token(
    credentials: Credentials,
    code: str,
) -> Cmd[Result[Response, RequestException]]:
    endpoint = Endpoint(f"{ACCOUNTS_URL}/oauth/v2/token")
    raw: dict[str, Primitive] = {
        "grant_type": "authorization_code",
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "code": code,
    }
    empty: JsonObj = FrozenDict({})
    encoded = urlencode(raw)
    headers: dict[str, Primitive] = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(encoded)),
    }
    client = HttpClientFactory.new_client(None, UnfoldedFactory.from_dict(headers), None)
    return client.post(endpoint, Params(empty), Data(encoded))


def _decode_refresh(result: Result[Response, RequestException]) -> ResultE[RefreshToken]:
    response = Bug.assume_success(
        "AuthRefreshError.response",
        inspect.currentframe(),
        (),
        result.alt(cast_exception),
    )
    json_data = Bug.assume_success(
        "AuthRefreshError.decode_json",
        inspect.currentframe(),
        (),
        decode_json(response).alt(
            lambda e: e.map(cast_exception, lambda f: f.map(cast_exception, cast_exception)),
        ),
    )
    return _decode(json_data)


def generate_refresh_token(
    credentials: Credentials,
) -> Cmd[RefreshToken]:
    msg = Cmd.wrap_impure(
        lambda: LOG.info(
            "Generating refresh token with scopes: %s",
            ",".join(credentials.scopes),
        ),
    )
    return msg + _user_input_code().bind(lambda c: _gen_refresh_token(credentials, c)).map(
        lambda r: Bug.assume_success(
            "AuthRefreshError.decode_token",
            inspect.currentframe(),
            (str(r),),
            _decode_refresh(r),
        ),
    )
