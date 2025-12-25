# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""RegistryUtils class."""

from typing import Union
from azure.ai.ml import MLClient, operations as ops
from azureml.registry.tools.config import AssetType


class RegistryUtils:
    """Registry utils."""

    def get_operations_from_type(asset_type: AssetType, ml_client: MLClient) -> Union[
                                 ops.ComponentOperations, ops.DataOperations, ops.EnvironmentOperations,
                                 ops.ModelOperations]:
        """Get MLCLient operations related to an asset type.

        Args:
            asset_type (AssetType): Asset type.
            ml_client (MLClient): ML client.
        Returns:
            Union[ops.ComponentOperations, ops.DataOperations, ops.EnvironmentOperations,
                ops.ModelOperations]: Operations object.
        """
        if asset_type == AssetType.COMPONENT:
            return ml_client.components
        elif asset_type == AssetType.DATA:
            return ml_client.data
        elif asset_type == AssetType.ENVIRONMENT:
            return ml_client.environments
        elif asset_type == AssetType.MODEL:
            return ml_client.models
        else:
            raise Exception(f"Asset type {asset_type} is not supported.")
