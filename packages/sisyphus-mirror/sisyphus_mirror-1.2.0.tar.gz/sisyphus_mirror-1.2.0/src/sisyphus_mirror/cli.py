from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from sisyphus_mirror.checks import is_rsync_rate_limit
from sisyphus_mirror.consts import (
    ARCH_LIST,
    BRANCH_LIST,
    DEFAULT_ARCH,
    DEFAULT_CONF_PATH,
    DEFAULT_CONN_TIMEOUT,
    DEFAULT_EXCLUDE_FILES,
    DEFAULT_HOME_PATH,
    DEFAULT_INCLUDE_FILES,
    DEFAULT_IO_TIMEOUT,
    DEFAULT_RATE_LIMIT,
    DEFAULT_SNAPSHOTS_LIMIT,
    DEFAULT_SOURCE,
)
from sisyphus_mirror.errors import CommandError
from sisyphus_mirror.typedefs import CLIArgsT


def handle_cli_options(
    args: Sequence[str] | None = None,  # for pytest
) -> CLIArgsT:
    parser = ArgumentParser()

    add_arg = partial(parser.add_argument, default=SUPPRESS)
    add_flag = partial(add_arg, action="store_true")

    add_arg("-c", "--config", type=Path,
        help=f"Path to TOML configuration file. Defaults: {DEFAULT_CONF_PATH}.")

    add_flag("-n", "--dry-run", help="Perform a trial run without making changes.")

    add_flag("-v", "--verbose", help="Enable verbose mode with detailed output.")

    add_flag("-d", "--debug", help=("Enable debug mode."))

    add_arg("-b", "--branch-list", choices=BRANCH_LIST, nargs="*",
        help="Explicitly defined repository branches.")

    add_arg("-s", "--source-url",
        help=f"Repository source URL. Defaults: {DEFAULT_SOURCE}.")

    add_arg("-w", "--working-dir", type=Path, help=(
        "Working directory for snapshots and temporary synchronization data. "
        f"Defaults: {DEFAULT_HOME_PATH}."))

    add_arg("-a", "--arch-list", choices=ARCH_LIST, nargs="*",
        help=f"Target CPU architectures. Defaults: {DEFAULT_ARCH}.")

    add_arg("-L", "--linkdest-list", type=Path, nargs="*",
        help="Paths to additional hard-link sources.")

    add_arg("-I", "--include-files", nargs="*", help=(
        "File patterns to include during synchronization. "
        f"Defaults: {DEFAULT_INCLUDE_FILES}."))

    add_arg("-E", "--exclude-files", nargs="*", help=(
        "File patterns to exclude from synchronization. "
        f"Defaults: {DEFAULT_EXCLUDE_FILES}."))

    add_arg("-S", "--snapshot-limit", type=int, help=(
        "Maximum number of snapshots to keep. Must be >= 1. "
        f"Defaults: {DEFAULT_SNAPSHOTS_LIMIT}."))

    add_arg("-R", "--rate-limit",
            help=f"limit socket I/O bandwidth. Defaults: {DEFAULT_RATE_LIMIT}.")

    add_arg("--conn-timeout", type=int,
        help=f"Connection timeout in seconds. Defaults: {DEFAULT_CONN_TIMEOUT}.")

    add_arg("--io-timeout", type=int,
        help=f"I/O timeout in seconds. Defaults: {DEFAULT_IO_TIMEOUT}.")

    cli_options = vars(parser.parse_args(args))

    linkdest_list: list[Path] = cli_options.get("linkdest_list", [])
    for linkdest in linkdest_list:
        if not linkdest.exists():
            msg = (
                f"CLI option -L / --linkdest-list: path `{linkdest}` does not exist or "
                "permission denied."
            )
            raise CommandError(msg)

    snapshot_limit = cli_options.get("snapshot_limit")
    if isinstance(snapshot_limit, int) and snapshot_limit < 1:
        msg = (
            "CLI option -S or --snapshot-limit must be >= 1. "
            f"Got: {snapshot_limit}."
        )
        raise CommandError(msg)

    rate_limit = cli_options.get("rate_limit")
    if isinstance(rate_limit, str) and not is_rsync_rate_limit(rate_limit):
        msg = (
            f'CLI option -R --rate-limit '
            'must be integer (512) or string ("1.5m"). '
            f"Got: {rate_limit}."
        )
        raise CommandError(msg)

    conn_timeout = cli_options.get("conn_timeout")
    if isinstance(conn_timeout, int) and conn_timeout < 0:
        msg = (
            "CLI option --conn-timeout must be >= 0. "
            f"Got: {conn_timeout}."
        )
        raise CommandError(msg)

    io_timeout = cli_options.get("io_timeout")
    if isinstance(io_timeout, int) and io_timeout < 0:
        msg = (
            "CLI option --io-timeout must be >= 0. "
            f"Got: {io_timeout}."
        )
        raise CommandError(msg)

    return cli_options  # type: ignore[return-value]
