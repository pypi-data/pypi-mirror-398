from pathlib import Path

import pytest

from sisyphus_mirror.cli import handle_cli_options
from sisyphus_mirror.consts import (
    ARCH_LIST,
    BRANCH_LIST,
)
from sisyphus_mirror.errors import CommandError
from sisyphus_mirror.typedefs import ArchT, BranchT


@pytest.mark.parametrize("branch", BRANCH_LIST)
def test_cli_branch_list_one_valid(branch: BranchT) -> None:
    expected = {"branch_list": [branch]}
    assert handle_cli_options(["-b", branch]) == expected
    assert handle_cli_options(["--branch-list", branch]) == expected


def test_cli_branch_list_all_valid() -> None:
    expected = {"branch_list": list(BRANCH_LIST)}
    assert handle_cli_options(["-b", *BRANCH_LIST]) == expected
    assert handle_cli_options(["--branch-list", *BRANCH_LIST]) == expected


@pytest.mark.parametrize("arch_list", ARCH_LIST)
def test_cli_arch_list_one_valid(arch_list: ArchT) -> None:
    expected = {"arch_list": [arch_list]}
    assert handle_cli_options(["-a", arch_list]) == expected
    assert handle_cli_options(["--arch-list", arch_list]) == expected


def test_cli_arch_list_all_valid() -> None:
    expected = {"arch_list": list(ARCH_LIST)}

    assert handle_cli_options(["-a", *ARCH_LIST]) == expected
    assert handle_cli_options(["--arch-list", *ARCH_LIST]) == expected


def test_cli_linkdest_list_all_valid() -> None:
    user_snapshots = ["src", "tests"]
    expected = {"linkdest_list": [Path(e) for e in user_snapshots]}

    assert handle_cli_options(["-L", *user_snapshots]) == expected
    assert handle_cli_options(["--linkdest-list", *user_snapshots]) == expected


@pytest.mark.parametrize("snapshot_limit", ["-1", "0"])
def test_cli_snapshot_limit_invalid(snapshot_limit: str) -> None:
    with pytest.raises(CommandError):
        handle_cli_options(["-S", snapshot_limit])
    with pytest.raises(CommandError):
        handle_cli_options(["--snapshot-limit", snapshot_limit])


@pytest.mark.parametrize("rate_limit", ["-1", "1.5", "1.m", ""])
def test_cli_rate_limit_invalid(rate_limit: str) -> None:
    with pytest.raises(CommandError):
        handle_cli_options(["-R", rate_limit])
    with pytest.raises(CommandError):
        handle_cli_options(["--rate-limit", rate_limit])


@pytest.mark.parametrize("io_timeout", ["-1"])
def test_cli_io_timeout_invalid(io_timeout: str) -> None:
    with pytest.raises(CommandError):
        handle_cli_options(["--io-timeout", io_timeout])


@pytest.mark.parametrize("conn_timeout", ["-1"])
def test_cli_conn_timeout_invalid(conn_timeout: str) -> None:
    with pytest.raises(CommandError):
        handle_cli_options(["--conn-timeout", conn_timeout])
