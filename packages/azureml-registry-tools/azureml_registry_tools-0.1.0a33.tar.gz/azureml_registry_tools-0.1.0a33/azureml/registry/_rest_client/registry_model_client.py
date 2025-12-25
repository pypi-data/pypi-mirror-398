# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from .base_rest_client import BaseAzureRestClient
from .registry_management_client import RegistryManagementClient
from json.decoder import JSONDecodeError
from typing import Optional, Dict, Any

DEFAULT_API_VERSION = "2025-04-01"


class RegistryModelClient(BaseAzureRestClient):
    """Python client for RegistryModelController.

    Provides key operations for AzureML model management: get, list and, delete models.
    """

    def __init__(self, registry_name: str, subscription_id: str = None, resource_group_name: str = None,
                 primary_region: str = None, api_key: str = None, max_retries: int = 5, backoff_factor: int = 1):
        """
        Initialize the RegistryModelClient.

        Args:
            registry_name (str): Name of the AzureML registry.
            subscription_id (str, optional): Azure subscription ID. If None, auto-resolves from registry discovery.
            resource_group_name (str, optional): Resource group name containing the registry. If None, auto-resolves from registry discovery.
            primary_region (str, optional): Azure primary region for the registry. If None, auto-resolves from registry discovery.
            api_key (str, optional): API key or bearer token. If None, uses DefaultAzureCredential.
            max_retries (int): Maximum number of retries for requests.
            backoff_factor (int): Backoff factor for retries.
        """
        # Auto-discover missing parameters using registry discovery
        if subscription_id is None or resource_group_name is None or primary_region is None:
            discovery = RegistryManagementClient(registry_name=registry_name).discovery()
            discovered_subscription_id = discovery.get('subscriptionId')
            discovered_resource_group = discovery.get('resourceGroup')
            discovered_primary_region = discovery.get('primaryRegion')

            # Validate that passed parameters match discovered ones
            if subscription_id is not None and subscription_id != discovered_subscription_id:
                raise ValueError(
                    f"Provided subscription_id '{subscription_id}' does not match "
                    f"discovered subscription_id '{discovered_subscription_id}' for registry '{registry_name}'"
                )
            if resource_group_name is not None and resource_group_name != discovered_resource_group:
                raise ValueError(
                    f"Provided resource_group_name '{resource_group_name}' does not match "
                    f"discovered resource_group '{discovered_resource_group}' for registry '{registry_name}'"
                )
            if primary_region is not None and primary_region != discovered_primary_region:
                raise ValueError(
                    f"Provided primary_region '{primary_region}' does not match "
                    f"discovered primary_region '{discovered_primary_region}' for registry '{registry_name}'"
                )

            # Use discovered values for any missing parameters
            subscription_id = subscription_id or discovered_subscription_id
            resource_group_name = resource_group_name or discovered_resource_group
            primary_region = primary_region or discovered_primary_region

        base_url = f"https://{primary_region}.api.azureml.ms"
        super().__init__(base_url, api_key=api_key, max_retries=max_retries, backoff_factor=backoff_factor)

        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.registry_name = registry_name

        # Build the base path for model operations
        self.base_path = (
            f"/modelregistry/v1.0/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group_name}"
            f"/providers/Microsoft.MachineLearningServices"
            f"/registries/{registry_name}/models"
        )

    def list_models(self, name: str = None, tags: str = None, version: str = None,
                    framework: str = None, description: str = None, properties: str = None,
                    run_id: str = None, dataset_id: str = None, order_by: str = None,
                    skip_token: str = None, list_view_type: str = "ActiveOnly",
                    api_version: str = DEFAULT_API_VERSION, **kwargs) -> Dict[str, Any]:
        """
        Query the list of models in a registry.

        Args:
            name (str, optional): The model name.
            tags (str, optional): Comma separated string of tags key or tags key=value.
            version (str, optional): The model version.
            framework (str, optional): The framework.
            description (str, optional): The model description.
            properties (str, optional): Comma separated string of properties key and/or properties key=value.
            run_id (str, optional): The runId which created the model.
            dataset_id (str, optional): The datasetId associated with the model.
            order_by (str, optional): How the models are ordered in the response.
            skip_token (str, optional): The continuation token to retrieve the next page.
            list_view_type (str): View type filter (default: ActiveOnly).
            api_version (str): The API version to use.
            **kwargs: Additional arguments for the request.

        Returns:
            Dict[str, Any]: Paged response containing list of models.
        """
        self._refresh_api_key_if_needed()

        # Build query parameters
        params = {"api-version": api_version, "listViewType": list_view_type}
        if name:
            params["name"] = name
        if tags:
            params["tags"] = tags
        if version:
            params["version"] = version
        if framework:
            params["framework"] = framework
        if description:
            params["description"] = description
        if properties:
            params["properties"] = properties
        if run_id:
            params["runId"] = run_id
        if dataset_id:
            params["datasetId"] = dataset_id
        if order_by:
            params["orderBy"] = order_by
        if skip_token:
            params["$skipToken"] = skip_token

        url = f"{self.base_url}{self.base_path}"
        response = self.get(url, params=params, **kwargs)

        try:
            return response.json()
        except JSONDecodeError:
            raise ValueError(f"Failed to decode JSON response from {url}: {response.text.strip()}")

    # Method below is not currently used in the CLI, but kept for reference
    def get_model_by_asset_id(self, asset_id_or_reference: str, include_deployment_settings: bool = False,
                              workspace_id: str = None, api_version: str = DEFAULT_API_VERSION, **kwargs) -> Dict[str, Any]:
        """
        Get a model from registry using assetId or reference.

        Args:
            asset_id_or_reference (str): Model assetId like azureml://registries/myRegistry/models/myModel/versions/1.
            include_deployment_settings (bool): Whether to include deployment settings.
            workspace_id (str, optional): Workspace ID GUID for deployment environment association.
            api_version (str): The API version to use.
            **kwargs: Additional arguments for the request.

        Returns:
            Dict[str, Any]: The model data.
        """
        self._refresh_api_key_if_needed()

        # Use the alternate endpoint
        url = f"{self.base_url}/modelregistry/v1.0/registry/models"

        params = {
            "assetIdOrReference": asset_id_or_reference,
            "includeDeploymentSettings": str(include_deployment_settings).lower(),
            "api-version": api_version
        }
        if workspace_id:
            params["workspaceId"] = workspace_id

        response = self.get(url, params=params, **kwargs)

        try:
            return response.json()
        except JSONDecodeError:
            raise ValueError(f"Failed to decode JSON response from {url}: {response.text.strip()}")

    def get_model_by_name_and_version(self, name: str, version: str,
                                      api_version: str = DEFAULT_API_VERSION, **kwargs) -> Dict[str, Any]:
        """
        Get a specific model by name and version from the registry.

        Args:
            name (str): The name of the model.
            version (str): The version of the model.
            api_version (str): The API version to use.
            **kwargs: Additional arguments for the request.

        Returns:
            Dict[str, Any]: The model data.

        Raises:
            ValueError: If name or version is not provided.
        """
        if not name or not version:
            raise ValueError("Both name and version must be provided")

        self._refresh_api_key_if_needed()

        # Use the MMS ID format that the server expects: {name}:{version}
        model_id = f"{name}:{version}"
        url = f"{self.base_url}{self.base_path}/{model_id}"

        response = self.get(url, **kwargs)

        try:
            return response.json()
        except JSONDecodeError:
            raise ValueError(f"Failed to decode JSON response from {url}: {response.text.strip()}")

    def delete_model(self, name: str, version: str = None,
                     api_version: str = DEFAULT_API_VERSION, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Delete a model from the registry.

        Args:
            name (str): The name of the model to delete.
            version (str, optional): The version to delete. If None, deletes all versions.
            api_version (str): The API version to use.
            **kwargs: Additional arguments for the request.

        Returns:
            Optional[Dict[str, Any]]: The deletion response, if any.

        Raises:
            ValueError: If name is not provided.
        """
        if not name:
            raise ValueError("name must be provided")

        self._refresh_api_key_if_needed()

        if version:
            # Delete a specific version using the MMS ID format: {name}:{version}
            model_id = f"{name}:{version}"
            url = f"{self.base_url}{self.base_path}/{model_id}"
            response = self.delete(url, **kwargs)

            try:
                return response.json()
            except JSONDecodeError:
                return response.text or None
        else:
            # Delete all versions: first list all versions, then delete each one
            list_response = self.list_models(name=name, **kwargs)

            if "value" not in list_response:
                return {"message": f"No models found with name '{name}'"}

            models = list_response["value"]
            if not models:
                return {"message": f"No models found with name '{name}'"}

            deleted_versions = []
            errors = []

            for model in models:
                try:
                    model_version = model.get("properties", {}).get("version") or model.get("version")
                    if model_version:
                        # Delete this specific version
                        model_id = f"{name}:{model_version}"
                        url = f"{self.base_url}{self.base_path}/{model_id}"
                        response = self.delete(url, **kwargs)

                        if response.status_code in [200, 202, 204]:
                            deleted_versions.append(model_version)
                        else:
                            errors.append(f"Failed to delete version {model_version}: {response.status_code}")
                    else:
                        errors.append(f"Could not determine version for model: {model}")
                except Exception as e:
                    errors.append(f"Error deleting model version: {str(e)}")

            result = {
                "message": f"Deleted {len(deleted_versions)} version(s) of model '{name}'",
                "deleted_versions": deleted_versions
            }

            if errors:
                result["errors"] = errors

            return result

    # Method below is not currently used in the CLI, but kept for reference
    def get_model_for_non_azure_accounts(self, asset_id: str, api_version: str = DEFAULT_API_VERSION, **kwargs) -> Dict[str, Any]:
        """
        Get a model from registry for non-Azure accounts.

        Args:
            asset_id (str): Model assetId like azureml://registries/myRegistry/models/myModel/versions/1.
            api_version (str): The API version to use.
            **kwargs: Additional arguments for the request.

        Returns:
            Dict[str, Any]: The model data with SAS URL.
        """
        self._refresh_api_key_if_needed()

        url = f"{self.base_url}/modelregistry/v1.0/registry/models/nonazureaccount"
        params = {
            "assetId": asset_id,
            "api-version": api_version
        }

        response = self.get(url, params=params, **kwargs)

        try:
            return response.json()
        except JSONDecodeError:
            raise ValueError(f"Failed to decode JSON response from {url}: {response.text.strip()}")

    @staticmethod
    def parse_asset_id(asset_id: str) -> Dict[str, str]:
        """
        Parse an asset ID into its components.

        Args:
            asset_id (str): Model assetId like azureml://registries/myRegistry/models/myModel/versions/1.

        Returns:
            Dict[str, str]: Dictionary containing registry_name, name, and version.

        Raises:
            ValueError: If the asset ID format is invalid.
        """
        if not asset_id.startswith("azureml://registries/"):
            raise ValueError("Asset ID must start with 'azureml://registries/'")

        asset_id_parts = asset_id.split("/")
        if len(asset_id_parts) < 8 or asset_id_parts[4] != "models" or asset_id_parts[6] != "versions":
            raise ValueError(
                "Invalid asset ID format. Expected: azureml://registries/myRegistry/models/myModel/versions/1"
            )

        return {
            "registry_name": asset_id_parts[3],
            "name": asset_id_parts[5],
            "version": asset_id_parts[7]
        }
