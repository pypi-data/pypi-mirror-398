# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Syndication manifest generator for AzureML registries.

This script parses YAML files describing source registries and assets, validates them, and generates a syndication
manifest for AzureML registries.
"""

import os
import glob
import argparse
import json
from ruamel.yaml import YAML
from .syndication_manifest import Asset, SourceRegistry, SyndicationManifest

REQUIRED_SOURCE_FIELDS = ['name', 'tenant_id', 'is_ipp', 'assets']
REQUIRED_REGISTRY_FIELDS = ['tenant_id', 'name']
ALLOWED_ASSET_TYPES = {
    'environments', 'models', 'deployment-templates', 'components', 'datasets'
}

ASSET_TYPE_MAP = {
    'models': 'Models',
    'environments': 'Environments',
    'deployment-templates': 'DeploymentTemplates',
    'components': 'Components',
    'datasets': 'Datasets',
}


def validate_manifest_data(data: dict, file_path: str) -> None:
    """Validate required root-level fields and allowed values for nested fields under 'assets'.

    Args:
        data (dict): Parsed YAML content.
        file_path (str): Path to the YAML file (for error reporting).

    Raises:
        ValueError: If required fields are missing or invalid values are found.
    """
    missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in data]
    if missing:
        raise ValueError(
            f"Missing required field(s) in {file_path}: {', '.join(missing)}"
        )
    assets = data.get('assets', {})
    if not isinstance(assets, dict):
        raise ValueError(f"'assets' field in {file_path} must be a dictionary.")
    for asset_type in assets:
        if asset_type not in ALLOWED_ASSET_TYPES:
            raise ValueError(
                f"Invalid asset type '{asset_type}' in 'assets' of {file_path}. Allowed: "
                f"{', '.join(ALLOWED_ASSET_TYPES)}"
            )


def parse_asset_objs(asset_type: str, asset_dict: dict) -> list:
    """Parse asset objects from the asset dictionary for a given asset type.

    Args:
        asset_type (str): The asset type (e.g., 'models').
        asset_dict (dict or str): Dictionary of asset names to version lists or dicts, or a wildcard string.

    Returns:
        list: List of Asset objects.
    """
    assets = []
    # Handle wildcard string case: environments: "*"
    if asset_dict == "*":
        assets.append(Asset(name=".*", version=".*"))
        return assets
    if not asset_dict or not isinstance(asset_dict, dict):
        return assets
    for asset_name, asset_info in asset_dict.items():
        if isinstance(asset_info, dict) and 'versions' in asset_info:
            versions = asset_info['versions']
        elif isinstance(asset_info, list):
            versions = asset_info
        else:
            versions = [asset_info]
        for version in versions:
            assets.append(Asset(name=asset_name, version=version))
    return assets


def read_manifest_files(folder: str) -> dict:
    """Recursively read all YAML files in the 'sources' subdirectory and validate required root-level fields.

    Args:
        folder (str): Root folder containing the 'sources' directory.

    Returns:
        dict: Mapping of file paths to loaded SourceRegistry instances.

    Raises:
        ValueError: If required fields are missing in any YAML file.
    """
    sources_path = os.path.join(folder, 'sources')
    yaml_files = glob.glob(os.path.join(sources_path, '**', '*.yaml'), recursive=True)
    contents = {}
    yaml = YAML(typ='safe')
    for file_path in yaml_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
        validate_manifest_data(data, file_path)
        assets = {}
        for yaml_key in ALLOWED_ASSET_TYPES:
            asset_objs = parse_asset_objs(yaml_key, data.get('assets', {}).get(yaml_key))
            if asset_objs:
                assets[yaml_key] = asset_objs
        source_registry = SourceRegistry(
            registry_name=data['name'],
            tenant_id=data['tenant_id'],
            assets=assets
        )
        contents[file_path] = source_registry
    return contents


def _load_registry_yaml(folder: str) -> SyndicationManifest:
    """Load 'registry.yaml' from the specified folder into a SyndicationManifest instance (without SourceRegistries).

    Args:
        folder (str): Folder containing the 'registry.yaml' file.

    Returns:
        SyndicationManifest: Instance populated from the YAML file (SourceRegistries is an empty list), with
            _allow_wildcards set.

    Raises:
        FileNotFoundError: If 'registry.yaml' is not found in the folder.
        ValueError: If required fields are missing.
    """
    registry_path = os.path.join(folder, 'registry.yaml')
    if not os.path.isfile(registry_path):
        raise FileNotFoundError(f"{registry_path} not found.")
    yaml = YAML(typ='safe')
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f)
    missing = [field for field in REQUIRED_REGISTRY_FIELDS if field not in data]
    if missing:
        raise ValueError(
            f"Missing required field(s) in registry.yaml: {', '.join(missing)}"
        )
    # Read allow_wildcards flag, default to False if not present
    allow_wildcards = data.get('allow_wildcards', False)
    return SyndicationManifest(
        registry_name=data['name'],
        tenant_id=data['tenant_id'],
        source_registries=[],
        _allow_wildcards=allow_wildcards
    )


def generate_syndication_manifest(folder: str) -> SyndicationManifest:
    """Load the destination registry and all source registries manifests from the specified folder.

    This function loads the destination registry's configuration, all source registries, validates asset uniqueness
    and wildcard usage, and returns a complete SyndicationManifest object.

    Args:
        folder (str): Root folder containing the manifest for the sources.

    Returns:
        SyndicationManifest: The complete syndication manifest with destination and source registries.

    Raises:
        ValueError: If asset names are not unique across all SourceRegistry instances, or if wildcards are not allowed
            but used.
    """
    # Load the destination registry manifest and allow_wildcards flag
    manifest = _load_registry_yaml(folder)
    allow_wildcards = manifest._allow_wildcards
    # Read all source registry manifests from the sources directory
    source_registries_dict = read_manifest_files(folder)
    source_registries = list(source_registries_dict.values())

    # Validate uniqueness of asset names within the same asset type across all SourceRegistry instances
    asset_types = [
        ('Models', 'models'),
        ('Environments', 'environments'),
        ('DeploymentTemplates', 'deployment-templates'),
        ('Components', 'components'),
        ('Datasets', 'datasets'),
    ]
    for class_attr, yaml_key in asset_types:
        registry_asset_map = dict()  # asset_name -> set of (registry_name, uri)
        duplicates = dict()  # asset_name -> set of uris
        for sr in source_registries:
            asset_list = sr.assets.get(yaml_key, [])
            for asset in asset_list:
                uri = f"azureml://registries/{sr.registry_name}/{yaml_key}/name/{asset.name}/versions/{asset.version}"
                # If allow_wildcards is False, disallow wildcard versions in asset URIs
                if not allow_wildcards:
                    if asset.version == ".*" or asset.version == "*":
                        raise ValueError(
                            f"Wildcard asset version not allowed (allow_wildcards is False): {uri}"
                        )
                # Extract asset name from URI for uniqueness validation
                asset_name = asset.name
                registry_name = sr.registry_name
                if asset_name not in registry_asset_map:
                    registry_asset_map[asset_name] = set()
                registry_asset_map[asset_name].add((registry_name, uri))
        # Check for duplicate asset names across registries for this asset type
        for asset_name, reg_uris in registry_asset_map.items():
            registries = {reg for reg, _ in reg_uris}
            if len(registries) > 1:
                uris = {uri for _, uri in reg_uris}
                duplicates[asset_name] = uris
        if duplicates:
            error_lines = []
            for asset_name, uris in sorted(duplicates.items()):
                error_lines.append(
                    f"Asset name '{asset_name}' for asset type '{yaml_key}' is duplicated across registries in URIs: "
                    + ", ".join(sorted(uris))
                )
            raise ValueError("\n".join(error_lines))

    # Populate SourceRegistries in the SyndicationManifest instance
    manifest.source_registries = source_registries
    return manifest


if __name__ == "__main__":
    # Parse command-line arguments for the manifest folder
    parser = argparse.ArgumentParser(description="Syndication manifest structure.")
    parser.add_argument(
        '-f', '--folder', type=str, help='Registry syndication manifest folder', required=True
    )
    args = parser.parse_args()
    # Generate the syndication manifest and print as formatted JSON
    manifest = generate_syndication_manifest(args.folder)
    print(json.dumps(manifest.to_dto(), indent=2))
