from logging import Logger

from sisyphus_mirror.cli import handle_cli_options
from sisyphus_mirror.config import ConfigHandler
from sisyphus_mirror.consts import DEFAULT_CONF_PATH
from sisyphus_mirror.logger import get_logger, setup_logging
from sisyphus_mirror.mirror import repo_mirroring
from sisyphus_mirror.typedefs import CLIArgsT, ConfigKW


def main(logger: Logger = get_logger(__name__)) -> None:
    cli_options = handle_cli_options()

    config_path = cli_options.pop("config", DEFAULT_CONF_PATH)
    config_options = ConfigKW()

    config_handler = ConfigHandler(config_path)
    config_options = config_handler.run()

    # instead of dict.update() for type checkers
    options: CLIArgsT | ConfigKW = {
        **config_options,
        **cli_options,
    }
    debug = options.pop("debug", False)
    verbose = options.get("verbose", False)
    setup_logging(
        debug=debug,
        verbose=verbose,
    )
    logger.info("Started.")
    logger.debug(f"Merged options: {options}")
    repo_mirroring(**options)


if __name__ == "__main__":
    main()
