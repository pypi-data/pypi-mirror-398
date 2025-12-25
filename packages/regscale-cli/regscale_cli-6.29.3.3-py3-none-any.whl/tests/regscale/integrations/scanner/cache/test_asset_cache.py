#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for AssetCache class."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.scanner.cache.asset_cache import AssetCache
from regscale.models import regscale_models
from regscale.utils.threading.threadsafe_dict import ThreadSafeDict

PATH = "regscale.integrations.scanner.cache.asset_cache"
logger = logging.getLogger("regscale")


@pytest.fixture
def mock_asset():
    """Create a mock Asset object for testing."""
    asset = MagicMock(spec=regscale_models.Asset)
    asset.id = 1
    asset.name = "test-asset"
    asset.otherTrackingNumber = "ASSET-001"
    asset.ipAddress = "192.168.1.100"
    asset.fqdn = "test.example.com"
    asset.dns = "test-dns.example.com"
    return asset


@pytest.fixture
def mock_assets():
    """Create a list of mock Asset objects for testing."""
    assets = []

    # Asset with all identifiers
    asset1 = MagicMock(spec=regscale_models.Asset)
    asset1.id = 1
    asset1.name = "asset-1"
    asset1.otherTrackingNumber = "ASSET-001"
    asset1.ipAddress = "192.168.1.1"
    asset1.fqdn = "asset1.example.com"
    asset1.dns = "dns1.example.com"
    assets.append(asset1)

    # Asset with partial identifiers
    asset2 = MagicMock(spec=regscale_models.Asset)
    asset2.id = 2
    asset2.name = "asset-2"
    asset2.otherTrackingNumber = "ASSET-002"
    asset2.ipAddress = "192.168.1.2"
    asset2.fqdn = None
    asset2.dns = "dns2.example.com"
    assets.append(asset2)

    # Asset with minimal identifiers
    asset3 = MagicMock(spec=regscale_models.Asset)
    asset3.id = 3
    asset3.name = "asset-3"
    asset3.otherTrackingNumber = "ASSET-003"
    asset3.ipAddress = None
    asset3.fqdn = None
    asset3.dns = None
    assets.append(asset3)

    return assets


@pytest.fixture
def asset_map(mock_assets):
    """Create a dictionary mapping identifiers to assets."""
    return {
        "ASSET-001": mock_assets[0],
        "ASSET-002": mock_assets[1],
        "ASSET-003": mock_assets[2],
    }


class TestAssetCacheInit:
    """Test AssetCache initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        assert cache.plan_id == 123
        assert cache.parent_module == "securityplans"
        assert cache.identifier_field == "otherTrackingNumber"
        assert cache.is_component is False
        assert cache.options_map_assets_to_components is False
        assert cache.suppress_not_found_errors is False
        assert isinstance(cache._cache, ThreadSafeDict)
        assert not cache.is_loaded

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        cache = AssetCache(
            plan_id=456,
            parent_module="components",
            identifier_field="ipAddress",
            is_component=True,
            options_map_assets_to_components=True,
            suppress_not_found_errors=True,
        )

        assert cache.plan_id == 456
        assert cache.parent_module == "components"
        assert cache.identifier_field == "ipAddress"
        assert cache.is_component is True
        assert cache.options_map_assets_to_components is True
        assert cache.suppress_not_found_errors is True

    def test_init_with_external_cache(self):
        """Test initialization with external cache."""
        external_cache = ThreadSafeDict()
        external_cache["test-key"] = MagicMock()

        cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            external_cache=external_cache,
        )

        assert cache._cache is external_cache
        assert "test-key" in cache._cache


class TestAssetCacheProperties:
    """Test AssetCache property getters and setters."""

    def test_options_map_assets_to_components_getter(self):
        """Test getting options_map_assets_to_components property."""
        cache = AssetCache(plan_id=123, parent_module="securityplans", options_map_assets_to_components=True)

        assert cache.options_map_assets_to_components is True

    def test_options_map_assets_to_components_setter(self):
        """Test setting options_map_assets_to_components property."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        assert cache.options_map_assets_to_components is False

        cache.options_map_assets_to_components = True
        assert cache.options_map_assets_to_components is True

    def test_suppress_not_found_errors_getter(self):
        """Test getting suppress_not_found_errors property."""
        cache = AssetCache(plan_id=123, parent_module="securityplans", suppress_not_found_errors=True)

        assert cache.suppress_not_found_errors is True

    def test_suppress_not_found_errors_setter(self):
        """Test setting suppress_not_found_errors property."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        assert cache.suppress_not_found_errors is False

        cache.suppress_not_found_errors = True
        assert cache.suppress_not_found_errors is True

    def test_is_loaded_property(self):
        """Test is_loaded property."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        assert not cache.is_loaded

        cache._loaded = True
        assert cache.is_loaded


