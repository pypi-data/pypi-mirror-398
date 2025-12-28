from logging import Logger
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

BranchT = Literal["c10f2", "p10", "p11", "Sisyphus"]
ArchT = Literal["aarch64", "armh", "i586", "noarch", "x86_64", "x86_64-i586"]


class CommonKW(TypedDict):
    dry_run: NotRequired[bool]
    verbose: NotRequired[bool]
    debug: NotRequired[bool]

    branch_list: NotRequired[list[BranchT]]
    working_dir: NotRequired[Path]
    source_url: NotRequired[str]
    arch_list: NotRequired[list[ArchT]]
    linkdest_list: NotRequired[list[Path]]

    include_files: NotRequired[list[str]]
    exclude_files: NotRequired[list[str]]

    snapshot_limit: NotRequired[int]
    rate_limit: NotRequired[int | str]
    conn_timeout: NotRequired[int]
    io_timeout: NotRequired[int]

    logger: NotRequired[Logger]


class CLIArgsT(CommonKW):
    config: NotRequired[Path]


class ConfigKW(CommonKW):
    ...


class RepoMirrorKW(CommonKW):
    ...


class BranchMirrorKW(CommonKW):
    branch: NotRequired[BranchT]
