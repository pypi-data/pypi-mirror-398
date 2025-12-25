# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Create or update assets."""

import azure
import copy
import json
import os
import re
import tempfile
import yaml
from git import InvalidGitRepositoryError, Repo
from pathlib import Path
from typing import List, Union

from azure.ai.ml import MLClient, load_component, load_data, load_model
from azure.ai.ml.entities._component.component import Component
from azure.ai.ml.entities._assets._artifacts.data import Data
from azure.ai.ml.entities._assets._artifacts.model import Model
from azure.identity import DefaultAzureCredential
import azureml.assets as assets

from azureml.registry.tools.config import AssetType, AssetSpec
from azureml.registry.tools.registry_utils import RegistryUtils
from azureml.registry.tools.repo2registry_config import Repo2RegistryConfig


def get_diff_files(base_commit: str,
                   target_commit: str) -> List[str]:
    """Run git diff to compare changes from base to target commit.

    Args:
        base_commit (str): Commit to be compared against.
        target_commit (str): Commit to be compared to the base_commit.

    Returns:
        List[str]: Names of files changed from base to target commit.
    """
    print("Base and/or target commit argument(s) provided, checking for Github repository.")
    try:
        repo = Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise Exception(f"Could not find a repository in current or parent directories: {e}")

    print(f"Found .git folder: {Path(repo.git_dir).as_posix()}")

    repo.git.execute(["git", "fetch", "origin"])

    base_commit_type = repo.git.execute(["git", "cat-file", "-t", base_commit])
    target_commit_type = repo.git.execute(["git", "cat-file", "-t", target_commit])

    # Validate type of both commit arguments
    if base_commit_type != "commit":
        raise Exception(f"Base commit argument {base_commit} is an invalid commit")
    if target_commit_type != "commit":
        raise Exception(f"Target commit argument {target_commit} is an invalid commit")

    print("Finding changed files using git diff")
    diff_files = repo.git.execute(["git", "diff", base_commit, target_commit, "--name-only"])

    # Each file in diff_files is relative to parent directory of the .git dir
    parent_dir = os.path.abspath(os.path.join(repo.git_dir, ".."))
    diff_files = diff_files.split("\n")
    diff_files = [Path(parent_dir, f).as_posix() for f in diff_files]

    return diff_files


def find_assets(input_dir: Path,
                base_commit: str = None,
                target_commit: str = None,
                asset_filter: re.Pattern = None) -> List[assets.AssetConfig]:
    """Search directories for assets.

    Args:
        input_dir (Path): Directory to search in.
        base_commit (str): Commit to be compared against for detecting file changes.
        target_commit (str): Commit to be compared to the base_commit for detecting file changes.
        asset_filter (re.Pattern): Regex pattern used to filter assets.
    """
    filename_pattern = re.compile(r'(environment|component|model|data)\.yaml$')
    found_assets = []
    found_changed_file = False

    # Only if there's a base/target commit, check the git diff
    changed_files = get_diff_files(base_commit, target_commit) if base_commit or target_commit else None
    if changed_files == []:
        print("No changed files found using git diff")
        return []

    print(f"Finding assets inside {input_dir}")

    for file in input_dir.rglob("*.yaml"):
        resolved_file = Path(file.resolve()).as_posix()
        is_changed_file = resolved_file in changed_files if changed_files else None
        filename_match = filename_pattern.match(file.name)

        if filename_match:
            if is_changed_file is False:
                continue
            found_changed_file = True
            try:
                asset_spec = AssetSpec(file, filename_match.group(1))
            except Exception as e:
                raise Exception(f"Failed to create AssetSpec object for {resolved_file}: {e}")

            if asset_filter is not None and not asset_filter.fullmatch(asset_spec.full_name):
                continue

            found_assets.append(asset_spec)

    if asset_filter and len(found_assets) == 0 and found_changed_file:
        print(f"No assets found with the asset filter {asset_filter}. Please verify your filter regex can match assets with the format "
              f"<type>/<name>/<version>, where asset type is component, data, environment, model.")
    elif len(found_assets) == 0:
        print("No assets were found.")
    else:
        print(f"Found assets: {[asset.full_name for asset in found_assets]}")

    return found_assets


