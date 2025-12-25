# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Repo2RegistryConfig class."""

import configparser
from pathlib import Path


class Repo2RegistryConfig:
    """Repo2RegistryConfig class."""

    def __init__(self, repo2registry_config_file_name: str):
        """Repo2RegistryConfig init.

        Args:
            repo2registry_config_file (Path): Path of repo2registry config file.
        """
        if not Path(repo2registry_config_file_name).is_file():
            raise FileNotFoundError(f"File '{repo2registry_config_file_name.resolve().as_posix()}' does not exist.")

        config = configparser.ConfigParser()
        config.read(repo2registry_config_file_name)

        self._validate_schema(config, repo2registry_config_file_name)

        self._subscription_id = config["registry"]["subscription_id"]
        self._resource_group = config["registry"]["resource_group"]
        self._registry_name = config["registry"]["registry_name"]
        self._continue_on_asset_failure = self._get_bool_value(config["settings"]["continue_on_asset_failure"])

    def _get_bool_value(self, value) -> bool:
        return value.lower() == "true"

    def _value_is_bool(self, value) -> bool:
        return value.lower() in ("true", "false")

    def _validate_schema(self, config, repo2registry_config_file_name):
        """Validate repo2registry config schema."""
        if not config.has_section("registry"):
            raise Exception(f'"registry" section not found in config file {repo2registry_config_file_name}')
        if not config.has_section("settings"):
            raise Exception(f'"settings" section not found in config file {repo2registry_config_file_name}')

        if not config.has_option("registry", "subscription_id"):
            raise Exception(f'Key "subscription_id" not found under "registry" section in config file {repo2registry_config_file_name}')
        if not config.has_option("registry", "resource_group"):
            raise Exception(f'Key "resource_group" not found under "registry" section in config file {repo2registry_config_file_name}')
        if not config.has_option("registry", "registry_name"):
            raise Exception(f'Key "registry_name" not found under "registry" section in config file {repo2registry_config_file_name}')

        if not config.has_option("settings", "continue_on_asset_failure"):
            raise Exception(f'Key "continue_on_asset_failure" not found under "settings" section in config file {repo2registry_config_file_name}')
        if not self._value_is_bool(config["settings"]["continue_on_asset_failure"]):
            raise Exception(f'Key "continue_on_asset_failure" under "settings" section must be a boolean in config file {repo2registry_config_file_name}')

    @property
    def subscription_id(self) -> str:
        """Subscription id."""
        return self._subscription_id

    @property
    def resource_group(self) -> str:
        """Resource group."""
        return self._resource_group

    @property
    def registry_name(self) -> str:
        """Registry name."""
        return self._registry_name

    @property
    def continue_on_asset_failure(self) -> bool:
        """Continue on asset failure."""
        return self._continue_on_asset_failure


def create_repo2registry_config(registry_name: str, subscription: str, resource_group: str, repo2registry_config_file_name: Path,
                                continue_on_asset_failure: str):
    """Create repo2registry config.

    Args:
        registry_name (str): Registry name.
        subscription (str): Registry subscription id.
        resource_group (str): Registry resource group.
        repo2registry_config_file_name (Path): Path to config file.
        continue_on_asset_failure (str): Whether to continue creating/updating remaining assets when asset creation/update fails.
    """
    print("Creating repo2registry config...")

    repo2registry_config = configparser.ConfigParser()
    repo2registry_config.add_section("registry")
    repo2registry_config.set("registry", "registry_name", registry_name)
    repo2registry_config.set("registry", "subscription_id", subscription)
    repo2registry_config.set("registry", "resource_group", resource_group)

    # Set default settings
    repo2registry_config.add_section("settings")
    repo2registry_config.set("settings", "continue_on_asset_failure", continue_on_asset_failure)

    # Write to path
    with open(repo2registry_config_file_name, "w", encoding="utf-8") as repo2registry_config_file:
        repo2registry_config.write(repo2registry_config_file)

    repo2registry_cfg_abs_path = Path(repo2registry_config_file_name).resolve().as_posix()

    print(f"Wrote repo2registry config file to {repo2registry_cfg_abs_path}")
