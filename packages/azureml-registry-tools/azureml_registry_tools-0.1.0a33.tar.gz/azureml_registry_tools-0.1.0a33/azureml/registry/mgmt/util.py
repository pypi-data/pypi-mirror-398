"""File resolution utilities for asset management."""

import os
from pathlib import Path, PurePath
from typing import Tuple, Union, Any

import azureml.assets as assets  # noqa: E402


def is_file_relative_to_asset_path(asset: assets.AssetConfig, value: Any) -> bool:
    """Check if the value is a file with respect to the asset path.

    Args:
        asset (AssetConfig): the asset to try and resolve the value for
        value: value to check

    Returns:
        bool: True if value represents a file relative to asset path, False otherwise
    """
    if not isinstance(value, str) and not isinstance(value, PurePath):
        return False

    path_value = value if isinstance(value, Path) else Path(value)

    if not path_value.is_relative_to(asset.file_path):
        path_value = asset._append_to_file_path(path_value)

    return os.path.isfile(path_value)


def resolve_from_file_for_asset(asset: assets.AssetConfig, value: Any) -> Any:
    """Resolve the value from a file for an asset if it is a file, otherwise returns the value.

    Args:
        asset (AssetConfig): the asset to try and resolve the value for
        value: value to try and resolve

    Returns:
        Any: File content if value is a file path relative to asset, otherwise the original value
    """
    if not is_file_relative_to_asset_path(asset, value):
        return value

    path_value = value if isinstance(value, Path) else Path(value)

    if not path_value.is_relative_to(asset.file_path):
        path_value = asset._append_to_file_path(path_value)

    is_resolved_from_file, resolved_value = _resolve_from_file(path_value)

    if is_resolved_from_file:
        return resolved_value
    else:
        return value


def _resolve_from_file(value: Union[str, Path]) -> Tuple[bool, Union[str, None]]:
    """Resolve file content (internal helper).

    Args:
        value: File path to resolve

    Returns:
        Tuple[bool, Union[str, None]]: (success, content) where success indicates
                                       if file was read and content is the file content
    """
    if os.path.isfile(value):
        try:
            with open(value, 'r', encoding='utf-8') as f:
                content = f.read()
                return (True, content)
        except Exception as e:
            raise Exception(f"Failed to read file {value}: {e}")
    else:
        return (False, None)
