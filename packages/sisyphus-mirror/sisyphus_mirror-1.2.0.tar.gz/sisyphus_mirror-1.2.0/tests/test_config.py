from pathlib import Path

import pytest

from sisyphus_mirror.config import ConfigHandler
from sisyphus_mirror.consts import (
    ARCH_LIST,
    DEFAULT_ARCH,
    DEFAULT_CONF_PATH,
    DEFAULT_HOME_PATH,
    DEFAULT_SOURCE,
)
from sisyphus_mirror.errors import ConfigError


@pytest.fixture
def config_handler() -> ConfigHandler:
    return ConfigHandler(config_path=DEFAULT_CONF_PATH)


def test_config_handler_load_options(config_handler: ConfigHandler) -> None:
    config_handler.config_path = Path("not-exists-file-path")
    with pytest.raises(ConfigError):
        config_handler.load_options()


def test_config_handler_normalize_options(config_handler: ConfigHandler) -> None:
    unnormalized = {
        "working-dir": str(DEFAULT_HOME_PATH),
        "linkdest_list": ["user-snapshot-1", "user-snapshot-2"],
    }
    normalized = {
        "working_dir": DEFAULT_HOME_PATH,
        "linkdest_list": [Path("user-snapshot-1"), Path("user-snapshot-2")],
    }
    result = config_handler.normalize_options(unnormalized)
    assert result == normalized


def test_config_handler_validate_boolean(config_handler: ConfigHandler) -> None:
    assert config_handler.validate_boolean(
        option_name="option_name", option_value=True,
    ) is None
    assert config_handler.validate_boolean(
        option_name="option_name", option_value=False,
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_boolean(
            option_name="option_name", option_value=None,
        )


def test_config_handler_validate_literal_string_list(
    config_handler: ConfigHandler,
) -> None:
    assert config_handler.validate_literal_string_list(
        option_name="option_name", option_value=DEFAULT_ARCH, choices=ARCH_LIST,
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_literal_string_list(
            option_name="option_name", option_value=None, choices=ARCH_LIST,
        )
    with pytest.raises(ConfigError):
        config_handler.validate_literal_string_list(
            option_name="option_name", option_value=[None], choices=ARCH_LIST,
        )
    with pytest.raises(ConfigError):
        config_handler.validate_literal_string_list(
            option_name="option_name", option_value=["UNKNOWN"], choices=ARCH_LIST,
        )


def test_config_handler_validate_min_integer(config_handler: ConfigHandler) -> None:
    assert config_handler.validate_min_integer(
        option_name="option_name", option_value=2, min_value=1,
    ) is None
    assert config_handler.validate_min_integer(
        option_name="option_name", option_value=1, min_value=1,
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_min_integer(
            option_name="option_name", option_value=0, min_value=1,
        )


def test_config_handler_validate_exist_path(config_handler: ConfigHandler) -> None:
    assert config_handler.validate_exist_path(
        option_name="option_name", option_value=Path("/"),
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_exist_path(
            option_name="option_name", option_value=None,
        )


def test_config_handler_validate_rsync_rate_limit(
    config_handler: ConfigHandler,
) -> None:
    assert config_handler.validate_rsync_rate_limit(
        option_name="option_name", option_value=0,
    ) is None
    assert config_handler.validate_rsync_rate_limit(
        option_name="option_name", option_value=512,
    ) is None
    assert config_handler.validate_rsync_rate_limit(
        option_name="option_name", option_value="512",
    ) is None
    assert config_handler.validate_rsync_rate_limit(
        option_name="option_name", option_value="1m",
    ) is None
    assert config_handler.validate_rsync_rate_limit(
        option_name="option_name", option_value="1.5m",
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_rsync_rate_limit(
            option_name="option_name", option_value=-1,
        )
    with pytest.raises(ConfigError):
        config_handler.validate_rsync_rate_limit(
            option_name="option_name", option_value="1.5",
        )

def test_config_handler_validate_rsync_url(config_handler: ConfigHandler) -> None:
    assert config_handler.validate_rsync_url(
        option_name="option_name", option_value=DEFAULT_SOURCE,
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_rsync_url(
            option_name="option_name", option_value="http://example.com",
        )

def test_config_handler_validate_string_list(config_handler: ConfigHandler) -> None:
    assert config_handler.validate_string_list(
        option_name="option_name", option_value=["a", "b", "c"],
    ) is None
    with pytest.raises(ConfigError):
        config_handler.validate_string_list(
            option_name="option_name", option_value=None,
        )
    with pytest.raises(ConfigError):
        config_handler.validate_string_list(
            option_name="option_name", option_value=[None],
        )
