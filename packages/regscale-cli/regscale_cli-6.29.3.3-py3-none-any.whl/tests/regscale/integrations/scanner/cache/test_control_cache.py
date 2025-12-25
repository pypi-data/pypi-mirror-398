#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for ControlCache class."""
import logging
import threading
from unittest.mock import MagicMock, patch, call
from collections import defaultdict

import pytest

from regscale.integrations.scanner.cache.control_cache import ControlCache
from regscale.utils.threading import ThreadSafeDict


class TestControlCacheInit:
    """Test ControlCache constructor initialization."""

    def test_init_with_defaults(self):
        """Test ControlCache initialization with default parameters."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        assert cache.plan_id == 123
        assert cache.parent_module == "SecurityPlans"
        assert cache._enable_cci_mapping is True
        assert cache._no_ccis is False
        assert cache._cci_map_loaded is False
        assert cache._control_label_map_loaded is False
        assert cache._control_id_map_loaded is False
        assert isinstance(cache._cci_to_control_map, ThreadSafeDict)
        assert isinstance(cache._control_label_to_impl_id_map, dict)
        assert isinstance(cache._control_id_to_impl_id_map, dict)
        assert isinstance(cache._impl_id_to_control_label_map, dict)
        # Verify locks are threading.Lock instances
        assert type(cache._cci_map_lock).__name__ == "lock"
        assert type(cache._control_label_map_lock).__name__ == "lock"
        assert type(cache._control_id_map_lock).__name__ == "lock"

    def test_init_with_cci_mapping_disabled(self):
        """Test ControlCache initialization with CCI mapping disabled."""
        cache = ControlCache(plan_id=456, parent_module="Components", enable_cci_mapping=False)

        assert cache.plan_id == 456
        assert cache.parent_module == "Components"
        assert cache._enable_cci_mapping is False
        assert cache._no_ccis is True
        assert cache._cci_map_loaded is False

    def test_init_with_different_plan_ids(self):
        """Test ControlCache initialization with different plan IDs."""
        cache1 = ControlCache(plan_id=100, parent_module="SecurityPlans")
        cache2 = ControlCache(plan_id=200, parent_module="Components")

        assert cache1.plan_id == 100
        assert cache2.plan_id == 200
        assert cache1.parent_module == "SecurityPlans"
        assert cache2.parent_module == "Components"


class TestGetCciToControlMap:
    """Test get_cci_to_control_map() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_success(self, mock_map_ccis):
        """Test successful loading of CCI to control map."""
        mock_map_ccis.return_value = {
            "CCI-000001": {101, 102},
            "CCI-000002": {103},
            "CCI-000366": {104},
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_cci_to_control_map()

        assert len(result) == 3
        assert result.get("CCI-000001") == {101, 102}
        assert result.get("CCI-000002") == {103}
        assert result.get("CCI-000366") == {104}
        assert cache._cci_map_loaded is True
        assert cache._no_ccis is False
        mock_map_ccis.assert_called_once_with(parent_id=123)

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_empty_result(self, mock_map_ccis):
        """Test loading CCI map when API returns empty result."""
        mock_map_ccis.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_cci_to_control_map()

        assert len(result) == 0
        assert cache._cci_map_loaded is True
        assert cache._no_ccis is True
        mock_map_ccis.assert_called_once_with(parent_id=123)

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_none_result(self, mock_map_ccis):
        """Test loading CCI map when API returns None."""
        mock_map_ccis.return_value = None

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_cci_to_control_map()

        assert len(result) == 0
        assert cache._cci_map_loaded is True
        assert cache._no_ccis is True
        mock_map_ccis.assert_called_once_with(parent_id=123)

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_exception(self, mock_map_ccis):
        """Test CCI map loading when exception occurs."""
        mock_map_ccis.side_effect = Exception("API error")

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_cci_to_control_map()

        assert len(result) == 0
        assert cache._cci_map_loaded is True
        assert cache._no_ccis is True
        mock_map_ccis.assert_called_once_with(parent_id=123)

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_lazy_loading(self, mock_map_ccis):
        """Test CCI map is only loaded once (lazy loading)."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # Call multiple times
        result1 = cache.get_cci_to_control_map()
        result2 = cache.get_cci_to_control_map()
        result3 = cache.get_cci_to_control_map()

        assert result1.get("CCI-000001") == {101}
        assert result2.get("CCI-000001") == {101}
        assert result3.get("CCI-000001") == {101}
        # API should only be called once
        mock_map_ccis.assert_called_once_with(parent_id=123)

    def test_get_cci_to_control_map_disabled(self):
        """Test get_cci_to_control_map with CCI mapping disabled."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans", enable_cci_mapping=False)

        result = cache.get_cci_to_control_map()

        assert len(result) == 0
        assert cache._no_ccis is True
        assert cache._cci_map_loaded is False

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_fast_path_no_ccis(self, mock_map_ccis):
        """Test fast path when _no_ccis is True."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache._no_ccis = True

        result = cache.get_cci_to_control_map()

        assert len(result) == 0
        mock_map_ccis.assert_not_called()

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_cci_to_control_map_fast_path_loaded(self, mock_map_ccis):
        """Test fast path when map is already loaded."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # First call loads the map
        cache.get_cci_to_control_map()
        mock_map_ccis.assert_called_once()

        # Reset mock to verify no additional calls
        mock_map_ccis.reset_mock()

        # Second call should use fast path
        result = cache.get_cci_to_control_map()

        assert result.get("CCI-000001") == {101}
        mock_map_ccis.assert_not_called()


