from pathlib import Path

from sisyphus_mirror.mirror import BranchMirror


def test_branch_mirror_paths() -> None:
    branch = "Sisyphus"
    custom_home = Path("/custom-path")

    instance = BranchMirror(
        branch="Sisyphus", branch_list=["Sisyphus"], working_dir=custom_home)

    assert instance.last_symlink == custom_home / branch
    assert instance.partial_dir == custom_home / ".partial" / branch


def test_branch_mirror_rsync_cmd() -> None:
    branch = "Sisyphus"
    custom_home = Path("/custom-path")

    instance = BranchMirror(
        branch="Sisyphus", branch_list=["Sisyphus"], working_dir=custom_home)

    rsync_cmd = instance.prepare_rsync_cmd()
    assert rsync_cmd == [
        "rsync",
        "-rltmvH",
        "--delete-delay",
        "--delete-excluded",
        "--stats",
        "--chmod=Du+w",
        "--exclude=*debuginfo*",
        "--exclude=SRPMS",
        "--include=list/**",
        "--include=.timestamp",
        "--include=noarch/**",
        "--include=x86_64/**",
        "--include=x86_64-i586/**",
        "--include=*/",
        "--exclude=*",
        "--bwlimit=5m",
        "--contimeout=60",
        "--timeout=600",
        f"--partial-dir={custom_home}/.partial/{branch}",
        f"rsync://ftp.altlinux.org/ALTLinux/{branch}/branch",
        f"{custom_home}/.snapshots/__{branch}_UNCOMPLETE__/"]
