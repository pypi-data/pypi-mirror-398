import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger, getLogger
from os import chdir
from pathlib import Path
from typing import Unpack

from sisyphus_mirror.consts import (
    DEFAULT_ARCH,
    DEFAULT_CONN_TIMEOUT,
    DEFAULT_EXCLUDE_FILES,
    DEFAULT_HOME_PATH,
    DEFAULT_INCLUDE_FILES,
    DEFAULT_IO_TIMEOUT,
    DEFAULT_RATE_LIMIT,
    DEFAULT_SNAPSHOTS_LIMIT,
    DEFAULT_SOURCE,
)
from sisyphus_mirror.logger import get_logger
from sisyphus_mirror.typedefs import ArchT, BranchT, RepoMirrorKW


def repo_mirroring(**kwargs: Unpack[RepoMirrorKW]) -> None:
    logger = kwargs.get("logger", getLogger(__name__))

    if working_dir := kwargs.get("working_dir"):
        chdir(working_dir)

    if not (branch_list := kwargs.get("branch_list")):
        msg = (
            "You must set branches in CLI arguments or config options.\n\n"
            "Command line example:\n\n"
            "sisyphus-mirror -b p11\n\n"
            "Config example:\n\n"
            "[sisyphus-mirror]\n"
            'branch_list = ["p11"]'
        )
        raise ValueError(msg)

    for branch in branch_list:
        logger.info(f"{branch=} synchronization started.")
        branch_sync = BranchMirror(
            branch=branch,
            **kwargs,
        )
        branch_sync.run()