class TestGetControlToCciMap:
    """Test get_control_to_cci_map() method (reverse mapping)."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_control_to_cci_map_success(self, mock_map_ccis):
        """Test successful reverse mapping from control IDs to CCIs."""
        mock_map_ccis.return_value = {
            "CCI-000001": {101, 102},
            "CCI-000002": {102, 103},
            "CCI-000366": {104},
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_to_cci_map()

        assert result[101] == {"CCI-000001"}
        assert result[102] == {"CCI-000001", "CCI-000002"}
        assert result[103] == {"CCI-000002"}
        assert result[104] == {"CCI-000366"}

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_control_to_cci_map_empty(self, mock_map_ccis):
        """Test reverse mapping with empty CCI map."""
        mock_map_ccis.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_to_cci_map()

        assert len(result) == 0
        assert isinstance(result, dict)

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_control_to_cci_map_single_entry(self, mock_map_ccis):
        """Test reverse mapping with single CCI entry."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_to_cci_map()

        assert result[101] == {"CCI-000001"}
        assert len(result) == 1


class TestGetImplementationIdForCci:
    """Test get_implementation_id_for_cci() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_success(self, mock_map_ccis, mock_control_id_map):
        """Test successful retrieval of implementation ID for a CCI."""
        mock_map_ccis.return_value = {
            "CCI-000001": {101},
            "CCI-000366": {104},
        }
        mock_control_id_map.return_value = {
            101: 201,
            104: 204,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-000001")

        assert result == 201

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_fallback_to_366(self, mock_map_ccis, mock_control_id_map):
        """Test fallback to CCI-000366 when CCI not found."""
        mock_map_ccis.return_value = {
            "CCI-000366": {104},
        }
        mock_control_id_map.return_value = {
            104: 204,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-999999")

        assert result == 204

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_none_cci(self, mock_map_ccis, mock_control_id_map):
        """Test handling of None CCI."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci(None)

        assert result is None
        mock_map_ccis.assert_not_called()
        mock_control_id_map.assert_not_called()

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_empty_string(self, mock_map_ccis, mock_control_id_map):
        """Test handling of empty string CCI."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("")

        assert result is None
        mock_map_ccis.assert_not_called()
        mock_control_id_map.assert_not_called()

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_not_in_map(self, mock_map_ccis, mock_control_id_map):
        """Test when CCI and fallback CCI-000366 are not in map."""
        mock_map_ccis.return_value = {}
        mock_control_id_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-000001")

        assert result is None

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_no_implementation(self, mock_map_ccis, mock_control_id_map):
        """Test when control ID has no implementation ID mapping."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}
        mock_control_id_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-000001")

        assert result is None

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_for_cci_multiple_control_ids(self, mock_map_ccis, mock_control_id_map):
        """Test when CCI maps to multiple control IDs (returns first with implementation)."""
        mock_map_ccis.return_value = {
            "CCI-000001": {101, 102, 103},
        }
        mock_control_id_map.return_value = {
            102: 202,
            103: 203,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-000001")

        # Should return one of the implementation IDs
        assert result in [202, 203]


class TestGetControlLabelToImplementationMap:
    """Test get_control_label_to_implementation_map() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_control_label_map_success(self, mock_control_label_map):
        """Test successful loading of control label to implementation ID map."""
        mock_control_label_map.return_value = {
            "AC-1": 201,
            "AC-2": 202,
            "SC-7": 207,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_label_to_implementation_map()

        assert len(result) == 3
        assert result["AC-1"] == 201
        assert result["AC-2"] == 202
        assert result["SC-7"] == 207
        assert cache._control_label_map_loaded is True
        mock_control_label_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_control_label_map_empty(self, mock_control_label_map):
        """Test loading control label map when API returns empty result."""
        mock_control_label_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_label_to_implementation_map()

        assert len(result) == 0
        assert cache._control_label_map_loaded is True
        mock_control_label_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_control_label_map_exception(self, mock_control_label_map):
        """Test control label map loading when exception occurs."""
        mock_control_label_map.side_effect = Exception("API error")

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_label_to_implementation_map()

        assert len(result) == 0
        assert cache._control_label_map_loaded is True
        mock_control_label_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_control_label_map_lazy_loading(self, mock_control_label_map):
        """Test control label map is only loaded once (lazy loading)."""
        mock_control_label_map.return_value = {"AC-1": 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # Call multiple times
        result1 = cache.get_control_label_to_implementation_map()
        result2 = cache.get_control_label_to_implementation_map()
        result3 = cache.get_control_label_to_implementation_map()

        assert result1["AC-1"] == 201
        assert result2["AC-1"] == 201
        assert result3["AC-1"] == 201
        # API should only be called once
        mock_control_label_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_control_label_map_builds_reverse_map(self, mock_control_label_map):
        """Test that loading control label map also builds reverse mapping."""
        mock_control_label_map.return_value = {
            "AC-1": 201,
            "AC-2": 202,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache.get_control_label_to_implementation_map()

        # Check reverse mapping was built
        assert cache._impl_id_to_control_label_map[201] == "AC-1"
        assert cache._impl_id_to_control_label_map[202] == "AC-2"


class TestGetControlIdToImplementationMap:
    """Test get_control_id_to_implementation_map() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    def test_get_control_id_map_success(self, mock_control_id_map):
        """Test successful loading of control ID to implementation ID map."""
        mock_control_id_map.return_value = {
            101: 201,
            102: 202,
            107: 207,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_id_to_implementation_map()

        assert len(result) == 3
        assert result[101] == 201
        assert result[102] == 202
        assert result[107] == 207
        assert cache._control_id_map_loaded is True
        mock_control_id_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    def test_get_control_id_map_empty(self, mock_control_id_map):
        """Test loading control ID map when API returns empty result."""
        mock_control_id_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_id_to_implementation_map()

        assert len(result) == 0
        assert cache._control_id_map_loaded is True
        mock_control_id_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    def test_get_control_id_map_exception(self, mock_control_id_map):
        """Test control ID map loading when exception occurs."""
        mock_control_id_map.side_effect = Exception("API error")

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_id_to_implementation_map()

        assert len(result) == 0
        assert cache._control_id_map_loaded is True
        mock_control_id_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    def test_get_control_id_map_lazy_loading(self, mock_control_id_map):
        """Test control ID map is only loaded once (lazy loading)."""
        mock_control_id_map.return_value = {101: 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # Call multiple times
        result1 = cache.get_control_id_to_implementation_map()
        result2 = cache.get_control_id_to_implementation_map()
        result3 = cache.get_control_id_to_implementation_map()

        assert result1[101] == 201
        assert result2[101] == 201
        assert result3[101] == 201
        # API should only be called once
        mock_control_id_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")


class TestGetImplementationIdForControlLabel:
    """Test get_implementation_id_for_control_label() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_implementation_id_for_control_label_success(self, mock_control_label_map):
        """Test successful retrieval of implementation ID for a control label."""
        mock_control_label_map.return_value = {"AC-1": 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_control_label("AC-1")

        assert result == 201

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_implementation_id_for_control_label_not_found(self, mock_control_label_map):
        """Test retrieval when control label not found."""
        mock_control_label_map.return_value = {"AC-1": 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_control_label("SC-7")

        assert result is None


class TestGetImplementationIdToControlLabelMap:
    """Test get_implementation_id_to_control_label_map() method."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_reverse_map_success(self, mock_control_label_map):
        """Test successful retrieval of reverse mapping."""
        mock_control_label_map.return_value = {
            "AC-1": 201,
            "AC-2": 202,
        }

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_to_control_label_map()

        assert len(result) == 2
        assert result[201] == "AC-1"
        assert result[202] == "AC-2"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_get_reverse_map_empty(self, mock_control_label_map):
        """Test reverse mapping with empty control label map."""
        mock_control_label_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_to_control_label_map()

        assert len(result) == 0


class TestControlCacheHelperMethods:
    """Test helper methods: load_cci_map, load_control_maps, clear."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_load_cci_map(self, mock_map_ccis):
        """Test explicit CCI map loading."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache.load_cci_map()

        assert cache._cci_map_loaded is True
        mock_map_ccis.assert_called_once_with(parent_id=123)

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_load_control_maps(self, mock_label_map, mock_id_map):
        """Test explicit control maps loading."""
        mock_label_map.return_value = {"AC-1": 201}
        mock_id_map.return_value = {101: 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache.load_control_maps()

        assert cache._control_label_map_loaded is True
        assert cache._control_id_map_loaded is True
        mock_label_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")
        mock_id_map.assert_called_once_with(parent_id=123, parent_module="SecurityPlans")

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_clear_all_caches(self, mock_map_ccis, mock_label_map, mock_id_map):
        """Test clearing all cached mappings."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}
        mock_label_map.return_value = {"AC-1": 201}
        mock_id_map.return_value = {101: 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # Load all maps
        cache.get_cci_to_control_map()
        cache.get_control_label_to_implementation_map()
        cache.get_control_id_to_implementation_map()

        assert cache._cci_map_loaded is True
        assert cache._control_label_map_loaded is True
        assert cache._control_id_map_loaded is True

        # Clear all caches
        cache.clear()

        assert cache._cci_map_loaded is False
        assert cache._control_label_map_loaded is False
        assert cache._control_id_map_loaded is False
        assert len(cache._cci_to_control_map) == 0
        assert len(cache._control_label_to_impl_id_map) == 0
        assert len(cache._control_id_to_impl_id_map) == 0
        assert cache._no_ccis is False


class TestControlCacheProperties:
    """Test ControlCache properties."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    def test_is_cci_map_loaded_false(self):
        """Test is_cci_map_loaded property when not loaded."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        assert cache.is_cci_map_loaded is False

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_is_cci_map_loaded_true(self, mock_map_ccis):
        """Test is_cci_map_loaded property when loaded."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache.get_cci_to_control_map()

        assert cache.is_cci_map_loaded is True

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_has_ccis_true(self, mock_map_ccis):
        """Test has_ccis property when CCIs are available."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        assert cache.has_ccis is True

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_has_ccis_false(self, mock_map_ccis):
        """Test has_ccis property when no CCIs are available."""
        mock_map_ccis.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        assert cache.has_ccis is False

    def test_has_ccis_disabled(self):
        """Test has_ccis property when CCI mapping is disabled."""
        cache = ControlCache(plan_id=123, parent_module="SecurityPlans", enable_cci_mapping=False)
        assert cache.has_ccis is False


class TestControlCacheThreadSafety:
    """Test thread safety of ControlCache."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_concurrent_cci_map_access(self, mock_map_ccis):
        """Test thread safety of CCI map loading."""
        mock_map_ccis.return_value = {"CCI-000001": {101}}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        results = []

        def load_map():
            result = cache.get_cci_to_control_map()
            results.append(result)

        # Create multiple threads
        threads = [threading.Thread(target=load_map) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify API was called only once due to double-checked locking
        assert mock_map_ccis.call_count == 1

        # Verify all threads got the same result
        for result in results:
            assert result.get("CCI-000001") == {101}

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_concurrent_control_label_map_access(self, mock_label_map):
        """Test thread safety of control label map loading."""
        mock_label_map.return_value = {"AC-1": 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        results = []

        def load_map():
            result = cache.get_control_label_to_implementation_map()
            results.append(result)

        # Create multiple threads
        threads = [threading.Thread(target=load_map) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify API was called only once due to double-checked locking
        assert mock_label_map.call_count == 1

        # Verify all threads got the same result
        for result in results:
            assert result["AC-1"] == 201

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    def test_concurrent_control_id_map_access(self, mock_id_map):
        """Test thread safety of control ID map loading."""
        mock_id_map.return_value = {101: 201}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        results = []

        def load_map():
            result = cache.get_control_id_to_implementation_map()
            results.append(result)

        # Create multiple threads
        threads = [threading.Thread(target=load_map) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify API was called only once due to double-checked locking
        assert mock_id_map.call_count == 1

        # Verify all threads got the same result
        for result in results:
            assert result[101] == 201


class TestControlCacheDoubleCheckedLocking:
    """Test double-checked locking pattern verification."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_double_checked_locking_cci_map(self, mock_map_ccis):
        """Test double-checked locking prevents multiple API calls for CCI map."""
        call_count = 0

        def slow_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate slow API call
            import time

            time.sleep(0.01)
            return {"CCI-000001": {101}}

        mock_map_ccis.side_effect = slow_api_call

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        # Simulate concurrent access
        def access_map():
            cache.get_cci_to_control_map()

        threads = [threading.Thread(target=access_map) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should only be called once despite multiple concurrent accesses
        assert call_count == 1
        assert cache._cci_map_loaded is True

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_double_checked_locking_control_label_map(self, mock_label_map):
        """Test double-checked locking prevents multiple API calls for control label map."""
        call_count = 0

        def slow_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            import time

            time.sleep(0.01)
            return {"AC-1": 201}

        mock_label_map.side_effect = slow_api_call

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")

        def access_map():
            cache.get_control_label_to_implementation_map()

        threads = [threading.Thread(target=access_map) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert call_count == 1
        assert cache._control_label_map_loaded is True


class TestControlCacheEdgeCases:
    """Test edge cases and error conditions."""

    PATH = "regscale.integrations.scanner.cache.control_cache"

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_get_implementation_id_with_cci_366_missing(self, mock_map_ccis, mock_control_id_map):
        """Test when even the fallback CCI-000366 is missing."""
        mock_map_ccis.return_value = {}
        mock_control_id_map.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_implementation_id_for_cci("CCI-000001")

        assert result is None

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_label_map_by_parent")
    def test_exception_during_label_map_loading_creates_empty_maps(self, mock_label_map):
        """Test that exception during loading creates empty maps."""
        mock_label_map.side_effect = Exception("API error")

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        result = cache.get_control_label_to_implementation_map()

        assert result == {}
        assert cache._impl_id_to_control_label_map == {}
        assert cache._control_label_map_loaded is True

    def test_multiple_cache_instances_independent(self):
        """Test that multiple cache instances are independent."""
        cache1 = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache2 = ControlCache(plan_id=456, parent_module="Components")

        cache1._no_ccis = True

        assert cache1._no_ccis is True
        assert cache2._no_ccis is False

    @patch(f"{PATH}.regscale_models.ControlImplementation.get_control_id_map_by_parent")
    @patch(f"{PATH}.regscale_models.map_ccis_to_control_ids")
    def test_clear_resets_no_ccis_flag(self, mock_map_ccis, mock_control_id_map):
        """Test that clear() resets the _no_ccis flag."""
        mock_map_ccis.return_value = {}

        cache = ControlCache(plan_id=123, parent_module="SecurityPlans")
        cache.get_cci_to_control_map()

        assert cache._no_ccis is True

        cache.clear()

        assert cache._no_ccis is False
        assert cache._cci_map_loaded is False
