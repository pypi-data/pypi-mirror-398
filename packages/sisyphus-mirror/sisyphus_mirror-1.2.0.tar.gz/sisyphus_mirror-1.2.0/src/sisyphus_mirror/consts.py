from pathlib import Path
from typing import get_args

from sisyphus_mirror.typedefs import ArchT, BranchT

APP_NAME = "Sysiphus Mirror"
ARCH_LIST = get_args(ArchT)
BRANCH_LIST = get_args(BranchT)
DEFAULT_CONF_PATH = Path("/etc/sisyphus-mirror/default.toml")
DEFAULT_SOURCE = "rsync://ftp.altlinux.org/ALTLinux"
DEFAULT_HOME_PATH = Path("/srv/mirrors/altlinux")
DEFAULT_ARCH: list[ArchT] = ["noarch", "x86_64", "x86_64-i586"]
DEFAULT_INCLUDE_FILES = ["list/**", ".timestamp"]
DEFAULT_EXCLUDE_FILES = ["*debuginfo*", "SRPMS"]
DEFAULT_SNAPSHOTS_LIMIT = 1
DEFAULT_RATE_LIMIT: int | str = "5m"
DEFAULT_CONN_TIMEOUT: int = 60
DEFAULT_IO_TIMEOUT: int = 600