@dataclass()
class BranchMirror:
    branch: BranchT
    branch_list: list[BranchT]
    dry_run: bool = False
    verbose: bool = False
    debug: bool = False
    source_url: str = DEFAULT_SOURCE
    working_dir: Path = DEFAULT_HOME_PATH
    arch_list: list[ArchT] = field(default_factory=lambda: DEFAULT_ARCH)
    linkdest_list: list[Path] = field(default_factory=list)
    include_files: list[str] = field(default_factory=lambda: DEFAULT_INCLUDE_FILES)
    exclude_files: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_FILES)
    snapshot_limit: int = DEFAULT_SNAPSHOTS_LIMIT
    rate_limit: int | str = DEFAULT_RATE_LIMIT
    conn_timeout: int = DEFAULT_CONN_TIMEOUT
    io_timeout: int = DEFAULT_IO_TIMEOUT
    logger: Logger = get_logger(__name__)
    new_snapshot: Path | None = field(init=False)

    def __post_init__(self) -> None:
        self.flag = self.working_dir/f".snapshots/__{self.branch}_IN_PROCESS__"
        self.last_symlink = self.working_dir/self.branch
        self.partial_dir = self.working_dir/".partial"/self.branch
        self.snapshots_dir = self.working_dir/".snapshots"
        self.dest_dir = self.snapshots_dir/f"__{self.branch}_UNCOMPLETE__"
        self.new_snapshot = None

    def run(self) -> None:
        self.logger.info(f"Branch {self.branch} mirror run")
        try:
            if not self.dry_run:
                self.check_or_make_subdirs()
                self.check_branch_lock()
                self.set_branch_lock()
            self.sync_with_source()
            if not self.dry_run:
                self.complete_snapshot()
                self.update_stable_link()
                self.delete_old_snapshots()
        finally:
            if not self.dry_run:
                self.unset_branch_lock()

    def check_or_make_subdirs(self) -> None:
        self.logger.info("Check or make subdirectories.")
        for subdir in (
            self.dest_dir,
            self.partial_dir,
            self.snapshots_dir,
        ):

            self.logger.info(f"Check or make subdirectory: {subdir}.")
            subdir.mkdir(parents=True, exist_ok=True)

    def check_branch_lock(self) -> None:
        self.logger.info("Check branch lock")
        if self.flag.exists():
            msg = (
                "Another synchronization is in progress "
                f"(flag file exists: {self.flag})."
            )
            raise OSError(msg)

    def set_branch_lock(self) -> None:
        self.logger.info("Set branch lock")
        self.flag.touch(exist_ok=True)

    @property
    def snapshot_map(self) -> dict[BranchT, list[Path]]:
        snapshot_map: dict[BranchT, list[Path]] = {}
        for branch in self.branch_list:
            branch_snapshots = [
                path for path in self.working_dir.glob(f".snapshots/{branch}-*")
                if path.is_dir()
            ]
            oldest_first = sorted(branch_snapshots)
            snapshot_map[branch] = oldest_first
        return snapshot_map

    @property
    def link_dest_paths(self) -> list[Path]:
        paths: list[Path] = []

        if current_snapshots := self.snapshot_map.get(self.branch):
            paths.append(current_snapshots[-1])

        paths.extend(self.linkdest_list)

        for other_branch in self.branch_list:
            if other_branch != self.branch:
                if other_snapshots := self.snapshot_map.get(other_branch):
                    paths.append(other_snapshots[-1])

        return paths[:20]

    def prepare_rsync_cmd(self) -> list[str]:
        rsync_cmd = [
            "rsync",
            "-rltmvH",
            "--delete-delay",
            "--delete-excluded",
            "--stats",
            "--chmod=Du+w",  # permissions for self.delete_old_snapshots()
            *[f"--exclude={pattern}" for pattern in self.exclude_files],
            *[f"--include={pattern}" for pattern in self.include_files],
            *[f"--include={pattern}/**" for pattern in self.arch_list],
            "--include=*/",
            "--exclude=*",
        ]
        if self.dry_run:
            rsync_cmd.append("--dry-run")

        if self.verbose:
            rsync_cmd.append("--progress")

        if self.rate_limit:
            rsync_cmd.append(f"--bwlimit={self.rate_limit}")

        if self.conn_timeout:
            rsync_cmd.append(f"--contimeout={self.conn_timeout}")

        if self.io_timeout:
            rsync_cmd.append(f"--timeout={self.io_timeout}")

        if not self.dry_run:
            rsync_cmd.extend([
                f"--link-dest={link_dest}"
                for link_dest in self.link_dest_paths
            ])
            rsync_cmd.append(f"--partial-dir={self.partial_dir}")

        rsync_cmd.append(f"{self.source_url}/{self.branch}/branch")

        if not self.dry_run:
            rsync_cmd.append(f"{self.dest_dir}/")

        self.logger.debug(f"rsync command:\n{' \\\n    '.join(rsync_cmd)}")

        return rsync_cmd

    def sync_with_source(self) -> None:
        rsync_cmd = self.prepare_rsync_cmd()
        self.logger.info("rsync process start")
        for _ in range(3):
            result = subprocess.run(rsync_cmd, check=False, text=True)
            if result.returncode == 0:
                break
        else:
            msg = "Synchronization failed"
            raise RuntimeError(msg)

    def complete_snapshot(self) -> None:
        if self.dest_dir.exists():
            datetime_string = datetime.now().strftime("%Y%m%d%H%M%S%f")
            self.new_snapshot = self.snapshots_dir/f"{self.branch}-{datetime_string}"
            self.logger.info(f"complete snapshot {self.new_snapshot}")
            self.dest_dir.rename(self.new_snapshot)

    def update_stable_link(self) -> None:
        self.logger.info(
            f"update stable link {self.last_symlink} to {self.new_snapshot}")
        if self.new_snapshot is None:
            msg = "New snapshot attribute not set"
            raise RuntimeError(msg)
        if not self.new_snapshot.exists():
            msg = f"New snapshot {self.new_snapshot} not found"
            raise RuntimeError(msg)
        last_snapshot = self.snapshot_map[self.branch][-1]
        if self.new_snapshot != last_snapshot:
            msg = (
                f"A new snapshot {self.new_snapshot}"
                f"is not a last snapshot {last_snapshot}"
            )
            raise RuntimeError(msg)
        relative_path = Path(".snapshots") / self.new_snapshot.name  # for rsyncd chroot
        subprocess.run(["ln", "-nsf", relative_path, self.last_symlink], check=True)

    def delete_old_snapshots(self) -> None:
        if self.snapshot_limit < 1:
            msg = (
                "Snapshot limit must be >= 1. "
                f"Got: {self.snapshot_limit}."
            )
            raise ValueError(msg)
        oldest_first = self.snapshot_map[self.branch]
        stop_delete = 0 - self.snapshot_limit  # negative stop index
        snapshots_to_delete = oldest_first[:stop_delete]
        for dir_ in snapshots_to_delete:
            self.logger.info(f"Delete old snapshot: {dir_}")
            shutil.rmtree(dir_)

    def unset_branch_lock(self) -> None:
        if self.flag.exists():
            self.logger.info("Unset branch lock")
            self.flag.unlink()
