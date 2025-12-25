# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Syndication manifest dataclasses and validation for AzureML registry asset syndication."""

from dataclasses import dataclass, field
from typing import List
from uuid import UUID


def _norm_key(k):
    return k.replace('_', '').lower()


def _get_key(dct, *keys, normalize_keys=False):
    """Normalize and retrieve a value from a dict by trying multiple key casings.

    If normalize_keys is True, normalize the dict keys before searching.
    """
    if normalize_keys:
        dct_norm = {_norm_key(k): v for k, v in dct.items()}
        for k in keys:
            nk = _norm_key(k)
            if nk in dct_norm:
                return dct_norm[nk]
        return None
    else:
        for k in keys:
            if k in dct:
                return dct[k]
        return None


@dataclass
class Asset:
    """Represents a single asset with a name and version."""

    name: str
    version: str

    def to_dict(self) -> dict:
        """Convert the Asset instance to a dictionary with serialized field names."""
        return {"Name": self.name, "Version": self.version}

    @staticmethod
    def from_dict(d: dict, normalize_keys=False) -> "Asset":
        """Create an Asset instance from a dictionary with serialized field names."""
        return Asset(
            name=_get_key(d, "Name", normalize_keys=normalize_keys),
            version=_get_key(d, "Version", normalize_keys=normalize_keys) or ".*"
        )


@dataclass
class SourceRegistry:
    """Represents a source registry in the syndication manifest.

    Attributes:
        registry_name (str): The name of the source registry.
        tenant_id (UUID): The Azure tenant ID for the source registry.
        assets (dict): Dictionary mapping asset type to list of Asset objects.
    """

    registry_name: str
    tenant_id: UUID
    assets: dict  # asset_type (str) -> List[Asset]

    def to_dict(self) -> dict:
        """Convert the SourceRegistry instance to a dictionary with serialized field names."""
        asset_dict = {}
        for asset_type, asset_list in self.assets.items():
            if asset_list:
                asset_dict[asset_type] = [
                    {"Name": a.name} if a.name == ".*" else {"Name": a.name, "Version": a.version}
                    for a in asset_list
                ]
        return {
            "RegistryName": self.registry_name,
            "TenantId": str(self.tenant_id),
            "Assets": asset_dict
        }

    @staticmethod
    def from_dict(d: dict, normalize_keys=False) -> "SourceRegistry":
        """Create a SourceRegistry instance from a dictionary with any key casing (snake, camel, Pascal)."""
        assets = {}
        assets_dict = _get_key(d, "Assets", "assets", normalize_keys=normalize_keys)
        for asset_type, asset_list in assets_dict.items():
            assets[asset_type] = [Asset.from_dict(a, normalize_keys=normalize_keys) for a in asset_list]
        return SourceRegistry(
            registry_name=_get_key(d, "RegistryName", "registry_name", normalize_keys=normalize_keys),
            tenant_id=UUID(str(_get_key(d, "TenantId", "tenant_id", normalize_keys=normalize_keys))),
            assets=assets
        )


