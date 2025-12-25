from arch_lint.dag import (
    DagMap,
)
from arch_lint.graph import (
    FullPathModule,
)
from fluidattacks_etl_utils.typing import (
    Dict,
    FrozenSet,
    NoReturn,
    TypeVar,
)

_T = TypeVar("_T")


def raise_or_return(item: _T | Exception) -> _T | NoReturn:
    if isinstance(item, Exception):
        raise item
    return item


def _module(path: str) -> FullPathModule | NoReturn:
    return raise_or_return(FullPathModule.from_raw(path))


_dag: Dict[str, tuple[tuple[str, ...] | str, ...]] = {
    "fluidattacks_zoho_sdk": (
        ("zoho_desk"),
        ("auth", "_http_client", "bulk_export", "_decoders"),
        "ids",
    ),
    "fluidattacks_zoho_sdk.auth": (
        ("_access", "_refresh", "_revoke"),
        "_decode",
        "_core",
    ),
    "fluidattacks_zoho_sdk._http_client": (
        "_client",
        "paginate",
        "_core",
    ),
    "fluidattacks_zoho_sdk.bulk_export": (
        "_client",
        "_decode",
        "utils",
        "core",
    ),
    "fluidattacks_zoho_sdk.zoho_desk": (
        "_client",
        "_decode",
        "core",
    ),
}


def project_dag() -> DagMap:
    return raise_or_return(DagMap.new(_dag))


def forbidden_allowlist() -> Dict[FullPathModule, FrozenSet[FullPathModule]]:
    _raw: Dict[str, FrozenSet[str]] = {}
    return {_module(k): frozenset(_module(i) for i in v) for k, v in _raw.items()}
