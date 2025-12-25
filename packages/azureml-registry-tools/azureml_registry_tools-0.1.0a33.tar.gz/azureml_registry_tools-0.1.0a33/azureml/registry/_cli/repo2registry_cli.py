# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import argparse
import re
from pathlib import Path

from azureml.registry.tools.repo2registry_config import create_repo2registry_config
from azureml.registry.tools.create_or_update_assets import create_or_update_assets


def validate_json_extension(output_json_file_name) -> Path:
    """Validate if output file name provided is a .json file."""
    output_json_file_path = Path(output_json_file_name)
    if not output_json_file_path.suffix == ".json":
        raise argparse.ArgumentTypeError(f"--output-json arg {output_json_file_name} must have a .json extension")
    return output_json_file_path


def validate_repo2registry_cfg(cfg_file_name) -> Path:
    """Validate if output file name provided is a .cfg file."""
    cfg_file_path = Path(cfg_file_name)
    if not cfg_file_path.suffix == ".cfg":
        raise argparse.ArgumentTypeError(f"--repo2registry-config arg {cfg_file_name} must be a path to a .cfg file")
    return cfg_file_path


def validate_continue_on_asset_failure_bool_str(bool_arg) -> str:
    """Validate if continue_on_asset_failure arg can be converted to a boolean."""
    if bool_arg.lower() not in ("true", "false"):
        raise argparse.ArgumentTypeError(f"--continue-on-asset-failure arg {bool_arg} must be a boolean (True or False)")

    return bool_arg.capitalize()


def main():
    """Repo2Registry CLI tool."""
    # Handle command-line args
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("-i", "--input-dir", type=Path,
                               help="Directory containing assets to create/update")
    update_parser.add_argument("-c", "--repo2registry-config", type=validate_repo2registry_cfg,
                               help="Config containing info of registry to publish to")
    update_parser.add_argument("-o", "--output-json", type=validate_json_extension, required=True,
                               help="Output JSON file to write create/update results")
    update_parser.add_argument("-d", "--dry-run", action="store_true",
                               help="Dry run, don't actually create/update assets", default=False)
    update_parser.add_argument("-f", "--filter", type=re.compile,
                               help="Regex pattern to select assets to create/update, in the format <type>/<name>/<version>")

    update_parser.add_argument("--git", action="store_true",
                               help="Use git commits to detect file changes", default=False)
    update_parser.add_argument("-b", "--base-commit",
                               help="Base git commit for finding file changes")
    update_parser.add_argument("-t", "--target-commit",
                               help="Target git commit for finding file changes")

    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--registry-name", type=str, required=True,
                               help="Name of registry to create/update assets")
    config_parser.add_argument("--subscription", type=str, required=True,
                               help="Subscription id of registry")
    config_parser.add_argument("-g", "--resource_group", type=str, required=True,
                               help="Name of registry resource group")
    config_parser.add_argument("-c", "--repo2registry-config", type=validate_repo2registry_cfg, default=Path("repo2registry.cfg"),
                               help="Config to write info of registry to publish to. Defaults to repo2registry.cfg")
    config_parser.add_argument("--continue-on-asset-failure", default="False", type=validate_continue_on_asset_failure_bool_str,
                               help="Continue creating/updating remaining assets when asset creation/update fails. Defaults to False.")

    args = parser.parse_args()

    if args.command == "config":
        create_repo2registry_config(registry_name=args.registry_name,
                                    subscription=args.subscription,
                                    resource_group=args.resource_group,
                                    repo2registry_config_file_name=args.repo2registry_config,
                                    continue_on_asset_failure=args.continue_on_asset_failure)
    elif args.command == "update":
        if (args.git or args.base_commit or args.target_commit) and not (args.git and args.base_commit and args.target_commit):
            parser.error("When using git, --git, --base-commit, and --target-commit are all required.")
        if args.dry_run:
            print("Dry run option was selected. No assets will be created or updated.")

        create_or_update_assets(input_dir=args.input_dir,
                                repo2registry_config_file_name=args.repo2registry_config,
                                output_json_file_name=args.output_json,
                                base_commit=args.base_commit,
                                target_commit=args.target_commit,
                                asset_filter=args.filter,
                                dry_run=args.dry_run)


if __name__ == '__main__':
    main()
