from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from tomllib import load as toml_load
from typing import Any, cast
from urllib.parse import urlparse

from sisyphus_mirror.checks import is_rsync_rate_limit
from sisyphus_mirror.consts import (
    ARCH_LIST,
    BRANCH_LIST,
    DEFAULT_CONF_PATH,
    DEFAULT_SNAPSHOTS_LIMIT,
)
from sisyphus_mirror.errors import ConfigError
from sisyphus_mirror.typedefs import ConfigKW


@dataclass
class ConfigHandler:
    config_path: Path = DEFAULT_CONF_PATH

    def __post_init__(self) -> None:
        self.validator_map: dict[str, Callable[..., None]] = {
            "debug": self.validate_boolean,
            "dry_run": self.validate_boolean,
            "verbose": self.validate_boolean,
            "branch_list": partial(
                self.validate_literal_string_list, choices=BRANCH_LIST),
            "source_url": self.validate_rsync_url,
            "working_dir": self.validate_exist_path,
            "arch_list": partial(
                self.validate_literal_string_list, choices=ARCH_LIST),
            "linkdest_list": self.validate_exist_path_list,
            "include_files": self.validate_string_list,
            "exclude_files": self.validate_string_list,
            "snapshot_limit": partial(
                self.validate_min_integer, min_value=DEFAULT_SNAPSHOTS_LIMIT),
            "rate_limit": self.validate_rsync_rate_limit,
            "conn_timeout": partial(self.validate_min_integer, min_value=0),
            "io_timeout": partial(self.validate_min_integer, min_value=0),
        }

    def run(self) -> ConfigKW:
        loaded = self.load_options()
        normalized = self.normalize_options(loaded)
        return self.validate_options(normalized)

    def load_options(self) -> dict[str, Any]:
        if not self.config_path.exists():
            if self.config_path != DEFAULT_CONF_PATH:
                msg = (
                    f"{self.config_path}: No such file or directory"
                    "or permission denied."
                )
                raise ConfigError(msg)
            return {}

        with self.config_path.open("rb") as file:
            file_dict = toml_load(file)
        if not isinstance(file_dict, dict):
            msg = (
                f"Configuration file {self.config_path} must contain "
                f"a TOML table (dictionary). Got: {file_dict}."
            )
            raise ConfigError(msg)

        if "sisyphus-mirror" in file_dict and "sisyphus_mirror" not in file_dict:
            file_dict["sisyphus_mirror"] = file_dict.pop("sisyphus-mirror", None)

        if not (config_options := file_dict.get("sisyphus_mirror", None)):
            msg = f"Not found [sisyphus-mirror] section in {self.config_path}"
            raise ConfigError(msg)
        if not isinstance(config_options, dict):
            msg = f"sisyphus-mirror is not a valid section in {self.config_path}"
            raise ConfigError(msg)
        return config_options

    def normalize_options(self, options: dict[str, Any]) ->  dict[str, Any]:
        options = {key.replace("-", "_"): value for key,value in options.items()}
        if working_dir := options.get("working_dir"):
            options["working_dir"] = Path(working_dir)
        if linkdest_list := options.get("linkdest_list"):
            options["linkdest_list"] = [Path(linkdest) for linkdest in linkdest_list]
        return options

    def validate_options(self, options: dict[str, Any]) -> ConfigKW:
        for option_name, option_value in options.items():
            if (validator := self.validator_map.get(option_name)):
                    validator(option_name, option_value)
            else:
                msg = f"{self.config_path}: unexpected option {option_name}"
                raise ConfigError(msg)
        return cast("ConfigKW", options)

    def validate_boolean(self, option_name: str, option_value: Any) -> None:
        if not isinstance(option_value, bool):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                f"Type must be boolean (true or false). "
                "Got: {option_value}."
            )
            raise ConfigError(msg)

    def validate_exist_path(self, option_name: str, option_value: Any) -> None:
        if not isinstance(option_value, Path):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Type must be file path string. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        if not option_value.exists():
            msg = (
                f'{self.config_path}: option "{option_name}". '
                f"Path does not exist or permission denied. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)

    def validate_exist_path_list(self, option_name: str, option_value: Any) -> None:
        if not isinstance(option_value, list):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Type must be array of file path strings. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        for index, item in enumerate(option_value):
            if not isinstance(item, Path):
                msg = (
                    f'{self.config_path}: option "{option_name}". '
                    f"Item #{index} must be a file path string. "
                    f"Got: {item}."
                )
                raise ConfigError(msg)
            if not item.exists():
                msg = (
                    f'{self.config_path}: option "{option_name}". '
                    f"Item #{index}: Path does not exist or permission denied. "
                    f"Got: {item}."
                )
                raise ConfigError(msg)

    def validate_literal_string_list(
        self,
        option_name: str,
        option_value: Any,
        choices: Sequence[Any],
    ) -> None:
        allowed_values = '", "'.join(choices)  # python3.10
        if not isinstance(option_value, list):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                f'Type must be array of strings. '
                f'Allowed values: "{allowed_values}". '
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        for index, item in enumerate(option_value):
            if not isinstance(item, str):
                msg = (
                    f'{self.config_path}: option "{option_name}". '
                    f'item #{index} must be string. '
                    f'Allowed values: "{allowed_values}". '
                    f'Got: {item}.'
                )
                raise ConfigError(msg)
            if item not in choices:
                msg = (
                    f'{self.config_path}: option "{option_name}". '
                    f'Item #{index} must be one of "{allowed_values}". '
                    f"Got: {item}."
                )
                raise ConfigError(msg)

    def validate_min_integer(
        self,
        option_name: str,
        option_value: Any,
        min_value: int = 1,
    ) -> None:
        if not isinstance(option_value, int):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Type must be integer. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        if option_value < min_value:
            msg = (
                f'{self.config_path}: option "{option_name}". '
                f"Value must be >= {min_value}. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)

    def validate_string_list(self, option_name: str, option_value: Any) -> None:
        if not isinstance(option_value, list):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Type must be array of strings. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        for index, item in enumerate(option_value):
            if not isinstance(item, str):
                msg = (
                    f'{self.config_path}: option "{option_name}". '
                    f'Item #{index} must be string. '
                    f"Got: {item}."
                )
                raise ConfigError(msg)

    def validate_rsync_rate_limit(self, option_name: str, option_value: Any) -> None:
        if not is_rsync_rate_limit(option_value):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                'Must be integer (512) or string ("1.5m"). '
                f"Got: {option_value}."
            )
            raise ConfigError(msg)

    def validate_rsync_url(self, option_name: str, option_value: Any) -> None:
        if not isinstance(option_value, str):
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Type must be string. "
                f"Got: {option_value}."
            )
            raise ConfigError(msg)
        if urlparse(option_value).scheme != "rsync":
            msg = (
                f'{self.config_path}: option "{option_name}". '
                "Value must have rsync:// URL scheme. "
                f"Got: {option_value}."
                f'Example: "rsync://example.com/path".'
            )
            raise ConfigError(msg)