def merge_yamls(existing_asset_file_name: str,
                updated_asset: AssetSpec) -> dict:
    """Preserve storage value from existing asset to updated asset.

    Args:
        existing_asset_file_name (str): Name of file containing details of asset currently in registry.
        updated_asset (AssetSpec): AssetSpec containing updated asset info.
    Returns:
        dict: Merged asset data.
    """
    with open(existing_asset_file_name, "r", encoding="utf-8") as existing_asset_file, open(updated_asset.file_name_with_path, "r", encoding="utf-8") as updated_asset_file:
        existing_asset_dict = yaml.safe_load(existing_asset_file)
        updated_asset_dict = yaml.safe_load(updated_asset_file)

    merged_asset = copy.deepcopy(updated_asset_dict)

    if updated_asset.type == AssetType.MODEL or updated_asset.type == AssetType.DATA:
        storage_key = "path"
        # "path" is always required for models, use the existing value
        if existing_asset_dict.get(storage_key) != updated_asset_dict.get(storage_key):
            print(f'"{storage_key}" is immutable, using existing value from asset in registry: {existing_asset_dict[storage_key]}')
            merged_asset[storage_key] = existing_asset_dict[storage_key]
    elif updated_asset.type == AssetType.COMPONENT:
        storage_key = "code"
        if existing_asset_dict.get(storage_key) is None and updated_asset_dict.get(storage_key) is not None:
            print(f'"{storage_key}" is immutable and cannot be added. Please create a new version to include "{storage_key}"')
        elif existing_asset_dict.get(storage_key) != updated_asset_dict.get(storage_key):
            print(f'"{storage_key}" is immutable, using existing value from asset in registry: {existing_asset_dict[storage_key]}')
            merged_asset[storage_key] = existing_asset_dict[storage_key]

    return merged_asset


def merge_assets(existing_asset: Union[Component, Data, Model],
                 asset: AssetSpec):
    """Prepare asset for update by preserving storage value from existing asset.

    Args:
        existing_asset (Union[Component, Data, Model]): Asset currently in registry.
        asset (AssetSpec): AssetSpec containing updated asset info.
    """
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as existing_asset_temp_file:
        existing_asset_temp_file_name = existing_asset_temp_file.name

    existing_asset.dump(existing_asset_temp_file_name)

    merged_result = merge_yamls(existing_asset_temp_file_name, asset)

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as merged_asset_temp_file:
        merged_asset_temp_file_name = merged_asset_temp_file.name

    with open(merged_asset_temp_file_name, "w", encoding="utf-8") as merged_asset_temp_file:
        merged_asset_temp_file.write(yaml.dump(merged_result, allow_unicode=True))

    if asset.type == AssetType.MODEL:
        merged_asset = load_model(merged_asset_temp_file_name)
    elif asset.type == AssetType.DATA:
        merged_asset = load_data(merged_asset_temp_file_name)
    elif asset.type == AssetType.COMPONENT:
        merged_asset = load_component(merged_asset_temp_file_name)

    asset.set_asset_obj_to_create_or_update(merged_asset)

    os.remove(existing_asset_temp_file_name)
    os.remove(merged_asset_temp_file_name)


