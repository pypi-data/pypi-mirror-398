import csv

from fa_purity import FrozenList, ResultE
from fa_purity.json import JsonObj, JsonUnfolder, JsonValueFactory, Unfolder
from fluidattacks_etl_utils import smash
from fluidattacks_etl_utils.decode import DecodeUtils

from .core import BulkData, BulkExportId, BulkExportObj, BulkStatus, ViewId


def decode_id_bulk(raw: JsonObj) -> ResultE[BulkExportId]:
    return JsonUnfolder.require(raw, "exportId", DecodeUtils.to_str).map(lambda v: BulkExportId(v))


def decode_id_view(raw: JsonObj) -> ResultE[ViewId]:
    return JsonUnfolder.require(raw, "viewId", DecodeUtils.to_str).map(lambda v: ViewId(v))


def decode_status_bulk(raw: JsonObj) -> ResultE[BulkStatus]:
    return JsonUnfolder.require(raw, "status", DecodeUtils.to_str).bind(
        lambda v: BulkStatus.from_raw(v),
    )


def decode_bulk_export(raw: JsonObj) -> ResultE[BulkExportObj]:
    return smash.smash_result_2(
        decode_id_bulk(raw),
        JsonUnfolder.require(raw, "module", DecodeUtils.to_str),
    ).map(lambda bulk: BulkExportObj(*bulk))


def decode_bulk_info(raw: JsonObj) -> ResultE[tuple[BulkExportObj, BulkStatus]]:
    return smash.smash_result_2(decode_bulk_export(raw), decode_status_bulk(raw))


def transform_columns(bulk: BulkData) -> ResultE[FrozenList[JsonObj]]:
    bulk.file.seek(0)
    reader = csv.DictReader(bulk.file)
    rows: list[dict[str, str | None]] = list(reader)

    return JsonValueFactory.from_any(rows).bind(lambda v: Unfolder.to_list_of(v, Unfolder.to_json))
