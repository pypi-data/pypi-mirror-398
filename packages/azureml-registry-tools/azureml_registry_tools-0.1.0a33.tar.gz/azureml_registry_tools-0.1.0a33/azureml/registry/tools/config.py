# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Asset spec classes."""

from enum import Enum
from pathlib import Path
from ruamel.yaml import YAML
from typing import Union

from azure.ai.ml import load_component, load_data, load_environment, load_model
from azure.ai.ml.entities import Component, Data, Environment, Model

FULL_ASSET_NAME_TEMPLATE = "{type}/{name}/{version}"


class ValidationException(Exception):
    """Validation errors."""


class AssetType(Enum):
    """Asset type."""

    COMPONENT = 'component'
    DATA = 'data'
    ENVIRONMENT = 'environment'
    MODEL = 'model'


class AssetSpec:
    """Asset spec."""

    def __init__(self, file_name: str, asset_type: str):
        """Asset spec init."""
        with open(file_name, "r", encoding="utf-8") as f:
            self._yaml = YAML().load(f)

        self._file_name_with_path = Path(file_name)
        self._file_name = Path(file_name).name
        self._file_path = Path(file_name).parent

        self._asset_type = asset_type
        self._asset_obj = None
        self._asset_obj_to_create_or_update = None
        self._repo2registry_config = None

        self._validate()

        if self.type == AssetType.COMPONENT:
            self._asset_obj = load_component(source=file_name)
        elif self.type == AssetType.DATA:
            self._asset_obj = load_data(source=file_name)
        elif self.type == AssetType.ENVIRONMENT:
            self._asset_obj = load_environment(source=file_name)
        elif self.type == AssetType.MODEL:
            self._asset_obj = load_model(source=file_name)

        if self._asset_obj is None:
            raise ValidationException(f"Asset type {self.type} is not supported")

    def _validate(self):
        """Validate asset spec."""
        if self.version is None:
            raise ValidationException("Version not found in spec. Please specify version.")

    @property
    def file_name(self) -> str:
        """Name of config file."""
        return self._file_name

    @property
    def file_name_with_path(self) -> Path:
        """Location of config file."""
        return self._file_name_with_path

    @property
    def file_path(self) -> Path:
        """Directory containing config file."""
        return self._file_path

    @property
    def type(self) -> AssetType:
        """Asset type."""
        return AssetType(self._asset_type)

    @property
    def name(self) -> str:
        """Asset name."""
        return self._yaml.get('name')

    @property
    def version(self) -> str:
        """Asset version."""
        version = self._yaml.get('version')
        return str(version) if version is not None else None

    @property
    def full_name(self) -> str:
        """Full asset name, including type and version."""
        return FULL_ASSET_NAME_TEMPLATE.format(type=self.type.value, name=self.name, version=self.version)

    @property
    def asset_obj(self) -> Union[Component, Data, Environment, Model]:
        """Asset loaded using load_*(component, data, environment, model) method."""
        return self._asset_obj

    @property
    def asset_obj_to_create_or_update(self) -> Union[Component, Data, Environment, Model]:
        """Asset to create_or_update."""
        if self._asset_obj_to_create_or_update:
            return self._asset_obj_to_create_or_update
        return self._asset_obj

    def set_asset_obj_to_create_or_update(self, asset_obj):
        """Set asset to create_or_update."""
        self._asset_obj_to_create_or_update = asset_obj
