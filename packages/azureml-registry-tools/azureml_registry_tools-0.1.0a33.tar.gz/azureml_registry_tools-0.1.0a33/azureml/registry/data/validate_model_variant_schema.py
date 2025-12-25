# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Validate model variant schema."""

import argparse
import yaml
import sys
import jsonschema
from jsonschema import validate
from pathlib import Path
from typing import List

import azureml.assets as assets
import azureml.assets.util as util
from azureml.assets.util import logger


def validate_model_variant_schema(input_dirs: List[Path],
                                  model_variant_schema_file: Path,
                                  asset_config_filename: str) -> bool:
    """Validate model variant schema.

    Args:
        input_dirs (List[Path]): Directories containing assets.
        model_variant_schema_file (Path): File containing model variant schema.
        asset_config_filename (str): Asset config filename to search for.

    Returns:
        bool: True on success.
    """
    # Load variantInfo schema from file
    model_variant_info_schema = {}
    with open(model_variant_schema_file, 'r', encoding="utf-8") as file:
        model_variant_info_schema = yaml.safe_load(file)

    asset_count = 0
    model_count = 0
    error_count = 0
    for input_dir in input_dirs:
        for asset_config in util.find_assets(input_dir, asset_config_filename):
            asset_count += 1
            if asset_config.type == assets.AssetType.MODEL:
                model_count += 1
                # Extract model variant info from spec
                variant_info = None
                with open(asset_config.spec_with_path, "r", encoding="utf-8") as f:
                    spec_config = yaml.safe_load(f)
                    variant_info = spec_config.get("variantInfo")

                if variant_info is not None:
                    logger.print(f"Found variantInfo in spec {asset_config.spec_with_path}. "
                                 f"Validating variantInfo against schema: {variant_info}")
                    # Validate data
                    try:
                        validate(instance=variant_info, schema=model_variant_info_schema)
                        logger.print("variantInfo is valid.")
                    except jsonschema.exceptions.ValidationError as e:
                        logger.log_error(f"variantInfo is invalid for {asset_config.spec_with_path}: {e.message}")
                        error_count += 1

    logger.print(f"Found {asset_count} total asset(s).")
    logger.print(f"Found {error_count} model(s) with error(s) out of {model_count} total model(s)")
    return error_count == 0


if __name__ == "__main__":
    # Handle command-line args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dirs", required=True, help="Comma-separated list of directories containing assets")
    parser.add_argument("-m", "--model-variant-schema-file", default=Path(__file__).parent / "model-variant.schema.json", type=Path, help="Model Variant Schema file")
    parser.add_argument("-a", "--asset-config-filename", default=assets.DEFAULT_ASSET_FILENAME, help="Asset config file name to search for")
    args = parser.parse_args()

    # Convert comma-separated values to lists
    input_dirs = [Path(d) for d in args.input_dirs.split(",")]

    # Validate variantInfo against model variant schema
    success = validate_model_variant_schema(input_dirs=input_dirs,
                                            model_variant_schema_file=args.model_variant_schema_file,
                                            asset_config_filename=args.asset_config_filename)

    if not success:
        sys.exit(1)
