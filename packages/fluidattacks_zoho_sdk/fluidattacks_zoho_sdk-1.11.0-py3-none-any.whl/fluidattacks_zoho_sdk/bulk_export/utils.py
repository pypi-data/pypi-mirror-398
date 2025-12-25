import logging
import tempfile
from typing import IO
from zipfile import ZipFile

from fa_purity import Cmd, Result, ResultE, cast_exception
from pure_requests.retry import sleep_cmd
from requests import Response

from .core import (
    BulkData,
    BulkExportId,
    BulkStatus,
    FileName,
    MustRestart,
    NonTerminalStatus,
    ShouldRetry,
)

LOG = logging.getLogger(__name__)


def _top_truncation(value: float, limit: float) -> float:
    if value > limit:
        return limit
    return value


def _waiting_msg(job: BulkExportId, time: float) -> Cmd[None]:
    return Cmd.wrap_impure(
        lambda: LOG.info("Waiting bulk export %s to be ready (%s)", job.id_bulk, int(time)),
    )


def _wait_job(retry: int, job: BulkExportId) -> Cmd[None]:
    wait_time = _top_truncation(60 * retry, 5 * 50)
    return _waiting_msg(job, wait_time) + sleep_cmd(wait_time)


def _handle_status(status_bulk: BulkStatus) -> ResultE[BulkStatus]:
    if status_bulk == BulkStatus.COMPLETED:
        return Result.success(status_bulk)
    if status_bulk in NonTerminalStatus:
        return Result.failure(ShouldRetry(status_bulk))
    return Result.failure(MustRestart(status_bulk))


def unzip_data(response: Response, file_name: FileName) -> Cmd[ResultE[BulkData]]:
    def _action() -> ResultE[BulkData]:
        # pylint: disable=consider-using-with
        # need refac of BulkData for enabling the above check
        name_file = file_name.name
        tmp_zipdir = tempfile.mkdtemp()
        file_zip: IO[bytes] = tempfile.NamedTemporaryFile(mode="wb+")  # noqa: SIM115
        file_unzip: IO[str] = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")  # noqa: SIM115
        file_zip.write(response.content)
        file_zip.seek(0)
        LOG.debug("Unzipping file")
        with ZipFile(file_zip, "r") as zip_obj:
            files = zip_obj.namelist()

            if name_file not in files:
                err = ValueError(f"Expected  {name_file} file. Decompressed {len(files)} files.")
                return Result.failure(cast_exception(err))
            zip_obj.extract(name_file, tmp_zipdir)
        LOG.debug("Generating BulkData")
        with open(tmp_zipdir + f"/{name_file}", encoding="UTF-8") as unzipped:  # noqa: PTH123
            file_unzip.write(unzipped.read())
        LOG.debug("Unzipped size: %s", file_unzip.tell())
        return Result.success(BulkData(file_unzip))

    return Cmd.wrap_impure(_action)
