# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Asset management commands for registry-mgmt CLI."""

import requests
import sys
import shutil
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import List

from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

from azureml.registry.data.validate_model_schema import validate_model_schema
from azureml.registry.data.validate_model_variant_schema import validate_model_variant_schema
from azureml.registry._rest_client.registry_management_client import RegistryManagementClient
from azureml.registry.mgmt.util import resolve_from_file_for_asset

# Cross-platform compatibility patch - must be applied before importing azureml.assets
import os
from subprocess import run


def patched_run_command(cmd: List[str]):
    """Run command with OS-appropriate shell setting for cross-platform compatibility."""
    # Use shell=True on Windows, shell=False on Unix-like systems
    use_shell = os.name == 'nt'  # 'nt' is Windows
    result = run(cmd, capture_output=True, encoding=sys.stdout.encoding, errors="ignore", shell=use_shell)
    return result


# Apply patch before importing azureml.assets
import azureml.assets.publish_utils as publish_utils  # noqa: E402
publish_utils.run_command = patched_run_command

import azureml.assets as assets  # noqa: E402
import azureml.assets.util as util  # noqa: E402
from azureml.assets.config import AssetConfig, AssetType  # noqa: E402
from azureml.assets.publish_utils import create_asset  # noqa: E402
from azureml.assets.validate_assets import validate_assets  # noqa: E402

# Set azcopy job plan location to avoid permission issues
os.environ.setdefault("AZCOPY_JOB_PLAN_LOCATION", tempfile.gettempdir())


def validate_model(asset_path: Path, allow_additional_properties: bool = False) -> bool:
    """Validate model.

    Args:
        asset_path (Path): Path to the asset folder to validate
        allow_additional_properties (bool): Whether to allow additional properties not defined in schema

    Returns:
        bool: True if validation passes, False otherwise
    """
    errors = 0

    print("⚙️ [VALIDATION #1]: Validate assets...")
    if not validate_assets(asset_path, assets.DEFAULT_ASSET_FILENAME):
        print("❌ [FAILED] Validation #1: validate_assets\n\n")
        errors += 1
    else:
        print("✅ [PASSED] Validation #1: validate_assets passed\n")

    # Model variant schema validation
    model_variant_schema_file = Path(__file__).parent.parent / "data" / "model-variant.schema.json"

    print("⚙️ [VALIDATION #2]: Validating model variant schema...")
    if not validate_model_variant_schema(input_dirs=[asset_path], model_variant_schema_file=model_variant_schema_file,
                                         asset_config_filename=assets.DEFAULT_ASSET_FILENAME):
        print("❌ [FAILED] Validation #2: validate_model_variant_schema\n")
        errors += 1
    else:
        print("✅ [PASSED] Validation #2: validate_model_variant_schema passed\n")

    # Model schema validation
    model_schema_file = Path(__file__).parent.parent / "data" / "model.schema.json"

    print("⚙️ [VALIDATION #3]: Validating model schema...")
    if not validate_model_schema(input_dirs=[asset_path], schema_file=model_schema_file,
                                 asset_config_filename=assets.DEFAULT_ASSET_FILENAME,
                                 allow_additional_properties=allow_additional_properties):
        print("❌ [FAILED] Validation #3: validate_model_schema\n")
        errors += 1
    else:
        print("✅ [PASSED] Validation #3: validate_model_schema passed\n")

    if errors != 0:
        return False

    print("🎉 [VALIDATION COMPLETE] All validations passed!\n")
    return True


def put_system_metadata(ml_client: MLClient, asset: AssetConfig, registry: str, system_metadata: dict):
    """PUT system metadata for an asset.

    Args:
        ml_client (MLClient): ML client.
        asset (AssetConfig): Asset config.
        registry (str): Name of registry.
        system_metadata (dict): System metadata payload.
    """
    # First, transform system metadata such that any files are read and their content used
    system_metadata = {k: resolve_from_file_for_asset(asset, v) for k, v in system_metadata.items()}

    # Use RegistryManagementClient for discovery
    registry_mgmt_client = RegistryManagementClient(registry_name=registry)
    discovery = registry_mgmt_client.discovery()

    # Extract the needed components
    base_url = discovery.get('registryFqdns', {}).get(discovery.get('primaryRegion', '').lower(), {}).get('uri')
    subscription_id = discovery.get('subscriptionId')
    resource_group = discovery.get('resourceGroup')

    # Build the URL
    mms_id = f"{asset.name}:{asset.version}"
    url = (f"{base_url}/modelregistry/v1.0/subscriptions/{subscription_id}/resourceGroups/{resource_group}/"
           f"providers/Microsoft.MachineLearningServices/registries/{registry}/models/{mms_id}/systemMetadata")

    # Get token and make request
    access_token = ml_client._credential.get_token("https://ml.azure.com").token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    print("Attempting to PUT system metadata")
    print(f"System Metadata Payload: {system_metadata}")

    response = requests.put(url, headers=headers, json=system_metadata)

    if response.status_code in [200, 201, 202]:
        print("PUT request successful")
        return response.json()
    else:
        print(f"PUT request failed: {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.reason}")
        print(f"Content: {response.text}")
        raise Exception(response.reason)


