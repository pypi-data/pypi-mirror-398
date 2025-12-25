import inspect
import logging

from fa_purity import (
    Cmd,
    FrozenDict,
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

from ._core import (
    Credentials,
    Token,
)
from ._decode import (
    decode_json,
)

ACCOUNTS_URL = "https://accounts.zoho.com"  # for US region
LOG = logging.getLogger(__name__)


def _decode(raw: JsonObj) -> ResultE[Token]:
    return JsonUnfolder.require(
        raw,
        "access_token",
        lambda v: Unfolder.to_primitive(v).bind(JsonPrimitiveUnfolder.to_str),
    ).map(Token)


def new_access_token(credentials: Credentials) -> Cmd[Token]:
    LOG.info("Generating access token")
    endpoint = Endpoint(f"{ACCOUNTS_URL}/oauth/v2/token")
    params: dict[str, Primitive] = {
        "refresh_token": credentials.refresh_token,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "grant_type": "refresh_token",
    }
    empty: JsonObj = FrozenDict({})
    client = HttpClientFactory.new_client(None, None, None)
    response = client.post(endpoint, Params(UnfoldedFactory.from_dict(params)), Data(empty)).map(
        lambda r: Bug.assume_success(
            "NewTokenError.response",
            inspect.currentframe(),
            (str(client), endpoint.raw, str(params)),
            r.alt(cast_exception),
        ),
    )
    data = response.map(
        lambda r: Bug.assume_success(
            "NewTokenError.decode_json",
            inspect.currentframe(),
            (str(client), endpoint.raw, str(params)),
            decode_json(r).alt(
                lambda c: c.map(
                    cast_exception,
                    lambda v: v.map(cast_exception, cast_exception),
                ),
            ),
        ),
    )

    return data.map(
        lambda j: Bug.assume_success(
            "NewTokenError.decode_json",
            inspect.currentframe(),
            (JsonUnfolder.dumps(j),),
            _decode(j),
        ),
    )
