import inspect
import logging

from fa_purity import Cmd, FrozenList, Result, ResultE, Unsafe, cast_exception
from fa_purity.json import JsonObj, Primitive, UnfoldedFactory
from fluidattacks_etl_utils.bug import Bug
from fluidattacks_etl_utils.retry import retry_cmd
from requests import Response

from fluidattacks_zoho_sdk._decoders import assert_single
from fluidattacks_zoho_sdk._http_client import HttpJsonClient, RelativeEndpoint

from ._decode import decode_bulk_info, transform_columns
from .core import (
    BulkData,
    BulkEndpoint,
    BulkExportObj,
    BulkStatus,
    FileName,
    ModuleName,
    ShouldRetry,
)
from .utils import _handle_status, _wait_job, unzip_data

LOG = logging.getLogger(__name__)


def _retry_waiting_step(
    retry: int,
    result: ResultE[BulkStatus],
    job: BulkExportObj,
    client: HttpJsonClient,
) -> Cmd[ResultE[BulkStatus]]:
    error_or_ok = result.to_coproduct().map(lambda _s: False, lambda e: isinstance(e, ShouldRetry))
    if error_or_ok is True:
        return _wait_job(retry, job.id_bulk).bind(
            lambda _: get_status_bulk_export(client, job).map(  # token
                lambda r: r.bind(lambda tup: _handle_status(tup[1])),
            ),
        )

    return Cmd.wrap_value(result)


def create_bulk_export(
    client: HttpJsonClient,
    # access_token: Token,
    module: ModuleName,
    endpoint_bulk: BulkEndpoint,
) -> Cmd[ResultE[tuple[BulkExportObj, BulkStatus]]]:
    endpoint = RelativeEndpoint.new(endpoint_bulk.route)
    params: dict[str, Primitive] = {"module": module.module}

    return client.post(endpoint, UnfoldedFactory.from_dict(params)).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(
                    Bug.new("_create_bulk_export", inspect.currentframe(), e, ()),
                ),
            )
            .bind(assert_single)
            .bind(decode_bulk_info)
        ),
    )


def get_status_retry(
    client: HttpJsonClient,
    bulk: BulkExportObj,
    max_attempts: int,
) -> Cmd[ResultE[BulkStatus]]:
    def get_attempt(
        obj: BulkExportObj,
        client: HttpJsonClient,
    ) -> Cmd[ResultE[BulkStatus]]:
        return get_status_bulk_export(client, obj).map(
            lambda result: (
                result.alt(
                    lambda e: cast_exception(
                        Bug.new("_get_bulk_export_status", inspect.currentframe(), e, ()),
                    ),
                ).bind(lambda tup: _handle_status(tup[1]))
            ),
        )

    log = Cmd.wrap_impure(lambda: LOG.info("[API]: Starting read status of bulk export"))
    handled = log + get_attempt(bulk, client)  # token

    return retry_cmd(
        handled,
        lambda retry, result: _retry_waiting_step(retry, result, bulk, client),  # token
        max_attempts,
    ).map(lambda r: r.alt(cast_exception))


def get_status_bulk_export(
    client: HttpJsonClient,
    # access_token: Token,
    bulk: BulkExportObj,
) -> Cmd[ResultE[tuple[BulkExportObj, BulkStatus]]]:
    endpoint = RelativeEndpoint.new("bulkExport", bulk.id_bulk.id_bulk)
    params: dict[str, Primitive] = {}

    return client.get(endpoint, UnfoldedFactory.from_dict(params)).map(  # access_token
        lambda result: (
            result.alt(
                lambda e: cast_exception(
                    Bug.new("_get_bulk_export_status", inspect.currentframe(), e, ()),
                ),
            )
            .bind(assert_single)
            .bind(decode_bulk_info)
        ),
    )


def _unwrap_and_unzip(
    result: Result[Response, Exception],
    file_name: FileName,
) -> Cmd[ResultE[BulkData]]:
    return result.to_coproduct().map(
        lambda inl: unzip_data(inl, file_name),
        lambda ri: Cmd.wrap_value(Result.failure(ri)),
    )


def download_bulk(
    client: HttpJsonClient,
    # access_token: Token,
    bulk: BulkExportObj,
    file_name: FileName,
) -> Cmd[ResultE[BulkData]]:
    endpoint = RelativeEndpoint.new("downloadBulkExportFile")
    params: dict[str, Primitive] = {"exportId": bulk.id_bulk.id_bulk}

    return (
        client.get_response(endpoint, UnfoldedFactory.from_dict(params))
        .map(
            lambda result: result.alt(
                lambda e: cast_exception(
                    Bug.new("_download_bulk_export", inspect.currentframe(), e, ()),
                ),
            ),
        )
        .bind(lambda v: _unwrap_and_unzip(v, file_name))
    )


def _wait_and_download(
    bulk_obj: BulkExportObj,
    client: HttpJsonClient,
    file_name: FileName,
) -> Cmd[ResultE[BulkData]]:
    return (
        get_status_retry(client, bulk_obj, 10)  # token
        .map(lambda r: r.map(lambda _: bulk_obj))
        .map(lambda r: r.alt(Unsafe.raise_exception).to_union())
        .bind(lambda bulk: download_bulk(client, bulk, file_name))
    )


def transform_csv_phase(csv: ResultE[BulkData]) -> ResultE[FrozenList[JsonObj]]:
    bulk_data = csv.alt(Unsafe.raise_exception).to_union()
    return transform_columns(bulk_data)


def fetch_bulk(
    client: HttpJsonClient,
    # access_token: Token,
    module: ModuleName,
    endpoint_bulk: BulkEndpoint,
    file_name: FileName,
) -> Cmd[ResultE[FrozenList[JsonObj]]]:
    create_bulk: Cmd[ResultE[tuple[BulkExportObj, BulkStatus]]] = create_bulk_export(
        client,
        # access_token,
        module,
        endpoint_bulk,
    )

    def on_created(
        result: ResultE[tuple[BulkExportObj, BulkStatus]],
    ) -> Cmd[ResultE[FrozenList[JsonObj]]]:
        return (
            result.map(lambda pair: pair[0])
            .to_coproduct()
            .map(
                lambda bulk_obj: _wait_and_download(bulk_obj, client, file_name).map(
                    lambda data: transform_csv_phase(data),
                ),
                lambda err: Cmd.wrap_value(Result.failure(err)),
            )
        )

    return create_bulk.bind(on_created)