def build_mutable_asset(base_asset: AssetConfig, mutable_asset_dir: str, override_storage: bool = False) -> AssetConfig:
    """Build a mutable copy of the asset in a temporary directory.

    Args:
        base_asset (AssetConfig): Base asset configuration to copy
        mutable_asset_dir (str): Directory path for the mutable asset copy
        override_storage (bool, optional): If True, model config will be modified to reference a local temp file.

    Returns:
        AssetConfig: Mutable asset configuration object
        system_metadata_payload (dict): Extracted system metadata from asset spec
    """
    common_dir, _ = util.find_common_directory(base_asset.release_paths)

    # Convert string paths to Path objects and ensure they're absolute
    common_dir = Path(common_dir).resolve()
    mutable_asset_dir = Path(mutable_asset_dir).resolve()
    base_asset_file = base_asset.file_name_with_path.resolve()
    base_spec_file = base_asset.spec_with_path.resolve()
    base_model_file = base_asset.extra_config_with_path.resolve()

    shutil.copytree(common_dir, mutable_asset_dir, dirs_exist_ok=True)

    # Reference asset files in mutable directory
    asset_config_file = mutable_asset_dir / base_asset_file.relative_to(common_dir)
    spec_config_file = mutable_asset_dir / base_spec_file.relative_to(common_dir)
    model_config_file = mutable_asset_dir / base_model_file.relative_to(common_dir)

    with open(spec_config_file, "r", encoding="utf-8") as f:
        spec_config = yaml.safe_load(f)

    # Override storage info for model card preview
    if override_storage:
        print("Model card preview - Default setting version and storage info")

        # Autoincrement version for mutable asset
        spec_config["version"] = datetime.now().strftime("%Y%m%d%H%M%S")

        # Remove intellectualPropertyPublisher if it exists in properties
        if "properties" in spec_config:
            spec_config["properties"].pop("intellectualPropertyPublisher", None)

        # Create dummy file to upload to storage
        with open(mutable_asset_dir / "dummy.txt", "w", encoding="utf-8") as f:
            f.write("This is a dummy file used in the artifact for model card preview.")

        yaml_content = """
        path:
            uri: ./dummy.txt
            type: local
        publish:
            description: description.md
            type: custom_model
        """
        new_model_config = yaml.safe_load(yaml_content)

        # Overwrite model config
        with open(model_config_file, "w", encoding="utf-8") as f:
            yaml.dump(new_model_config, f, allow_unicode=True, default_flow_style=False)

    # Extract system_metadata from model spec
    # PUT request will be made after asset creation while the SDK update/PATCH logic is being updated
    system_metadata_payload = spec_config.pop("system_metadata", {})
    if system_metadata_payload:
        print(f"system_metadata found in model spec. Extracted system_metadata and saved "
              f"to system_metadata: {system_metadata_payload}")
    else:
        print(f"No system_metadata found in model spec. Using system metadata payload {system_metadata_payload}")

    # Write updated spec config back to the file
    if override_storage or system_metadata_payload:
        with open(spec_config_file, "w", encoding="utf-8") as f:
            yaml.dump(spec_config, f, allow_unicode=True, default_flow_style=False)

    mutable_asset = AssetConfig(asset_config_file)

    return mutable_asset, system_metadata_payload