class TestAssetCacheGetByIdentifier:
    """Test get_by_identifier method."""

    def test_get_by_identifier_with_empty_identifier(self, asset_map):
        """Test get_by_identifier with empty identifier returns None."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)
        cache._loaded = True

        result = cache.get_by_identifier("")
        assert result is None

        result = cache.get_by_identifier(None)
        assert result is None

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_cache_hit(self, mock_get_all, mock_asset):
        """Test get_by_identifier with cache hit."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = mock_asset
        cache._loaded = True

        result = cache.get_by_identifier("ASSET-001")

        assert result is mock_asset
        mock_get_all.assert_not_called()

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_triggers_warm_cache(self, mock_get_all, mock_assets, asset_map):
        """Test get_by_identifier triggers warm_cache when not loaded."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        assert not cache.is_loaded

        result = cache.get_by_identifier("ASSET-001")

        assert cache.is_loaded
        mock_get_all.assert_called_once_with(parent_id=123, parent_module="securityplans")
        assert result is mock_assets[0]

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_fallback_ip_address(self, mock_get_all, mock_assets):
        """Test get_by_identifier fallback to ipAddress."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        # Search by IP address when not in primary cache
        result = cache.get_by_identifier("192.168.1.2")

        assert result is mock_assets[1]
        assert result.ipAddress == "192.168.1.2"

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_fallback_fqdn(self, mock_get_all, mock_assets):
        """Test get_by_identifier fallback to FQDN."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        result = cache.get_by_identifier("asset1.example.com")

        assert result is mock_assets[0]
        assert result.fqdn == "asset1.example.com"

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_fallback_dns(self, mock_get_all, mock_assets):
        """Test get_by_identifier fallback to DNS."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        result = cache.get_by_identifier("dns2.example.com")

        assert result is mock_assets[1]
        assert result.dns == "dns2.example.com"

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_not_found_with_error(self, mock_get_all, mock_assets, caplog):
        """Test get_by_identifier logs error when asset not found."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans", suppress_not_found_errors=False)
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        with caplog.at_level(logging.ERROR):
            result = cache.get_by_identifier("NON-EXISTENT-ASSET")

        assert result is None
        assert "Asset not found for identifier 'NON-EXISTENT-ASSET'" in caplog.text

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_not_found_suppressed(self, mock_get_all, mock_assets, caplog):
        """Test get_by_identifier suppresses error when configured."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans", suppress_not_found_errors=True)
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        with caplog.at_level(logging.ERROR):
            result = cache.get_by_identifier("NON-EXISTENT-ASSET")

        assert result is None
        assert "Asset not found" not in caplog.text

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_by_identifier_error_logged_once(self, mock_get_all, mock_assets, caplog):
        """Test get_by_identifier only logs error once per identifier."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        with caplog.at_level(logging.ERROR):
            cache.get_by_identifier("NON-EXISTENT-1")
            cache.get_by_identifier("NON-EXISTENT-1")
            cache.get_by_identifier("NON-EXISTENT-2")

        error_count = sum(1 for record in caplog.records if "Asset not found" in record.message)
        assert error_count == 2  # Once for NON-EXISTENT-1, once for NON-EXISTENT-2


class TestAssetCacheGetMap:
    """Test get_map method."""

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_map_without_component_mapping(self, mock_get_all, mock_assets):
        """Test get_map without component mapping uses get_all_by_parent."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans", options_map_assets_to_components=False)

        result = cache.get_map()

        mock_get_all.assert_called_once_with(parent_id=123, parent_module="securityplans")
        assert len(result) == 3
        assert "ASSET-001" in result
        assert "ASSET-002" in result
        assert "ASSET-003" in result

    @patch(f"{PATH}.regscale_models.Asset.get_map")
    def test_get_map_with_component_mapping(self, mock_get_map, asset_map):
        """Test get_map with component mapping uses Asset.get_map."""
        mock_get_map.return_value = asset_map

        cache = AssetCache(
            plan_id=456, parent_module="components", is_component=True, options_map_assets_to_components=True
        )

        result = cache.get_map()

        mock_get_map.assert_called_once_with(plan_id=456, key_field="otherTrackingNumber", is_component=True)
        assert result == asset_map

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_map_with_custom_identifier_field(self, mock_get_all, mock_assets):
        """Test get_map with custom identifier field."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans", identifier_field="ipAddress")

        result = cache.get_map()

        assert "192.168.1.1" in result
        assert "192.168.1.2" in result
        # Asset 3 has None ipAddress so it shouldn't be in the map
        assert None not in result

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_map_filters_none_identifiers(self, mock_get_all):
        """Test get_map filters out assets with None identifier field."""
        asset_with_none = MagicMock(spec=regscale_models.Asset)
        asset_with_none.id = 99
        asset_with_none.otherTrackingNumber = None

        asset_with_value = MagicMock(spec=regscale_models.Asset)
        asset_with_value.id = 100
        asset_with_value.otherTrackingNumber = "ASSET-100"

        mock_get_all.return_value = [asset_with_none, asset_with_value]

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        result = cache.get_map()

        assert None not in result
        assert "ASSET-100" in result
        assert len(result) == 1


class TestAssetCacheWarmCache:
    """Test warm_cache and prime methods."""

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_warm_cache_populates_cache(self, mock_get_all, mock_assets, caplog):
        """Test warm_cache populates the cache."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        with caplog.at_level(logging.INFO):
            cache.warm_cache()

        assert cache.is_loaded
        assert len(cache) == 3
        assert "Warming asset cache for plan_id=123" in caplog.text
        mock_get_all.assert_called_once_with(parent_id=123, parent_module="securityplans")

    @patch(f"{PATH}.regscale_models.Asset.get_map")
    def test_warm_cache_with_component_mapping(self, mock_get_map, asset_map):
        """Test warm_cache with component mapping."""
        mock_get_map.return_value = asset_map

        cache = AssetCache(plan_id=456, parent_module="components", options_map_assets_to_components=True)

        cache.warm_cache()

        assert cache.is_loaded
        assert len(cache) == 3
        mock_get_map.assert_called_once()

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_prime_is_alias_for_warm_cache(self, mock_get_all, mock_assets):
        """Test prime method is an alias for warm_cache."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        cache.prime()

        assert cache.is_loaded
        assert len(cache) == 3
        mock_get_all.assert_called_once()


class TestAssetCacheAdd:
    """Test add and add_by_identifier methods."""

    def test_add_asset_with_identifier(self, mock_asset):
        """Test adding asset with valid identifier."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        cache.add(mock_asset)

        assert "ASSET-001" in cache._cache
        assert cache._cache["ASSET-001"] is mock_asset

    def test_add_asset_without_identifier(self, caplog):
        """Test adding asset without identifier logs warning."""
        asset = MagicMock(spec=regscale_models.Asset)
        asset.id = 999
        asset.otherTrackingNumber = None

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        with caplog.at_level(logging.WARNING):
            cache.add(asset)

        assert len(cache) == 0
        assert "Cannot add asset 999 to cache: missing identifier field" in caplog.text

    def test_add_asset_custom_identifier_field(self):
        """Test adding asset with custom identifier field."""
        asset = MagicMock(spec=regscale_models.Asset)
        asset.id = 1
        asset.ipAddress = "10.0.0.1"

        cache = AssetCache(plan_id=123, parent_module="securityplans", identifier_field="ipAddress")

        cache.add(asset)

        assert "10.0.0.1" in cache._cache

    def test_add_by_identifier(self, mock_asset):
        """Test add_by_identifier with custom identifier."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        cache.add_by_identifier("custom-id", mock_asset)

        assert "custom-id" in cache._cache
        assert cache._cache["custom-id"] is mock_asset

    def test_add_by_identifier_empty_identifier(self, mock_asset, caplog):
        """Test add_by_identifier with empty identifier logs warning."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        with caplog.at_level(logging.WARNING):
            cache.add_by_identifier("", mock_asset)

        assert len(cache) == 0
        assert "Cannot add asset to cache with empty identifier" in caplog.text


