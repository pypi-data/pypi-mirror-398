"""Asset caching functionality for scanner integrations."""

import logging
from typing import Dict, List, Optional, Set

from regscale.models import regscale_models
from regscale.utils.threading.threadsafe_dict import ThreadSafeDict

logger = logging.getLogger("regscale")


class AssetCache:
    """
    Cache for asset lookups by identifier.

    Provides efficient O(1) lookups for assets by their identifier field
    (e.g., otherTrackingNumber, ipAddress, name). Also supports fallback
    lookups by IP address, FQDN, and DNS when the primary identifier
    doesn't match.

    Thread-safe implementation using ThreadSafeDict for concurrent access.
    """

    # Common fallback identifier fields for asset lookups
    FALLBACK_FIELDS = ("ipAddress", "fqdn", "dns")

    def __init__(
        self,
        plan_id: int,
        parent_module: str,
        identifier_field: str = "otherTrackingNumber",
        is_component: bool = False,
        options_map_assets_to_components: bool = False,
        suppress_not_found_errors: bool = False,
        external_cache: Optional[ThreadSafeDict] = None,
    ):
        """
        Initialize the asset cache.

        :param int plan_id: The security plan or component ID
        :param str parent_module: The parent module string (e.g., "securityplans", "components")
        :param str identifier_field: Field to use as primary lookup key, defaults to "otherTrackingNumber"
        :param bool is_component: Whether this is for a component (vs security plan), defaults to False
        :param bool options_map_assets_to_components: Use component-based asset mapping, defaults to False
        :param bool suppress_not_found_errors: Suppress 'asset not found' errors, defaults to False
        :param Optional[ThreadSafeDict] external_cache: External cache dict for backward compatibility
        """
        self.plan_id = plan_id
        self.parent_module = parent_module
        self.identifier_field = identifier_field
        self.is_component = is_component
        # Use external cache if provided, otherwise create new one
        self._cache: ThreadSafeDict[str, regscale_models.Asset] = external_cache or ThreadSafeDict()
        self._loaded = False
        self._alerted_identifiers: Set[str] = set()
        self._options_map_assets_to_components = options_map_assets_to_components
        self._suppress_not_found_errors = suppress_not_found_errors

    @property
    def options_map_assets_to_components(self) -> bool:
        """Get whether to use component-based asset mapping."""
        return self._options_map_assets_to_components

    @options_map_assets_to_components.setter
    def options_map_assets_to_components(self, value: bool) -> None:
        """
        Set whether to use component-based asset mapping.

        When enabled, uses Asset.get_map() which queries via assetMappings GraphQL.
        When disabled, uses Asset.get_all_by_parent() which queries directly by parent.

        :param bool value: Whether to enable component mapping
        """
        self._options_map_assets_to_components = value

    @property
    def suppress_not_found_errors(self) -> bool:
        """Get whether to suppress 'asset not found' error logging."""
        return self._suppress_not_found_errors

    @suppress_not_found_errors.setter
    def suppress_not_found_errors(self, value: bool) -> None:
        """
        Set whether to suppress 'asset not found' error logging.

        :param bool value: Whether to suppress not found errors
        """
        self._suppress_not_found_errors = value

    def get_by_identifier(self, identifier: str) -> Optional[regscale_models.Asset]:
        """
        Get an asset by its identifier with fallback lookups.

        First tries the primary identifier field. If not found, falls back
        to searching by IP address, FQDN, and DNS fields.

        :param str identifier: The identifier of the asset to find
        :return: The asset if found, None otherwise
        :rtype: Optional[regscale_models.Asset]
        """
        if not identifier:
            return None

        # Ensure cache is loaded
        if not self._loaded:
            self.warm_cache()

        # Try primary identifier field first
        if asset := self._cache.get(identifier):
            return asset

        # Fallback: Try common identifier fields
        # This helps when identifier_field doesn't match or assets use different identifiers
        for cached_asset in self._cache.values():
            for field in self.FALLBACK_FIELDS:
                if getattr(cached_asset, field, None) == identifier:
                    logger.debug("Found asset %d by %s fallback: %s", cached_asset.id, field, identifier)
                    return cached_asset

        # Log warning if still not found (only once per identifier)
        if identifier not in self._alerted_identifiers:
            self._alerted_identifiers.add(identifier)
            if not self._suppress_not_found_errors:
                logger.warning(
                    "Asset not found for identifier '%s' (tried %s, %s)",
                    identifier,
                    self.identifier_field,
                    ", ".join(self.FALLBACK_FIELDS),
                )

        return None

    def get_map(self) -> Dict[str, regscale_models.Asset]:
        """
        Get the full asset map, loading from API if necessary.

        Returns a dictionary mapping asset identifiers to Asset objects.
        Uses different retrieval strategies based on options_map_assets_to_components.

        :return: A dictionary mapping asset identifiers to Asset objects
        :rtype: Dict[str, regscale_models.Asset]
        """
        if self._options_map_assets_to_components:
            # Fetch asset map directly using assetMappings GraphQL query
            return regscale_models.Asset.get_map(
                plan_id=self.plan_id,
                key_field=self.identifier_field,
                is_component=self.is_component,
            )
        else:
            # Construct asset map by fetching all assets under the plan
            assets: List[regscale_models.Asset] = regscale_models.Asset.get_all_by_parent(
                parent_id=self.plan_id,
                parent_module=self.parent_module,
            )
            return {getattr(x, self.identifier_field): x for x in assets if getattr(x, self.identifier_field, None)}

    def warm_cache(self) -> None:
        """
        Pre-load all assets for the plan into cache.

        This method fetches all assets from the API and populates the
        internal cache for efficient subsequent lookups.

        :rtype: None
        """
        logger.info("Warming asset cache for plan_id=%d...", self.plan_id)
        asset_map = self.get_map()
        self._cache.update(asset_map)
        self._loaded = True
        logger.debug("Asset cache warmed with %d assets", len(self._cache))

    def prime(self) -> None:
        """
        Prime the asset cache by fetching assets for the given plan.

        This is an alias for warm_cache() that matches the existing
        _prime_asset_cache() method naming convention.

        :rtype: None
        """
        self.warm_cache()

    def add(self, asset: regscale_models.Asset) -> None:
        """
        Add an asset to the cache.

        :param regscale_models.Asset asset: The asset to add
        :rtype: None
        """
        identifier = getattr(asset, self.identifier_field, None)
        if identifier:
            self._cache[identifier] = asset
        else:
            logger.warning(
                "Cannot add asset %d to cache: missing identifier field '%s'",
                asset.id if asset.id else "unknown",
                self.identifier_field,
            )

    def add_by_identifier(self, identifier: str, asset: regscale_models.Asset) -> None:
        """
        Add an asset to the cache with a specific identifier.

        This is useful when the identifier differs from the asset's
        actual identifier field value.

        :param str identifier: The identifier key to use in the cache
        :param regscale_models.Asset asset: The asset to add
        :rtype: None
        """
        if identifier:
            self._cache[identifier] = asset
        else:
            logger.warning("Cannot add asset to cache with empty identifier")

    def update(self, asset_map: Dict[str, regscale_models.Asset]) -> None:
        """
        Update the cache with multiple assets.

        :param Dict[str, regscale_models.Asset] asset_map: Dictionary of identifier to asset mappings
        :rtype: None
        """
        self._cache.update(asset_map)
        if not self._loaded and asset_map:
            self._loaded = True

    def remove(self, identifier: str) -> Optional[regscale_models.Asset]:
        """
        Remove an asset from the cache by identifier.

        :param str identifier: The identifier of the asset to remove
        :return: The removed asset, or None if not found
        :rtype: Optional[regscale_models.Asset]
        """
        return self._cache.pop(identifier, None)

    def clear(self) -> None:
        """
        Clear the cache.

        Removes all cached assets and resets the loaded state.

        :rtype: None
        """
        self._cache.clear()
        self._alerted_identifiers.clear()
        self._loaded = False

    def __len__(self) -> int:
        """
        Get the number of assets in the cache.

        :return: The number of cached assets
        :rtype: int
        """
        return len(self._cache)

    def __contains__(self, identifier: str) -> bool:
        """
        Check if an identifier is in the cache.

        :param str identifier: The identifier to check
        :return: True if the identifier is cached, False otherwise
        :rtype: bool
        """
        return identifier in self._cache

    @property
    def is_loaded(self) -> bool:
        """
        Check if the cache has been loaded.

        :return: True if the cache has been warmed/loaded, False otherwise
        :rtype: bool
        """
        return self._loaded

    def values(self):
        """
        Get all cached assets.

        :return: List of cached Asset objects
        :rtype: List[regscale_models.Asset]
        """
        return self._cache.values()

    def keys(self):
        """
        Get all cached identifiers.

        :return: List of cached identifier strings
        :rtype: List[str]
        """
        return self._cache.keys()

    def items(self):
        """
        Get all cached identifier-asset pairs.

        :return: List of (identifier, asset) tuples
        :rtype: List[tuple]
        """
        return self._cache.items()

    def get(self, identifier: str, default: Optional[regscale_models.Asset] = None) -> Optional[regscale_models.Asset]:
        """
        Get an asset by identifier without fallback lookups.

        Unlike get_by_identifier(), this method only checks the primary
        cache without trying fallback fields.

        :param str identifier: The identifier of the asset
        :param Optional[regscale_models.Asset] default: Default value if not found
        :return: The asset if found, default otherwise
        :rtype: Optional[regscale_models.Asset]
        """
        return self._cache.get(identifier, default)