def create_or_update_asset(readonly_asset: AssetConfig, registry_name: str, subscription_id: str, resource_group: str, override_storage: bool = False):
    """Create or update an asset in the AzureML registry.

    Args:
        readonly_asset (AssetConfig): Asset configuration to create or update
        registry_name (str): Name of AzureML registry to deploy to
        subscription_id (str): Subscription ID of AzureML registry to deploy to
        resource_group (str): Resource group of AzureML registry to deploy to
        override_storage (bool): Whether to override storage settings
    """
    print("[CREATING/UPDATING ASSET]")
    print(f"Registry name: {registry_name}, Subscription ID: {subscription_id}, Resource group: {resource_group}")

    # Create ML client
    ml_client = MLClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        registry_name=registry_name,
        credential=DefaultAzureCredential(),  # CodeQL [SM05139] DefaultAzureCredential should only be used for local development and testing purposes.
    )

    if not shutil.which("azcopy"):
        raise RuntimeError(
            "azcopy is not available in PATH. "
            "Please install azcopy: https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10"
        )

    with tempfile.TemporaryDirectory() as mutable_asset_dir:
        mutable_asset, system_metadata_payload = build_mutable_asset(base_asset=readonly_asset, mutable_asset_dir=mutable_asset_dir, override_storage=override_storage)
        try:
            success = create_asset(mutable_asset, registry_name, ml_client)
            if not success:
                raise RuntimeError(f"Failed to create/update asset: create_asset 'success' returned {success}")
        except Exception as e:
            print(f"Failed to create/update asset: {e}")
            raise

        # PUT system metadata after model creation
        if success:
            try:
                put_system_metadata(ml_client, mutable_asset, registry_name, system_metadata_payload)
            except Exception as e:
                print(f"Failed to update {mutable_asset.name} with system metadata: {e}")
                raise

        print("\n[VALIDATE YOUR ASSET IN THE UI HERE]")
        print(f" - Model Catalog link: https://ai.azure.com/explore/models/{mutable_asset.name}/version/{mutable_asset.version}/registry/{registry_name}")
        print(f" - Azure Portal link: https://ml.azure.com/registries/{registry_name}/models/{mutable_asset.name}/version/{mutable_asset.version}")


def asset_validate(asset_path: Path, dry_run: bool = False, allow_additional_properties: bool = False) -> bool:
    """Validate an asset at the specified path.

    Args:
        asset_path (Path): Path to the asset folder to validate
        dry_run (bool): If True, perform a dry run without side effects
        allow_additional_properties (bool): Whether to allow additional properties not defined in schema

    Returns:
        bool: True if validation passes, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would validate asset at: {asset_path}")
        return True

    asset_path = asset_path.resolve()
    print(f"[VALIDATION] Begin validating for asset at: {asset_path}...")

    # Check if asset path exists
    if not asset_path.exists():
        print(f"❌ [ERROR]: Asset path {asset_path} does not exist")
        return False

    # Check for exactly one asset
    asset_count = len(util.find_assets([asset_path], assets.DEFAULT_ASSET_FILENAME))
    if asset_count != 1:
        print(f"❌ [ERROR]: Expected exactly one asset in {asset_path}, found {asset_count}")
        return False

    # Load asset configuration
    readonly_asset = assets.AssetConfig(asset_path / assets.DEFAULT_ASSET_FILENAME)

    # Check asset type
    if readonly_asset.type != AssetType.MODEL:
        print(f"❌ [ERROR]: Asset type {readonly_asset.type} is not supported for validation. "
              f"Only models are currently supported.")
        return False

    # Perform validation
    return validate_model(readonly_asset.file_path, allow_additional_properties)


def asset_deploy(asset_path: Path, registry_name: str, subscription_id: str, resource_group: str, dry_run: bool = False, allow_additional_properties: bool = False, override_storage: bool = False) -> bool:
    """Deploy an asset to a registry.

    Args:
        asset_path (Path): Path to the asset folder to deploy
        dry_run (bool): If True, perform a dry run without deploying
        allow_additional_properties (bool): Whether to allow additional properties not defined in schema
        override_storage (bool): Whether to override storage settings

    Returns:
        bool: True if deployment succeeds, False otherwise
    """
    if dry_run:
        if override_storage:
            print(f"[DRY RUN] Would preview asset at {asset_path} to registry {registry_name}")
        else:
            print(f"[DRY RUN] Would deploy asset at {asset_path} to registry {registry_name}")
        return True

    asset_path = asset_path.resolve()

    # Validate asset before deployment
    if not asset_validate(asset_path, dry_run=False, allow_additional_properties=allow_additional_properties):
        print("❌ [ERROR]: Asset validation failed. Asset deployment aborted.")
        return False

    # Load asset configuration
    readonly_asset = assets.AssetConfig(asset_path / assets.DEFAULT_ASSET_FILENAME)

    try:
        create_or_update_asset(readonly_asset, registry_name, subscription_id, resource_group, override_storage)
        return True
    except Exception as e:
        print(f"❌ [ERROR]: Failed to deploy asset: {e}")
        return False