class TestAssetCacheUpdate:
    """Test update method."""

    def test_update_empty_cache(self, asset_map):
        """Test updating empty cache."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        cache.update(asset_map)

        assert len(cache) == 3
        assert cache.is_loaded  # Update marks cache as loaded if it wasn't empty

    def test_update_existing_cache(self, mock_assets, asset_map):
        """Test updating existing cache."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = mock_assets[0]
        cache._loaded = True

        new_asset = MagicMock(spec=regscale_models.Asset)
        new_asset.otherTrackingNumber = "ASSET-004"

        cache.update({"ASSET-004": new_asset})

        assert len(cache) == 2
        assert "ASSET-004" in cache._cache

    def test_update_with_empty_dict(self):
        """Test updating with empty dictionary."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        cache.update({})

        assert len(cache) == 0
        assert not cache.is_loaded  # Empty update doesn't mark as loaded


class TestAssetCacheRemove:
    """Test remove method."""

    def test_remove_existing_asset(self, mock_asset):
        """Test removing existing asset."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = mock_asset

        result = cache.remove("ASSET-001")

        assert result is mock_asset
        assert "ASSET-001" not in cache._cache

    def test_remove_nonexistent_asset(self):
        """Test removing nonexistent asset returns None."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")

        result = cache.remove("DOES-NOT-EXIST")

        assert result is None


class TestAssetCacheClear:
    """Test clear method."""

    def test_clear_cache(self, asset_map):
        """Test clearing cache."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)
        cache._loaded = True
        cache._alerted_identifiers.add("test-id")

        cache.clear()

        assert len(cache) == 0
        assert not cache.is_loaded
        assert len(cache._alerted_identifiers) == 0


