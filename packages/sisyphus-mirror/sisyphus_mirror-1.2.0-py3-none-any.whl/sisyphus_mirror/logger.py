import logging
from logging import DEBUG, INFO, WARNING, Logger, getLogger

_configured = False

def setup_logging(*, debug: bool = False, verbose: bool = False) -> None:
    global _configured
    if _configured:
        return

    if debug:
        level = DEBUG
    elif verbose:
        level = INFO
    else:
        level = WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
    _configured = True


def get_logger(name: str) -> Logger:
    return getLogger(name)
