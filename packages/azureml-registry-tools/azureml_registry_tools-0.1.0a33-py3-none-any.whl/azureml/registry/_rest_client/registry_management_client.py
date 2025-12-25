# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from .base_rest_client import BaseAzureRestClient


class RegistryManagementClient(BaseAzureRestClient):
    """Python client for RegistrySyndicationManifestController (excluding S2S APIs).

    Handles authentication, token refresh, and provides methods for manifest and registry management.
    """

    def __init__(self, registry_name: str, primary_region: str = None, api_key: str = None, max_retries: int = 5, backoff_factor: int = 1) -> None:
        """
        Initialize the RegistryManagementClient.

        Args:
            primary_region (str): The Azure region for the registry.
            registry_name (str): The name of the AzureML registry.
            api_key (str, optional): Bearer token for authentication. If None, uses DefaultAzureCredential.
            max_retries (int): Maximum number of retries for failed requests.
            backoff_factor (int): Backoff factor for retry delays.
        """
        if primary_region is None:
            # Resolve the primary region if not provided
            primary_region = self.resolve_registry_primary_region(registry_name)
        if primary_region.lower() == "centraluseuap":
            base_url = "https://int.api.azureml-test.ms"
        else:
            base_url = f"https://{primary_region}.api.azureml.ms"
        super().__init__(base_url, api_key=api_key, max_retries=max_retries, backoff_factor=backoff_factor)
        self.registry_name = registry_name

    @staticmethod
    def resolve_registry_primary_region(registry_name: str) -> str:
        """
        Resolve the primary region for the given registry name.

        Args:
            registry_name (str): The name of the AzureML registry.

        Returns:
            str: The primary region for the registry.
        """
        discovery = RegistryManagementClient(registry_name, primary_region="eastus").discovery()
        return discovery.get('primaryRegion', 'eastus')

    def create_or_update_manifest(self, manifest_dto: dict) -> dict:
        """
        Create or update the syndication manifest for the registry.

        Args:
            manifest_dto (dict): The manifest data transfer object.

        Returns:
            dict: The response from the service.
        """
        self._refresh_api_key_if_needed()
        url = f"{self.base_url}/registrymanagement/v1.0/registrySyndication/{self.registry_name}/createOrUpdateManifest"
        response = self.post(url, json=manifest_dto)
        return response.json()

    def sync_assets_in_manifest(self, resync_assets_dto: dict) -> dict:
        """
        Resynchronize assets in the syndication manifest.

        Args:
            resync_assets_dto (dict): The DTO specifying which assets to resync.

        Returns:
            dict: The response from the service.
        """
        self._refresh_api_key_if_needed()
        url = f"{self.base_url}/registrymanagement/v1.0/registrySyndication/{self.registry_name}/resyncAssetsInManifest"
        response = self.post(url, json=resync_assets_dto)
        return response.json()

    def delete_manifest(self) -> dict:
        """
        Delete the syndication manifest for the registry.

        Returns:
            dict: The response from the service.
        """
        self._refresh_api_key_if_needed()
        url = f"{self.base_url}/registrymanagement/v1.0/registrySyndication/{self.registry_name}/deleteManifest"
        response = self.post(url)
        return response.json()

    def get_manifest(self) -> dict:
        """
        Get the syndication manifest for the registry.

        Returns:
            dict: The manifest data.
        """
        self._refresh_api_key_if_needed()
        url = f"{self.base_url}/registrymanagement/v1.0/registrySyndication/{self.registry_name}/getManifest"
        response = self.get(url)
        return response.json()

    def discovery(self) -> dict:
        """
        Get discovery information for the registry.

        Returns:
            dict: The discovery information for the registry.
        """
        self._refresh_api_key_if_needed()
        url = f"{self.base_url}/registrymanagement/v1.0/registries/{self.registry_name}/discovery"
        try:
            response = self.get(url)
            return response.json()
        except Exception as ex:
            # Special handling for HTTP errors with status_code attribute
            if hasattr(ex, 'response') and ex.response is not None:
                status_code = ex.response.status_code
                if status_code == 403:
                    raise RuntimeError(f"Received 403 Forbidden. This may indicate that the registry '{self.registry_name}' does not exist or you do not have access.")
                else:
                    raise RuntimeError(f"Failed to get discovery information: {status_code} {ex.response.text}")
            raise RuntimeError(f"Error occurred while trying to get discovery information: {ex}")