@dataclass
class SyndicationManifest:
    """Represents the root syndication manifest for a destination registry.

    Attributes:
        registry_name (str): The name of the destination registry.
        tenant_id (UUID): The Azure tenant ID for the destination registry.
        source_registries (List[SourceRegistry]): All source registries.
        _allow_wildcards (bool): Internal flag for wildcard version validation (not serialized).
    """

    registry_name: str
    tenant_id: UUID
    source_registries: List[SourceRegistry]
    _allow_wildcards: bool = field(default=False, repr=False, compare=False)

    def to_dict(self) -> dict:
        """Convert the SyndicationManifest instance to a dictionary with serialized field names."""
        return {
            "RegistryName": self.registry_name,
            "TenantId": str(self.tenant_id),
            "SourceRegistries": [sr.to_dict() for sr in self.source_registries]
        }

    def to_dto(self) -> dict:
        """Serialize the manifest as a value of {"Manifest": SyndicationManifest} for external consumers."""
        return {"Manifest": self.to_dict()}

    @staticmethod
    def from_dto(dto: dict, normalize_keys=False) -> "SyndicationManifest":
        """Deserialize a SyndicationManifest from a dictionary produced by to_dto, with validation. Handles any key casing."""
        if not isinstance(dto, dict) or _get_key(dto, "Manifest", normalize_keys=normalize_keys) is None:
            raise ValueError("Input must be a dict with a 'Manifest' key.")
        manifest = _get_key(dto, "Manifest", normalize_keys=normalize_keys)
        if not isinstance(manifest, dict):
            raise ValueError("'Manifest' value must be a dict.")
        for field_name in ("RegistryName", "TenantId", "SourceRegistries"):
            if _get_key(manifest, field_name, normalize_keys=normalize_keys) is None:
                raise ValueError(f"Missing required field '{field_name}' in Manifest.")
        registry_name = _get_key(manifest, "RegistryName", "registry_name", normalize_keys=normalize_keys)
        tenant_id = _get_key(manifest, "TenantId", "tenant_id", normalize_keys=normalize_keys)
        try:
            tenant_id = UUID(str(tenant_id))
        except Exception:
            raise ValueError("TenantId must be a valid UUID string.")
        sr_list = _get_key(manifest, "SourceRegistries", "source_registries", normalize_keys=normalize_keys)
        if not isinstance(sr_list, list):
            raise ValueError("SourceRegistries must be a list.")
        source_registries = [SourceRegistry.from_dict(sr, normalize_keys=normalize_keys) for sr in sr_list]
        return SyndicationManifest(
            registry_name=registry_name,
            tenant_id=tenant_id,
            source_registries=source_registries
        )


@dataclass
class AssetToResync:
    """Represents an asset to resync with its associated tenant ID."""

    asset_id: str
    tenant_id: UUID

    def to_dict(self) -> dict:
        """Convert the AssetToResync instance to a dictionary."""
        return {
            "AssetIds": self.asset_id,
            "TenantId": str(self.tenant_id)
        }

    @staticmethod
    def from_dict(d: dict, normalize_keys=False) -> "AssetToResync":
        """Create an AssetToResync instance from a dictionary."""
        asset_id = _get_key(d, "AssetIds", "asset_ids", normalize_keys=normalize_keys)
        if asset_id is None:
            raise ValueError("Missing required field 'AssetIds' in dictionary.")

        tenant_id_str = _get_key(d, "TenantId", "tenant_id", normalize_keys=normalize_keys)
        if tenant_id_str is None:
            raise ValueError("Missing required field 'TenantId' in dictionary.")

        try:
            tenant_id = UUID(str(tenant_id_str))
        except ValueError:
            raise ValueError("TenantId must be a valid UUID string.")

        return AssetToResync(
            asset_id=str(asset_id),
            tenant_id=tenant_id
        )


@dataclass
class ResyncAssetsInManifestDto:
    """Represents a collection of assets to resync in a manifest."""

    assets_to_resync: List[AssetToResync]

    def to_dict(self) -> dict:
        """Convert the ResyncAssetsInManifestDto instance to a dictionary."""
        return {
            "AssetsToResync": [asset.to_dict() for asset in self.assets_to_resync]
        }

    @staticmethod
    def from_dict(d: dict, normalize_keys=False) -> "ResyncAssetsInManifestDto":
        """Create a ResyncAssetsInManifestDto instance from a dictionary."""
        assets_list = _get_key(d, "AssetsToResync", "assets_to_resync", normalize_keys=normalize_keys)
        if not isinstance(assets_list, list):
            raise ValueError("AssetsToResync must be a list.")
        return ResyncAssetsInManifestDto(
            assets_to_resync=[AssetToResync.from_dict(asset, normalize_keys=normalize_keys) for asset in assets_list]
        )

    @staticmethod
    def from_asset_list(tenant_id: UUID, asset_ids: List[str]) -> "ResyncAssetsInManifestDto":
        """Create a ResyncAssetsInManifestDto instance from a tenant ID and list of asset ID strings.

        Args:
            tenant_id (UUID): The tenant ID to use for all assets.
            asset_ids (List[str]): List of asset ID strings.

        Returns:
            ResyncAssetsInManifestDto: Instance with assets created from the provided IDs and tenant ID.
        """
        assets_to_resync = [
            AssetToResync(asset_id=asset_id, tenant_id=tenant_id)
            for asset_id in asset_ids
        ]
        return ResyncAssetsInManifestDto(assets_to_resync=assets_to_resync)
