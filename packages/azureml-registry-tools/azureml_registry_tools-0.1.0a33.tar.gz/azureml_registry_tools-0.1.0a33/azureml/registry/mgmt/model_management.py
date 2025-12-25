# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Model management methods."""
import json
import sys
from typing import Tuple
from azureml.registry._rest_client.registry_model_client import RegistryModelClient


def parse_asset_id(asset_id: str) -> Tuple[str, str, str]:
    """Parse an asset ID into its components.

    Args:
        asset_id (str): Model assetId like azureml://registries/myRegistry/models/myModel/versions/1.

    Returns:
        Tuple[str, str, str]: (registry_name, model_name, version)

    Raises:
        ValueError: If the asset ID format is invalid.
    """
    try:
        parsed = RegistryModelClient.parse_asset_id(asset_id)
        return parsed["registry_name"], parsed["name"], parsed["version"]
    except ValueError as e:
        raise ValueError(f"Invalid asset ID '{asset_id}': {e}")


def model_list(registry_name: str, subscription_id: str = None, resource_group_name: str = None,
               primary_region: str = None, name: str = None, tags: str = None,
               version: str = None, framework: str = None, description: str = None,
               properties: str = None, run_id: str = None, dataset_id: str = None,
               order_by: str = None, skip_token: str = None, list_view_type: str = "ActiveOnly") -> str:
    """List models in the registry.

    Args:
        registry_name (str): Name of the Azure ML registry.
        subscription_id (str, optional): Azure subscription ID. If None, auto-resolves from registry discovery.
        resource_group_name (str, optional): Resource group name containing the registry. If None, auto-resolves from registry discovery.
        primary_region (str, optional): Azure primary region for the registry. If None, auto-resolves from registry discovery.
        name (str, optional): The object name.
        tags (str, optional): Comma separated string of tags key or tags key=value.
        version (str, optional): The object version.
        framework (str, optional): The framework.
        description (str, optional): The object description.
        properties (str, optional): Comma separated string of properties key and/or properties key=value.
        run_id (str, optional): The runId which created the model.
        dataset_id (str, optional): The datasetId associated with the model.
        order_by (str, optional): How the models are ordered in the response.
        skip_token (str, optional): The continuation token to retrieve the next page.
        list_view_type (str): View type filter (default: ActiveOnly).

    Returns:
        str: JSON response containing list of models.
    """
    try:
        client = RegistryModelClient(
            registry_name=registry_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            primary_region=primary_region
        )

        result = client.list_models(
            name=name, tags=tags, version=version, framework=framework,
            description=description, properties=properties, run_id=run_id,
            dataset_id=dataset_id, order_by=order_by, skip_token=skip_token,
            list_view_type=list_view_type
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        print(f"Error listing models: {e}", file=sys.stderr)
        sys.exit(1)


def model_get(registry_name: str, name: str, version: str,
              subscription_id: str = None, resource_group_name: str = None,
              primary_region: str = None, include_deployment_settings: bool = False, workspace_id: str = None) -> str:
    """Get a specific model by name and version.

    Args:
        registry_name (str): Name of the Azure ML registry.
        name (str): The name of the model.
        version (str): The version of the model.
        subscription_id (str, optional): Azure subscription ID. If None, auto-resolves from registry discovery.
        resource_group_name (str, optional): Resource group name containing the registry. If None, auto-resolves from registry discovery.
        primary_region (str, optional): Azure primary region for the registry. If None, auto-resolves from registry discovery.
        include_deployment_settings (bool): Whether to include deployment settings.
        workspace_id (str, optional): Workspace ID GUID for deployment environment association.

    Returns:
        str: JSON response containing the model data.
    """
    try:
        client = RegistryModelClient(
            registry_name=registry_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            primary_region=primary_region
        )

        result = client.get_model_by_name_and_version(
            name=name,
            version=version
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        print(f"Error getting model {name} version {version}: {e}", file=sys.stderr)
        sys.exit(1)


def model_delete(registry_name: str, name: str, version: str = None,
                 subscription_id: str = None, resource_group_name: str = None,
                 primary_region: str = None, dry_run: bool = False, force: bool = False) -> None:
    """Delete a model from the registry.

    Args:
        registry_name (str): Name of the Azure ML registry.
        name (str): The name of the model to delete.
        version (str, optional): The version to delete. If None, deletes all versions.
        subscription_id (str, optional): Azure subscription ID. If None, auto-resolves from registry discovery.
        resource_group_name (str, optional): Resource group name containing the registry. If None, auto-resolves from registry discovery.
        primary_region (str, optional): Azure primary region for the registry. If None, auto-resolves from registry discovery.
        dry_run (bool): If True, do not perform any changes.
        force (bool): If True, skip confirmation prompt.
    """
    try:
        if not force:
            if version:
                confirm = input(f"Are you sure you want to delete model '{name}' version '{version}' from registry '{registry_name}'? [y/N]: ")
            else:
                confirm = input(f"Are you sure you want to delete ALL versions of model '{name}' from registry '{registry_name}'? [y/N]: ")
            if confirm.lower() != "y":
                print("Model deletion cancelled.")
                return

        if dry_run:
            if version:
                print(f"Dry run: Would delete model {name} version {version}")
            else:
                print(f"Dry run: Would delete all versions of model {name}")
            return

        client = RegistryModelClient(
            registry_name=registry_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            primary_region=primary_region
        )

        result = client.delete_model(
            name=name,
            version=version
        )
        print(result)

        if version:
            print(f"Successfully deleted model '{name}' version '{version}'")
        else:
            print(f"Successfully deleted all versions of model '{name}'")

    except Exception as e:
        print(f"Error deleting model {name}: {e}", file=sys.stderr)
        sys.exit(1)
