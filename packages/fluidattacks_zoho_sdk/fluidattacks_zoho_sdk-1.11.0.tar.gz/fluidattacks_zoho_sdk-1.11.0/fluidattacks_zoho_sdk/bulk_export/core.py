from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import IO, Final, final

from fa_purity import Cmd, FrozenList, ResultE
from fa_purity.json import JsonObj
from fluidattacks_etl_utils.handle_errors import handle_value_error


@dataclass(frozen=True)
class BulkExportId:
    id_bulk: str


@dataclass(frozen=True)
class ViewId:
    id_bulk: str


@dataclass(frozen=True)
class ModuleName:
    module: str


@final
class BulkStatus(Enum):
    QUEUED = "QUEUED"
    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

    @staticmethod
    def from_raw(raw: str) -> ResultE[BulkStatus]:
        return handle_value_error(lambda: BulkStatus(raw))


NonTerminalStatus: Final[tuple[BulkStatus, ...]] = (
    BulkStatus.QUEUED,
    BulkStatus.IN_PROGRESS,
    BulkStatus.INITIATED,
)
TerminalStatus: Final[tuple[BulkStatus, ...]] = (
    BulkStatus.CANCELLED,
    BulkStatus.FAILED,
    BulkStatus.EXPIRED,
)


@dataclass(frozen=True)
class BulkExportObj:
    id_bulk: BulkExportId
    module: str


@dataclass(frozen=True)
class BulkEndpoint:
    route: str


@dataclass(frozen=True)
class ShouldRetry(Exception):
    status: BulkStatus


@dataclass(frozen=True)
class MustRestart(Exception):
    status: BulkStatus


@dataclass(frozen=True)
class BulkClient:
    create_bulk: Callable[
        [ModuleName, BulkEndpoint],
        Cmd[ResultE[tuple[BulkExportObj, BulkStatus]]],
    ]
    get_status: Callable[[BulkExportObj], Cmd[ResultE[tuple[BulkExportObj, BulkStatus]]]]
    download_bulk: Callable[[BulkExportObj, FileName], Cmd[ResultE[BulkData]]]
    fetch_bulk: Callable[
        [ModuleName, BulkEndpoint, FileName],
        Cmd[ResultE[FrozenList[JsonObj]]],
    ]


@dataclass(frozen=True)
class BulkData:
    file: IO[str]


@dataclass(frozen=True)
class FileName:
    name: str