def write_results(results_dict: dict,
                  output_json_file_name: str,
                  found_assets: List[AssetSpec],
                  dry_run: bool):
    """Write asset create/update results to JSON output file.

    Args:
        results_dict (dict): Results from asset create_or_update operations.
        output_json_file_name (str): File name of JSON to write results to.
        found_assets (List[AssetSpec]): List of assets found in input directories.
        dry_run (bool): Dry run flag.
    """
    for asset in found_assets:
        if asset.full_name not in results_dict:
            if dry_run:
                results_dict[asset.full_name] = {"DryRunCreateOrUpdateStatus": "NOT RUN", "Operation": "None", "Logs": ""}
            else:
                results_dict[asset.full_name] = {"CreateOrUpdateStatus": "NOT RUN", "Operation": "None", "Logs": ""}

    # Produce JSON output on status and diffs
    print("\nAsset create_or_update results:")
    print(json.dumps(results_dict, indent=2))
    with open(output_json_file_name, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
        print(f"Wrote asset create_or_update results to file {output_json_file_name}")


def resolve_from_parent_folder(input_folder: Path) -> Path:
    """Resolve repo2registry.cfg using parent folder.

    Args:
        input_folder (Path): Folder to check for repo2registry.cfg.

    Returns:
        Path: Folder containing repo2registry.cfg if found, otherwise None.
    """
    if os.path.exists(os.path.join(input_folder, "repo2registry.cfg")):
        return input_folder
    if os.path.abspath(input_folder) == os.path.abspath(os.sep):
        return None
    return resolve_from_parent_folder(os.path.dirname(input_folder))


def create_or_update_assets(input_dir: Path,
                            repo2registry_config_file_name: Path,
                            output_json_file_name: Path,
                            base_commit: str = None,
                            target_commit: str = None,
                            asset_filter: re.Pattern = None,
                            dry_run: bool = False):
    """Create or update assets.

    Args:
        input_dir (Path): Directory to search in.
        repo2registry_config (Path): Config file containing registry info.
        base_commit (str): Commit to be compared against for detecting file changes.
        target_commit (str): Commit to be compared to the base_commit for detecting file changes.
        output_json_file_name (Path): File name of JSON to write results to.
        asset_filter (re.Pattern): Regex pattern used to filter assets.
        dry_run (bool): Dry run flag.
    """
    if input_dir is None:
        print(f"Input directory not specified, using current working directory: {os.getcwd()}")
        input_dir = Path(os.getcwd())

    if repo2registry_config_file_name is not None:
        print(f"Using repo2registry.cfg file specified at path: {Path(repo2registry_config_file_name).resolve()} for all assets")
        repo2registry_config = Repo2RegistryConfig(repo2registry_config_file_name)
    else:
        # If path to repo2registry.cfg file is unspecified, resolve cfg file starting at input_dir
        print("No config file specified as an argument, resolving repo2registry.cfg file")

        input_dir_abs_path = input_dir.resolve().as_posix()
        repo2registry_config_folder = resolve_from_parent_folder(input_dir_abs_path)
        if repo2registry_config_folder is None:
            raise Exception(f"Could not find repo2registry.cfg file in any parent folders of {input_dir_abs_path}")

        repo2registry_file_path = os.path.join(repo2registry_config_folder, 'repo2registry.cfg')
        repo2registry_abs_file_path = Path(repo2registry_file_path).resolve().as_posix()
        print(f"Found repo2registry.cfg file in {repo2registry_abs_file_path}")
        repo2registry_config = Repo2RegistryConfig(repo2registry_file_path)

    ml_client = MLClient(
        subscription_id=repo2registry_config.subscription_id,
        resource_group_name=repo2registry_config.resource_group,
        registry_name=repo2registry_config.registry_name,
        credential=DefaultAzureCredential(),  # CodeQL [SM05139] DefaultAzureCredential should only be used for local development and testing purposes.
    )

    results_dict = {}
    found_assets = find_assets(input_dir, base_commit, target_commit, asset_filter)

    try:
        for asset in found_assets:
            print(f"\nPreparing {asset.full_name} for create/update")

            # Check if asset/version has already been created
            print(f"Attempting to find {asset.full_name} in {repo2registry_config.registry_name}")
            existing_asset = None
            try:
                operations = RegistryUtils.get_operations_from_type(asset.type, ml_client=ml_client)
                existing_asset = operations.get(name=asset.name, version=asset.version)
                operation_str = "Update"
                print(f"{asset.full_name} already exists. Preparing to {operation_str.upper()} asset.")
            except azure.core.exceptions.ResourceNotFoundError:
                operation_str = "Create"
                print(f"{asset.full_name} does not exist. Preparing to {operation_str.upper()} asset.")
            except Exception as e:
                if dry_run:
                    results_dict[asset.full_name] = {"DryRunCreateOrUpdateStatus": "NOT RUN", "Operation": "None", "Logs": f"{e}"}
                else:
                    results_dict[asset.full_name] = {"CreateOrUpdateStatus": "NOT RUN", "Operation": "None", "Logs": f"{e}"}
                if repo2registry_config.continue_on_asset_failure:
                    continue
                else:
                    raise

            if existing_asset:
                if asset.type in [AssetType.COMPONENT, AssetType.DATA, AssetType.MODEL]:
                    try:
                        merge_assets(existing_asset, asset)
                    except Exception as e:
                        print(f"Failed to prepare {asset.full_name} for create_or_update: {e}")
                        if dry_run:
                            results_dict[asset.full_name] = {"DryRunCreateOrUpdateStatus": "NOT RUN", "Operation": f"{operation_str}", "Logs": f"{e}"}
                        else:
                            results_dict[asset.full_name] = {"CreateOrUpdateStatus": "NOT RUN", "Operation": f"{operation_str}", "Logs": f"{e}"}
                        if repo2registry_config.continue_on_asset_failure:
                            continue
                        else:
                            raise

            try:
                print(f"[{operation_str.upper()}] Running create_or_update on {asset.full_name}")
                if not dry_run:
                    operations.create_or_update(asset.asset_obj_to_create_or_update)
                    print(f"Completed create_or_update for {asset.full_name}")
                    results_dict[asset.full_name] = {"CreateOrUpdateStatus": "SUCCESS", "Operation": f"{operation_str}", "Logs": ""}
                else:
                    results_dict[asset.full_name] = {"DryRunCreateOrUpdateStatus": "SUCCESS", "Operation": f"{operation_str}", "Logs": ""}
            except Exception as e:
                print(f"Failed create_or_update for {asset.full_name}: {e}")
                results_dict[asset.full_name] = {"CreateOrUpdateStatus": "FAILED", "Operation": f"{operation_str}", "Logs": f"{e}"}
                if repo2registry_config.continue_on_asset_failure:
                    continue
                else:
                    raise

    except Exception:
        write_results(results_dict, output_json_file_name, found_assets, dry_run)
        raise Exception("Errors occurred while creating/updating assets")

    write_results(results_dict, output_json_file_name, found_assets, dry_run)
