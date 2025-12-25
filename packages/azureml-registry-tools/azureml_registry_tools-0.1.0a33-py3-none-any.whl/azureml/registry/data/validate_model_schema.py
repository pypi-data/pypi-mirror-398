# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Validate model schema."""

import argparse
import jsonschema
import sys
import yaml

from pathlib import Path
from typing import Any, Dict, List

import azureml.assets as assets
import azureml.assets.util as util
from azureml.assets.util import logger


def set_additional_properties_true(obj):
    """Recursively set additionalProperties to True in a schema object."""
    if isinstance(obj, dict):
        if "additionalProperties" in obj:
            obj["additionalProperties"] = True
        for v in obj.values():
            set_additional_properties_true(v)
    elif isinstance(obj, list):
        for item in obj:
            set_additional_properties_true(item)


def load_schema(schema_file: Path, allow_additional_properties: bool = False) -> Dict[str, Any]:
    """Load and optionally modify the schema to allow for additional properties.

    Args:
        schema_file (Path): Path to the schema file
        allow_additional_properties (bool): Whether to allow additional properties not defined in the schema

    Returns:
        dict: Loaded model schema
    """
    # Load schema from file
    with open(schema_file, 'r', encoding='utf-8') as file:
        schema = yaml.safe_load(file)

    if allow_additional_properties:
        logger.print('Allowing for additional properties, setting "additionalProperties: true" in the model schema')
        set_additional_properties_true(schema)

    return schema


def validate_model_schema(input_dirs: List[Path],
                          schema_file: Path,
                          asset_config_filename: str,
                          allow_additional_properties: bool = False,
                          changed_files: List[Path] = None) -> bool:
    """Validate model variant schema.

    Args:
        input_dirs (List[Path]): Directories containing assets.
        schema_file (Path): File containing model variant schema.
        asset_config_filename (str): Asset config filename to search for.
        allow_additional_properties (bool): Whether to allow additional properties not defined in schema.
        changed_files (List[Path], optional): List of changed files, used to filter assets. Defaults to None.

    Returns:
        bool: True on success.
    """
    # Load model schema from file
    loaded_schema = load_schema(schema_file, allow_additional_properties)

    # Create validator instance for collecting all errors
    validator = jsonschema.Draft7Validator(loaded_schema)

    # Gather list of just changed assets, for later filtering
    changed_assets = util.find_asset_config_files(input_dirs, asset_config_filename, changed_files) if changed_files else None  # noqa: E501

    asset_count = 0
    model_count = 0
    changed_model_count = 0
    error_count = 0
    for input_dir in input_dirs:
        # Recursively find all files with the name matching asset_config_filename
        for asset_config_path in util.find_asset_config_files(input_dir, asset_config_filename):
            asset_count += 1

            validate_this = changed_assets is None or asset_config_path in changed_assets

            try:
                asset_config = assets.AssetConfig(asset_config_path)
            except Exception as e:
                raise Exception(f"Error loading asset config from {asset_config_path}: {e}")

            file_path = asset_config.spec_with_path

            if asset_config.type == assets.AssetType.MODEL:
                model_count += 1

                if validate_this:
                    changed_model_count += 1
                    # Validate the file against the schema
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            spec_config = yaml.safe_load(f)

                        # Collect all validation errors
                        errors = list(validator.iter_errors(spec_config))

                        if not errors:
                            logger.print(f"{file_path} is valid.")
                        else:
                            logger.log_error(f"\n‼️{file_path} has {len(errors)} validation error(s):")

                            for e in errors:
                                # Get detailed error information for each error
                                error_path = '.'.join(str(p) for p in e.path) if e.path else "root"
                                line_info = ""

                                # Get line number from jsonschema error if available
                                if hasattr(e, 'lineno') and e.lineno is not None:
                                    line_info = f" at line {e.lineno}"
                                else:
                                    # Try to find line number by looking at the path and instance
                                    try:
                                        with open(file_path, "r", encoding="utf-8") as f:
                                            yaml_content = f.readlines()
                                            yaml_lines = []
                                            for idx, line in enumerate(yaml_content):
                                                if error_path in line:
                                                    yaml_lines.append(f"line {idx+1}: {line.strip()}")
                                            if yaml_lines:
                                                line_info = "\nPossible location(s):\n  " + "\n  ".join(yaml_lines)
                                    except Exception:
                                        pass

                                schema_path = '.'.join(str(p) for p in e.schema_path)
                                logger.print(f"⚠️ {file_path} is invalid at path '{error_path}'{line_info}:")
                                logger.print(f"  Error: {e.message}")
                                logger.print(f"  Instance: {e.instance}")
                                logger.print(f"  Schema path: {schema_path}")
                            error_count += 1
                    except Exception as e:
                        logger.log_error(f"Error processing {file_path}: {str(e)}")
                        error_count += 1

    logger.print(f"Found {asset_count} total asset(s).")
    if changed_assets is not None:
        logger.print(f"Found {error_count} model(s) with error(s) out of {changed_model_count} total changed model(s)")
    else:
        logger.print(f"Found {error_count} model(s) with error(s) out of {model_count} total model(s)")
    return error_count == 0


if __name__ == "__main__":
    # Handle command-line args
    parser = argparse.ArgumentParser(description="Validate model specifications against JSON schema")
    parser.add_argument("-i", "--input-dirs", required=True,
                        help="Comma-separated list of directories containing assets")
    parser.add_argument("-m", "--schema-file", default=Path(__file__).parent / "model.schema.json", type=Path,
                        help="Model Schema file")
    parser.add_argument("-a", "--asset-config-filename", default=assets.DEFAULT_ASSET_FILENAME,
                        help="Asset config file name to search for")
    parser.add_argument("--allow-additional-properties", action="store_true",
                        help="Allow additional properties not defined in the schema")
    parser.add_argument("-c", "--changed-files",
                        help="Comma-separated list of changed files, used to filter assets")
    args = parser.parse_args()

    # Convert comma-separated values to lists
    input_dirs = [Path(d) for d in args.input_dirs.split(",")]
    changed_files = [Path(f) for f in args.changed_files.split(",")] if args.changed_files else []

    # Validate against model schema
    success = validate_model_schema(input_dirs=input_dirs,
                                    schema_file=args.schema_file,
                                    asset_config_filename=args.asset_config_filename,
                                    allow_additional_properties=args.allow_additional_properties,
                                    changed_files=changed_files)

    if not success:
        sys.exit(1)