class TestAssetCacheDunderMethods:
    """Test dunder methods (__len__, __contains__, etc.)."""

    def test_len(self, asset_map):
        """Test __len__ method."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)

        assert len(cache) == 3

    def test_contains(self, asset_map):
        """Test __contains__ method."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)

        assert "ASSET-001" in cache
        assert "ASSET-999" not in cache

    def test_keys(self, asset_map):
        """Test keys method."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)

        keys = cache.keys()

        assert "ASSET-001" in keys
        assert "ASSET-002" in keys
        assert "ASSET-003" in keys
        assert len(keys) == 3

    def test_values(self, asset_map, mock_assets):
        """Test values method."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)

        values = cache.values()

        assert mock_assets[0] in values
        assert mock_assets[1] in values
        assert mock_assets[2] in values
        assert len(values) == 3

    def test_items(self, asset_map, mock_assets):
        """Test items method."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache.update(asset_map)

        items = cache.items()

        assert ("ASSET-001", mock_assets[0]) in items
        assert ("ASSET-002", mock_assets[1]) in items
        assert ("ASSET-003", mock_assets[2]) in items
        assert len(items) == 3


class TestAssetCacheGet:
    """Test get method (without fallback)."""

    def test_get_existing_asset(self, mock_asset):
        """Test get with existing asset."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = mock_asset
        cache._loaded = True

        result = cache.get("ASSET-001")

        assert result is mock_asset

    def test_get_nonexistent_asset_returns_none(self):
        """Test get with nonexistent asset returns None."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True

        result = cache.get("DOES-NOT-EXIST")

        assert result is None

    def test_get_with_default_value(self):
        """Test get with default value."""
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True

        default_asset = MagicMock()
        result = cache.get("DOES-NOT-EXIST", default_asset)

        assert result is default_asset

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_get_no_fallback_lookup(self, mock_get_all, mock_assets):
        """Test get does not perform fallback lookups unlike get_by_identifier."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        # Try to get by IP address - should return None since get() doesn't do fallback
        result = cache.get("192.168.1.1")

        assert result is None
        mock_get_all.assert_not_called()


class TestAssetCacheThreadSafety:
    """Test thread safety of AssetCache."""

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_concurrent_get_by_identifier(self, mock_get_all, mock_assets):
        """Test concurrent get_by_identifier calls are thread-safe."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._loaded = True
        cache._cache.update({asset.otherTrackingNumber: asset for asset in mock_assets})

        results = []
        errors = []

        def get_asset(identifier):
            try:
                result = cache.get_by_identifier(identifier)
                results.append(result)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(50):
                futures.append(executor.submit(get_asset, "ASSET-001"))
                futures.append(executor.submit(get_asset, "ASSET-002"))
                futures.append(executor.submit(get_asset, "192.168.1.1"))

            for future in futures:
                future.result()

        assert len(errors) == 0
        assert len(results) == 150
        # All results for ASSET-001 should be the same object
        asset_001_results = [r for r in results if r and r.otherTrackingNumber == "ASSET-001"]
        assert all(r is mock_assets[0] for r in asset_001_results)

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_concurrent_add_operations(self, mock_get_all):
        """Test concurrent add operations are thread-safe."""
        mock_get_all.return_value = []

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        errors = []

        def add_asset(asset_id):
            try:
                asset = MagicMock(spec=regscale_models.Asset)
                asset.id = asset_id
                asset.otherTrackingNumber = f"ASSET-{asset_id:03d}"
                cache.add(asset)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_asset, i) for i in range(100)]
            for future in futures:
                future.result()

        assert len(errors) == 0
        assert len(cache) == 100

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_concurrent_warm_cache_calls(self, mock_get_all, mock_assets):
        """Test concurrent warm_cache calls are thread-safe."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        errors = []

        def warm():
            try:
                cache.warm_cache()
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(warm) for _ in range(10)]
            for future in futures:
                future.result()

        assert len(errors) == 0
        assert cache.is_loaded
        # get_all_by_parent might be called multiple times due to race conditions
        # but the cache should still be consistent
        assert len(cache) == 3


class TestAssetCacheEdgeCases:
    """Test edge cases and error scenarios."""

    def test_fallback_with_none_attributes(self):
        """Test fallback lookup handles None attribute values gracefully."""
        asset = MagicMock(spec=regscale_models.Asset)
        asset.id = 1
        asset.otherTrackingNumber = "ASSET-001"
        asset.ipAddress = None
        asset.fqdn = None
        asset.dns = None

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = asset
        cache._loaded = True

        # Should not match by None values
        result = cache.get_by_identifier(None)
        assert result is None

    def test_fallback_with_missing_attributes(self):
        """Test fallback lookup handles missing attributes gracefully."""
        asset = MagicMock(spec=regscale_models.Asset)
        asset.id = 1
        asset.otherTrackingNumber = "ASSET-001"
        # Simulate missing attributes by not setting them

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = asset
        cache._loaded = True

        # Should not crash when checking missing attributes
        result = cache.get_by_identifier("some-value")
        assert result is None

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_empty_result_from_api(self, mock_get_all):
        """Test handling empty result from API."""
        mock_get_all.return_value = []

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache.warm_cache()

        assert cache.is_loaded
        assert len(cache) == 0

    def test_multiple_assets_same_fallback_identifier(self):
        """Test behavior when multiple assets have the same fallback identifier."""
        asset1 = MagicMock(spec=regscale_models.Asset)
        asset1.id = 1
        asset1.otherTrackingNumber = "ASSET-001"
        asset1.ipAddress = "192.168.1.1"

        asset2 = MagicMock(spec=regscale_models.Asset)
        asset2.id = 2
        asset2.otherTrackingNumber = "ASSET-002"
        asset2.ipAddress = "192.168.1.1"  # Same IP

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache._cache["ASSET-001"] = asset1
        cache._cache["ASSET-002"] = asset2
        cache._loaded = True

        # Should return the first match found
        result = cache.get_by_identifier("192.168.1.1")
        assert result in [asset1, asset2]

    def test_special_characters_in_identifier(self):
        """Test handling of special characters in identifiers."""
        asset = MagicMock(spec=regscale_models.Asset)
        asset.id = 1
        asset.otherTrackingNumber = "ASSET-001/TEST@SPECIAL#CHARS"

        cache = AssetCache(plan_id=123, parent_module="securityplans")
        cache.add(asset)

        result = cache.get_by_identifier("ASSET-001/TEST@SPECIAL#CHARS")
        assert result is asset


class TestAssetCacheIntegration:
    """Integration tests combining multiple methods."""

    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_full_lifecycle(self, mock_get_all, mock_assets):
        """Test full lifecycle: warm, get, add, remove, clear."""
        mock_get_all.return_value = mock_assets

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        # Warm cache
        cache.warm_cache()
        assert len(cache) == 3
        assert cache.is_loaded

        # Get assets
        asset1 = cache.get_by_identifier("ASSET-001")
        assert asset1 is not None

        # Add new asset
        new_asset = MagicMock(spec=regscale_models.Asset)
        new_asset.id = 4
        new_asset.otherTrackingNumber = "ASSET-004"
        cache.add(new_asset)
        assert len(cache) == 4

        # Remove asset
        removed = cache.remove("ASSET-004")
        assert removed is new_asset
        assert len(cache) == 3

        # Clear cache
        cache.clear()
        assert len(cache) == 0
        assert not cache.is_loaded

    @patch(f"{PATH}.regscale_models.Asset.get_map")
    @patch(f"{PATH}.regscale_models.Asset.get_all_by_parent")
    def test_switching_component_mapping_mode(self, mock_get_all, mock_get_map, mock_assets, asset_map):
        """Test switching between component mapping modes."""
        mock_get_all.return_value = mock_assets
        mock_get_map.return_value = asset_map

        cache = AssetCache(plan_id=123, parent_module="securityplans")

        # Start without component mapping
        cache.warm_cache()
        mock_get_all.assert_called_once()
        mock_get_map.assert_not_called()

        # Clear and switch to component mapping
        cache.clear()
        cache.options_map_assets_to_components = True
        cache.warm_cache()
        mock_get_map.assert_called_once()

        assert len(cache) == 3
