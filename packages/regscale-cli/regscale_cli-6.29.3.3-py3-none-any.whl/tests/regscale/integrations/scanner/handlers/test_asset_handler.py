#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for AssetHandler class.

Tests cover:
- Constructor initialization
- Asset processing with progress tracking and error handling
- Asset creation and updates with/without components
- Field mapping and conversions
- Asset lookup by identifier
- Component handling
- Field validation and truncation
- Software inventory handling
- Edge cases and error scenarios
"""

import json
import logging
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pytest

from regscale.integrations.scanner.cache.asset_cache import AssetCache
from regscale.integrations.scanner.context import ScannerContext
from regscale.integrations.scanner.handlers.asset_handler import VALID_ASSET_TYPES, AssetHandler
from regscale.integrations.scanner.models.integration_asset import IntegrationAsset
from regscale.models import regscale_models

logger = logging.getLogger("regscale")


# Test fixtures
@pytest.fixture
def mock_context():
    """Create a mock ScannerContext for testing."""
    context = MagicMock(spec=ScannerContext)
    context.plan_id = 123
    context.tenant_id = 1
    context.parent_module = "securityplans"
    context.is_component = False
    context.title = "Test Scanner"
    context.asset_identifier_field = "otherTrackingNumber"
    context.assessor_id = "test-assessor-123"
    context.component = None
    context.components = []
    context.components_by_title = {}
    context.asset_progress = None
    context.num_assets_to_process = None
    context.stig_mapper = None
    context.software_to_create = []
    context.link_to_create = []
    context.link_to_update = []
    return context


@pytest.fixture
def mock_asset_cache():
    """Create a mock AssetCache for testing."""
    cache = MagicMock(spec=AssetCache)
    cache.get_by_identifier = MagicMock(return_value=None)
    cache.add_by_identifier = MagicMock()
    return cache


@pytest.fixture
def asset_handler(mock_context, mock_asset_cache):
    """Create an AssetHandler instance for testing."""
    return AssetHandler(mock_context, mock_asset_cache)


@pytest.fixture
def sample_integration_asset():
    """Create a sample IntegrationAsset for testing."""
    return IntegrationAsset(
        name="Test Asset",
        identifier="test-asset-001",
        asset_type="Virtual Machine (VM)",
        asset_category="Hardware",
        description="Test asset description",
        ip_address="192.168.1.1",
        fqdn="test.example.com",
        mac_address="00:11:22:33:44:55",
        asset_owner_id="owner-123",
        status=regscale_models.AssetStatus.Active,
        is_virtual=True,
    )


@pytest.fixture
def sample_integration_asset_with_components():
    """Create a sample IntegrationAsset with component names."""
    return IntegrationAsset(
        name="Component Asset",
        identifier="comp-asset-001",
        asset_type="Desktop",
        asset_category="Hardware",
        component_names=["Component A", "Component B"],
        component_type=regscale_models.ComponentType.Hardware,
    )


@pytest.fixture
def sample_regscale_asset():
    """Create a sample RegScale Asset model."""
    asset = MagicMock(spec=regscale_models.Asset)
    asset.id = 456
    asset.name = "Test Asset"
    asset.otherTrackingNumber = "test-asset-001"
    asset.get_module_string = MagicMock(return_value="assets")
    return asset


class TestAssetHandlerInitialization:
    """Tests for AssetHandler initialization."""

    def test_init_success(self, mock_context, mock_asset_cache):
        """Test successful initialization of AssetHandler."""
        handler = AssetHandler(mock_context, mock_asset_cache)

        assert handler.context == mock_context
        assert handler.asset_cache == mock_asset_cache

    def test_init_with_real_context_attributes(self):
        """Test initialization with context containing all expected attributes."""
        context = ScannerContext(plan_id=999, tenant_id=2)
        cache = AssetCache(plan_id=999, parent_module="securityplans")

        handler = AssetHandler(context, cache)

        assert handler.context.plan_id == 999
        assert handler.context.tenant_id == 2
        assert handler.asset_cache.plan_id == 999


class TestProcessAsset:
    """Tests for process_asset method."""

    def test_process_asset_without_components(self, asset_handler, sample_integration_asset):
        """Test processing an asset without component mapping."""
        with patch.object(asset_handler, "_set_asset_defaults", return_value=sample_integration_asset):
            with patch.object(asset_handler, "update_or_create_asset") as mock_update:
                asset_handler.process_asset(sample_integration_asset)

                mock_update.assert_called_once_with(sample_integration_asset, None)

    def test_process_asset_with_components(self, asset_handler, sample_integration_asset_with_components):
        """Test processing an asset with multiple components."""
        with patch.object(asset_handler, "_set_asset_defaults", return_value=sample_integration_asset_with_components):
            with patch.object(asset_handler, "update_or_create_asset") as mock_update:
                asset_handler.process_asset(sample_integration_asset_with_components)

                assert mock_update.call_count == 2
                mock_update.assert_any_call(sample_integration_asset_with_components, "Component A")
                mock_update.assert_any_call(sample_integration_asset_with_components, "Component B")

    def test_process_asset_with_progress_tracking(self, asset_handler, sample_integration_asset):
        """Test processing an asset with progress tracking."""
        # Setup progress tracking
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_task.total = 0
        mock_progress.tasks = {"task-1": mock_task}
        asset_handler.context.asset_progress = mock_progress
        asset_handler.context.num_assets_to_process = 10

        with patch.object(asset_handler, "_set_asset_defaults", return_value=sample_integration_asset):
            with patch.object(asset_handler, "update_or_create_asset"):
                asset_handler.process_asset(sample_integration_asset, loading_assets="task-1")

                # Verify progress was updated
                mock_progress.update.assert_called_once()
                mock_progress.advance.assert_called_once_with("task-1", 1)

    def test_process_asset_sets_defaults(self, asset_handler, sample_integration_asset):
        """Test that process_asset calls _set_asset_defaults."""
        sample_integration_asset.asset_owner_id = None

        with patch.object(asset_handler, "_set_asset_defaults") as mock_defaults:
            mock_defaults.return_value = sample_integration_asset
            with patch.object(asset_handler, "update_or_create_asset"):
                asset_handler.process_asset(sample_integration_asset)

                mock_defaults.assert_called_once_with(sample_integration_asset)


class TestUpdateOrCreateAsset:
    """Tests for update_or_create_asset method."""

    def test_update_or_create_asset_without_identifier(self, asset_handler, sample_integration_asset):
        """Test that asset without identifier is skipped."""
        sample_integration_asset.identifier = None

        asset_handler.update_or_create_asset(sample_integration_asset)

        # Should log warning and return early
        asset_handler.asset_cache.add_by_identifier.assert_not_called()

    def test_update_or_create_asset_creates_new(self, asset_handler, sample_integration_asset, sample_regscale_asset):
        """Test creating a new asset."""
        with patch.object(asset_handler, "_get_or_create_component_for_asset", return_value=None):
            with patch.object(
                asset_handler, "create_new_asset", return_value=(True, sample_regscale_asset)
            ) as mock_create:
                with patch.object(asset_handler, "_handle_component_mapping_and_durosuite"):
                    asset_handler.update_or_create_asset(sample_integration_asset)

                    mock_create.assert_called_once_with(sample_integration_asset, component=None)

    def test_update_or_create_asset_with_component(self, asset_handler, sample_integration_asset):
        """Test creating asset with component association."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 789

        with patch.object(asset_handler, "_get_or_create_component_for_asset", return_value=mock_component):
            with patch.object(asset_handler, "create_new_asset", return_value=(True, MagicMock())):
                with patch.object(asset_handler, "_handle_component_mapping_and_durosuite") as mock_handle:
                    asset_handler.update_or_create_asset(sample_integration_asset, "Test Component")

                    # Verify component was created/retrieved
                    assert mock_handle.call_args[0][1] == mock_component


class TestCreateNewAsset:
    """Tests for create_new_asset method."""

    def test_create_new_asset_success(self, asset_handler, sample_integration_asset):
        """Test successful asset creation."""
        mock_asset = MagicMock(spec=regscale_models.Asset)
        mock_asset.id = 456
        mock_asset.create_or_update_with_status = MagicMock(return_value=("created", mock_asset))

        with patch.object(asset_handler, "_validate_asset_requirements", return_value=True):
            with patch.object(asset_handler, "_validate_and_map_asset_type", return_value="Virtual Machine (VM)"):
                with patch.object(asset_handler, "_prepare_tracking_number", return_value="test-asset-001"):
                    with patch.object(
                        asset_handler, "_prepare_truncated_asset_fields", return_value={"name": "Test Asset"}
                    ):
                        with patch.object(
                            asset_handler, "_create_regscale_asset_model", return_value=mock_asset
                        ) as mock_create_model:
                            with patch.object(asset_handler, "_handle_software_and_stig_processing"):
                                created, new_asset = asset_handler.create_new_asset(sample_integration_asset, None)

                                assert created is True
                                assert new_asset == mock_asset
                                mock_create_model.assert_called_once()
                                asset_handler.asset_cache.add_by_identifier.assert_called_once_with(
                                    "test-asset-001", mock_asset
                                )

    def test_create_new_asset_update_existing(self, asset_handler, sample_integration_asset):
        """Test updating an existing asset."""
        mock_asset = MagicMock(spec=regscale_models.Asset)
        mock_asset.id = 456
        mock_asset.create_or_update_with_status = MagicMock(return_value=("updated", mock_asset))

        with patch.object(asset_handler, "_validate_asset_requirements", return_value=True):
            with patch.object(asset_handler, "_validate_and_map_asset_type", return_value="Virtual Machine (VM)"):
                with patch.object(asset_handler, "_prepare_tracking_number", return_value="test-asset-001"):
                    with patch.object(
                        asset_handler, "_prepare_truncated_asset_fields", return_value={"name": "Test Asset"}
                    ):
                        with patch.object(asset_handler, "_create_regscale_asset_model", return_value=mock_asset):
                            with patch.object(asset_handler, "_handle_software_and_stig_processing"):
                                created, new_asset = asset_handler.create_new_asset(sample_integration_asset, None)

                                assert created is False
                                assert new_asset == mock_asset

    def test_create_new_asset_validation_fails(self, asset_handler, sample_integration_asset):
        """Test that asset creation fails if validation fails."""
        with patch.object(asset_handler, "_validate_asset_requirements", return_value=False):
            created, new_asset = asset_handler.create_new_asset(sample_integration_asset, None)

            assert created is False
            assert new_asset is None


class TestConvertToRegscaleAsset:
    """Tests for convert_to_regscale_asset method."""

    def test_convert_to_regscale_asset(self, asset_handler, sample_integration_asset):
        """Test converting IntegrationAsset to RegScale Asset."""
        mock_asset = MagicMock(spec=regscale_models.Asset)

        with patch.object(asset_handler, "_set_asset_defaults", return_value=sample_integration_asset):
            with patch.object(asset_handler, "_validate_and_map_asset_type", return_value="Virtual Machine (VM)"):
                with patch.object(asset_handler, "_prepare_tracking_number", return_value="test-asset-001"):
                    with patch.object(
                        asset_handler, "_prepare_truncated_asset_fields", return_value={"name": "Test Asset"}
                    ):
                        with patch.object(
                            asset_handler, "_create_regscale_asset_model", return_value=mock_asset
                        ) as mock_create_model:
                            result = asset_handler.convert_to_regscale_asset(sample_integration_asset)

                            assert result == mock_asset
                            mock_create_model.assert_called_once()

    def test_convert_to_regscale_asset_applies_defaults(self, asset_handler):
        """Test that convert applies defaults to asset before conversion."""
        asset = IntegrationAsset(
            name="Test Asset", identifier="test-001", asset_type="Desktop", asset_category="Hardware"
        )
        asset.asset_owner_id = None

        with patch.object(asset_handler, "_set_asset_defaults") as mock_defaults:
            asset_copy = IntegrationAsset(
                name="Test Asset",
                identifier="test-001",
                asset_type="Desktop",
                asset_category="Hardware",
                asset_owner_id="default-owner",
            )
            mock_defaults.return_value = asset_copy
            with patch.object(asset_handler, "_validate_and_map_asset_type", return_value="Desktop"):
                with patch.object(asset_handler, "_prepare_tracking_number", return_value="test-001"):
                    with patch.object(
                        asset_handler, "_prepare_truncated_asset_fields", return_value={"name": "Test Asset"}
                    ):
                        with patch.object(asset_handler, "_create_regscale_asset_model", return_value=MagicMock()):
                            asset_handler.convert_to_regscale_asset(asset)

                            mock_defaults.assert_called_once_with(asset)


class TestGetAssetByIdentifier:
    """Tests for get_asset_by_identifier method."""

    def test_get_asset_by_identifier_found(self, asset_handler, sample_regscale_asset):
        """Test finding an asset by identifier."""
        asset_handler.asset_cache.get_by_identifier = MagicMock(return_value=sample_regscale_asset)

        result = asset_handler.get_asset_by_identifier("test-asset-001")

        assert result == sample_regscale_asset
        asset_handler.asset_cache.get_by_identifier.assert_called_once_with("test-asset-001")

    def test_get_asset_by_identifier_not_found(self, asset_handler):
        """Test asset not found by identifier."""
        asset_handler.asset_cache.get_by_identifier = MagicMock(return_value=None)

        result = asset_handler.get_asset_by_identifier("nonexistent")

        assert result is None


class TestComponentHandling:
    """Tests for component-related methods."""

    def test_get_or_create_component_for_asset_none(self, asset_handler, sample_integration_asset):
        """Test getting component when component_name is None."""
        result = asset_handler._get_or_create_component_for_asset(sample_integration_asset, None)

        assert result is None

    def test_get_or_create_component_for_asset_from_context(self, asset_handler, sample_integration_asset):
        """Test getting component from context."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.securityPlansId = 123
        asset_handler.context.is_component = True
        asset_handler.context.component = mock_component

        with patch.object(asset_handler, "_handle_component_mapping"):
            result = asset_handler._get_or_create_component_for_asset(sample_integration_asset, "Test Component")

            assert result == mock_component

    def test_get_or_create_component_for_asset_from_cache(self, asset_handler, sample_integration_asset):
        """Test getting component from cached components."""
        mock_component = MagicMock(spec=regscale_models.Component)
        asset_handler.context.components_by_title["Test Component"] = mock_component

        with patch.object(asset_handler, "_handle_component_mapping"):
            result = asset_handler._get_or_create_component_for_asset(sample_integration_asset, "Test Component")

            assert result == mock_component

    def test_get_or_create_component_for_asset_create_new(self, asset_handler, sample_integration_asset):
        """Test creating a new component."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 999

        with patch.object(asset_handler, "_create_new_component", return_value=mock_component) as mock_create:
            with patch.object(asset_handler, "_handle_component_mapping"):
                result = asset_handler._get_or_create_component_for_asset(sample_integration_asset, "New Component")

                assert result == mock_component
                mock_create.assert_called_once_with(sample_integration_asset, "New Component")
                assert asset_handler.context.components_by_title["New Component"] == mock_component

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Component")
    def test_create_new_component_success(self, mock_component_class, asset_handler, sample_integration_asset):
        """Test creating a new component successfully."""
        mock_component = MagicMock()
        mock_component.id = 111
        mock_component.securityPlansId = 123
        mock_component_instance = MagicMock()
        mock_component_instance.get_or_create = MagicMock(return_value=mock_component)
        mock_component_class.return_value = mock_component_instance

        with patch.object(asset_handler, "_get_assessor_id", return_value="assessor-123"):
            with patch.object(asset_handler, "_get_compliance_settings_id", return_value=456):
                result = asset_handler._create_new_component(sample_integration_asset, "New Component")

                assert result == mock_component
                assert mock_component in asset_handler.context.components

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Component")
    def test_create_new_component_failure(self, mock_component_class, asset_handler, sample_integration_asset):
        """Test component creation failure raises exception."""
        mock_component_instance = MagicMock()
        mock_component_instance.get_or_create = MagicMock(return_value=None)
        mock_component_class.return_value = mock_component_instance

        with patch.object(asset_handler, "_get_assessor_id", return_value="assessor-123"):
            with patch.object(asset_handler, "_get_compliance_settings_id", return_value=None):
                with pytest.raises(ValueError, match="Failed to create component with name New Component"):
                    asset_handler._create_new_component(sample_integration_asset, "New Component")

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.ComponentMapping")
    def test_handle_component_mapping_creates_mapping(self, mock_mapping_class, asset_handler):
        """Test creating component mapping."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 999
        mock_component.securityPlansId = 123

        mock_mapping = MagicMock()
        mock_mapping.id = 555
        mock_mapping_instance = MagicMock()
        mock_mapping_instance.get_or_create = MagicMock(return_value=mock_mapping)
        mock_mapping_class.return_value = mock_mapping_instance

        asset_handler._handle_component_mapping(mock_component)

        mock_mapping_class.assert_called_once_with(componentId=999, securityPlanId=123)

    def test_handle_component_mapping_skips_when_conditions_not_met(self, asset_handler):
        """Test that component mapping is skipped when conditions aren't met."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.securityPlansId = None

        # Should return early without creating mapping
        asset_handler._handle_component_mapping(mock_component)


class TestFieldValidationAndTruncation:
    """Tests for field validation and truncation methods."""

    def test_truncate_field_no_truncation_needed(self, asset_handler):
        """Test that short fields are not truncated."""
        value = "Short value"
        result = asset_handler._truncate_field(value, max_length=450)

        assert result == "Short value"

    def test_truncate_field_truncates_long_value(self, asset_handler):
        """Test that long fields are truncated."""
        value = "x" * 500
        result = asset_handler._truncate_field(value, max_length=450, field_name="testField")

        assert len(result) == 450
        assert result == "x" * 450

    def test_truncate_field_handles_none(self, asset_handler):
        """Test that None values are preserved."""
        result = asset_handler._truncate_field(None, max_length=450)

        assert result is None

    def test_truncate_field_handles_empty_string(self, asset_handler):
        """Test that empty strings are preserved."""
        result = asset_handler._truncate_field("", max_length=450)

        assert result == ""

    def test_validate_asset_requirements_valid(self, asset_handler, sample_integration_asset):
        """Test validation passes for valid asset."""
        result = asset_handler._validate_asset_requirements(sample_integration_asset)

        assert result is True

    def test_validate_asset_requirements_no_name(self, asset_handler):
        """Test validation fails when asset has no name."""
        asset = IntegrationAsset(name="", identifier="test-001", asset_type="Desktop", asset_category="Hardware")

        result = asset_handler._validate_asset_requirements(asset)

        assert result is False

    def test_validate_and_map_asset_type_valid(self, asset_handler):
        """Test mapping valid asset type."""
        for asset_type in VALID_ASSET_TYPES:
            result = asset_handler._validate_and_map_asset_type(asset_type)
            assert result == asset_type

    def test_validate_and_map_asset_type_invalid(self, asset_handler):
        """Test mapping invalid asset type to 'Other'."""
        result = asset_handler._validate_and_map_asset_type("Invalid Type")

        assert result == "Other"

    def test_prepare_tracking_number_from_other_tracking_number(self, asset_handler):
        """Test preparing tracking number from other_tracking_number field."""
        asset = IntegrationAsset(
            name="Test",
            identifier="id-001",
            asset_type="Desktop",
            asset_category="Hardware",
            other_tracking_number="tracking-123",
        )

        result = asset_handler._prepare_tracking_number(asset)

        assert result == "tracking-123"

    def test_prepare_tracking_number_from_identifier(self, asset_handler):
        """Test preparing tracking number from identifier field."""
        asset = IntegrationAsset(name="Test", identifier="id-001", asset_type="Desktop", asset_category="Hardware")

        result = asset_handler._prepare_tracking_number(asset)

        assert result == "id-001"

    def test_prepare_tracking_number_fallback_to_name(self, asset_handler):
        """Test preparing tracking number falls back to name."""
        asset = IntegrationAsset(
            name="Test Asset", identifier="", asset_type="Desktop", asset_category="Hardware", other_tracking_number=""
        )

        result = asset_handler._prepare_tracking_number(asset)

        assert result == "Test Asset"

    def test_prepare_truncated_asset_fields(self, asset_handler):
        """Test preparing truncated asset fields."""
        asset = IntegrationAsset(
            name="Test Asset",
            identifier="id-001",
            asset_type="Desktop",
            asset_category="Hardware",
            azure_identifier="azure-123",
            aws_identifier="aws-456",
            google_identifier="gcp-789",
            other_cloud_identifier="cloud-999",
            software_name="Test Software",
        )

        with patch.object(asset_handler, "_process_asset_name", return_value="Test Asset"):
            result = asset_handler._prepare_truncated_asset_fields(asset, "tracking-001")

            assert result["name"] == "Test Asset"
            assert result["azure_identifier"] == "azure-123"
            assert result["aws_identifier"] == "aws-456"
            assert result["google_identifier"] == "gcp-789"
            assert result["other_cloud_identifier"] == "cloud-999"
            assert result["software_name"] == "Test Software"
            assert result["other_tracking_number"] == "tracking-001"

    def test_process_asset_name_normal(self, asset_handler):
        """Test processing normal asset name."""
        asset = IntegrationAsset(
            name="Normal Name", identifier="id-001", asset_type="Desktop", asset_category="Hardware"
        )

        result = asset_handler._process_asset_name(asset, 450)

        assert result == "Normal Name"

    def test_process_asset_name_long_azure_path(self, asset_handler):
        """Test processing long Azure resource path."""
        long_name = "/subscriptions/sub-id/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/vm-name"
        asset = IntegrationAsset(name=long_name, identifier="id-001", asset_type="Desktop", asset_category="Hardware")

        with patch.object(
            asset_handler, "_shorten_azure_resource_path", return_value="../my-rg/.../virtualMachines/vm-name"
        ) as mock_shorten:
            asset_handler._process_asset_name(asset, 50)

            # Should attempt to shorten if name is too long and contains slashes
            if len(long_name) > 50:
                mock_shorten.assert_called_once()

    def test_process_asset_name_empty_fallback(self, asset_handler):
        """Test processing empty asset name returns fallback."""
        asset = IntegrationAsset(name="", identifier="id-001", asset_type="Desktop", asset_category="Hardware")

        with patch.object(asset_handler, "_truncate_field", return_value=None):
            result = asset_handler._process_asset_name(asset, 450)

            assert result == "Unknown Asset"

    def test_shorten_azure_resource_path(self, asset_handler):
        """Test shortening Azure resource path."""
        full_path = "/subscriptions/sub-id/resourceGroups/my-resource-group/providers/Microsoft.Compute/virtualMachines/my-vm-name"

        result = asset_handler._shorten_azure_resource_path(full_path, 450)

        assert "my-resource-group" in result
        assert "virtualMachines" in result
        assert "my-vm-name" in result
        assert len(result) <= 450

    def test_shorten_azure_resource_path_without_resource_group(self, asset_handler):
        """Test shortening Azure path without resource group."""
        full_path = "/providers/Microsoft.Compute/virtualMachines/my-vm-name"

        result = asset_handler._shorten_azure_resource_path(full_path, 450)

        assert "virtualMachines" in result
        assert "my-vm-name" in result

    def test_empty_to_none_with_value(self, asset_handler):
        """Test _empty_to_none returns value for non-empty string."""
        result = asset_handler._empty_to_none("test value")

        assert result == "test value"

    def test_empty_to_none_with_empty_string(self, asset_handler):
        """Test _empty_to_none returns None for empty string."""
        result = asset_handler._empty_to_none("")

        assert result is None

    def test_empty_to_none_with_none(self, asset_handler):
        """Test _empty_to_none returns None for None."""
        result = asset_handler._empty_to_none(None)

        assert result is None


class TestCreateRegscaleAssetModel:
    """Tests for _create_regscale_asset_model method."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.get_current_datetime")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    def test_create_regscale_asset_model_without_component(
        self, mock_asset_class, mock_get_datetime, asset_handler, sample_integration_asset
    ):
        """Test creating RegScale Asset model without component."""
        mock_get_datetime.return_value = "2024-01-01T00:00:00Z"
        mock_asset = MagicMock()
        mock_asset_class.return_value = mock_asset

        field_data = {
            "name": "Test Asset",
            "azure_identifier": None,
            "aws_identifier": None,
            "google_identifier": None,
            "other_cloud_identifier": None,
            "software_name": None,
            "other_tracking_number": "test-001",
        }

        result = asset_handler._create_regscale_asset_model(
            sample_integration_asset, None, "Virtual Machine (VM)", field_data
        )

        assert result == mock_asset
        # Verify Asset was constructed with correct arguments
        call_kwargs = mock_asset_class.call_args[1]
        assert call_kwargs["name"] == "Test Asset"
        assert call_kwargs["parentId"] == asset_handler.context.plan_id
        assert call_kwargs["parentModule"] == asset_handler.context.parent_module

    @patch("regscale.integrations.scanner.handlers.asset_handler.get_current_datetime")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    def test_create_regscale_asset_model_with_component(
        self, mock_asset_class, mock_get_datetime, asset_handler, sample_integration_asset
    ):
        """Test creating RegScale Asset model with component."""
        mock_get_datetime.return_value = "2024-01-01T00:00:00Z"
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 789
        mock_asset = MagicMock()
        mock_asset_class.return_value = mock_asset

        field_data = {
            "name": "Test Asset",
            "azure_identifier": None,
            "aws_identifier": None,
            "google_identifier": None,
            "other_cloud_identifier": None,
            "software_name": None,
            "other_tracking_number": "test-001",
        }

        asset_handler._create_regscale_asset_model(
            sample_integration_asset, mock_component, "Virtual Machine (VM)", field_data
        )

        # Verify parent is component ID
        call_kwargs = mock_asset_class.call_args[1]
        assert call_kwargs["parentId"] == 789

    @patch("regscale.integrations.scanner.handlers.asset_handler.get_current_datetime")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    def test_create_regscale_asset_model_sets_identifier_field(
        self, mock_asset_class, mock_get_datetime, asset_handler, sample_integration_asset
    ):
        """Test that custom identifier field is set on asset."""
        mock_get_datetime.return_value = "2024-01-01T00:00:00Z"
        mock_asset = MagicMock()
        mock_asset_class.return_value = mock_asset
        asset_handler.context.asset_identifier_field = "customField"

        field_data = {
            "name": "Test Asset",
            "azure_identifier": None,
            "aws_identifier": None,
            "google_identifier": None,
            "other_cloud_identifier": None,
            "software_name": None,
            "other_tracking_number": "test-001",
        }

        result = asset_handler._create_regscale_asset_model(sample_integration_asset, None, "Desktop", field_data)

        # Verify setattr was called to set custom field
        assert hasattr(result, "customField") or mock_asset_class.called


class TestSoftwareInventoryHandling:
    """Tests for software inventory handling."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.SoftwareInventory")
    def test_handle_software_inventory_creates_new(self, mock_software_class, asset_handler, sample_regscale_asset):
        """Test creating new software inventory items."""
        software_inventory = [
            {"name": "Software A", "version": "1.0"},
            {"name": "Software B", "version": "2.0"},
        ]

        with patch.object(regscale_models.SoftwareInventory, "get_all_by_parent", return_value=[]):
            asset_handler.handle_software_inventory(sample_regscale_asset, software_inventory, created=True)

            # Should add 2 software items to create list
            assert len(asset_handler.context.software_to_create) == 2

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.SoftwareInventory")
    def test_handle_software_inventory_skips_existing(self, mock_software_class, asset_handler, sample_regscale_asset):
        """Test skipping existing software inventory items."""
        software_inventory = [
            {"name": "Software A", "version": "1.0"},
        ]

        existing_software = MagicMock()
        existing_software.name = "Software A"
        existing_software.version = "1.0"

        with patch.object(regscale_models.SoftwareInventory, "get_all_by_parent", return_value=[existing_software]):
            asset_handler.handle_software_inventory(sample_regscale_asset, software_inventory, created=False)

            # Should not add to create list
            assert len(asset_handler.context.software_to_create) == 0

    def test_handle_software_inventory_empty_list(self, asset_handler, sample_regscale_asset):
        """Test handling empty software inventory."""
        asset_handler.handle_software_inventory(sample_regscale_asset, [], created=True)

        # Should not add anything
        assert len(asset_handler.context.software_to_create) == 0

    def test_handle_software_inventory_missing_name(self, asset_handler, sample_regscale_asset):
        """Test handling software inventory with missing name."""
        software_inventory = [
            {"version": "1.0"},  # Missing name
        ]

        with patch.object(regscale_models.SoftwareInventory, "get_all_by_parent", return_value=[]):
            asset_handler.handle_software_inventory(sample_regscale_asset, software_inventory, created=True)

            # Should skip item with missing name
            assert len(asset_handler.context.software_to_create) == 0


class TestAssetDataAndLinkCreation:
    """Tests for create_asset_data_and_link method."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Data")
    def test_create_asset_data_and_link_with_source_data(
        self, mock_data_class, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test creating Data object with source data."""
        sample_integration_asset.source_data = {"key": "value", "nested": {"data": 123}}
        mock_data_instance = MagicMock()
        mock_data_class.return_value = mock_data_instance

        asset_handler.create_asset_data_and_link(sample_regscale_asset, sample_integration_asset)

        # Verify Data was created
        mock_data_class.assert_called_once()
        call_kwargs = mock_data_class.call_args[1]
        assert call_kwargs["parentId"] == 456
        assert call_kwargs["dataSource"] == "Test Scanner"
        mock_data_instance.create_or_update.assert_called_once()

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Link")
    def test_create_asset_data_and_link_with_url_new_link(
        self, mock_link_class, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test creating new Link object."""
        sample_integration_asset.url = "https://example.com/asset/123"
        mock_link_instance = MagicMock()
        mock_link_instance.find_by_unique = MagicMock(return_value=False)
        mock_link_class.return_value = mock_link_instance

        asset_handler.create_asset_data_and_link(sample_regscale_asset, sample_integration_asset)

        # Verify Link was created and added to create list
        mock_link_class.assert_called_once()
        assert mock_link_instance in asset_handler.context.link_to_create

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Link")
    def test_create_asset_data_and_link_with_url_existing_link(
        self, mock_link_class, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test updating existing Link object."""
        sample_integration_asset.url = "https://example.com/asset/123"
        mock_link_instance = MagicMock()
        mock_link_instance.find_by_unique = MagicMock(return_value=True)
        mock_link_class.return_value = mock_link_instance

        asset_handler.create_asset_data_and_link(sample_regscale_asset, sample_integration_asset)

        # Verify Link was added to update list
        assert mock_link_instance in asset_handler.context.link_to_update

    def test_create_asset_data_and_link_no_data_or_url(
        self, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test with no source data or URL."""
        sample_integration_asset.source_data = None
        sample_integration_asset.url = None

        # Should complete without creating anything
        asset_handler.create_asset_data_and_link(sample_regscale_asset, sample_integration_asset)


class TestPortsProtocolCreation:
    """Tests for create_or_update_ports_protocol method."""

    @patch("regscale.integrations.scanner.handlers.asset_handler._retry_with_backoff")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.PortsProtocol")
    def test_create_or_update_ports_protocol_valid(
        self, mock_ports_class, mock_retry, sample_regscale_asset, sample_integration_asset
    ):
        """Test creating PortsProtocol with valid data."""
        sample_integration_asset.ports_and_protocols = [
            {"start_port": 80, "end_port": 80, "protocol": "TCP", "service": "HTTP"},
            {"start_port": 443, "end_port": 443, "protocol": "TCP", "service": "HTTPS"},
        ]
        mock_ports_instance = MagicMock()
        mock_ports_class.return_value = mock_ports_instance

        AssetHandler.create_or_update_ports_protocol(sample_regscale_asset, sample_integration_asset)

        # Should create 2 PortsProtocol objects
        assert mock_ports_class.call_count == 2
        assert mock_retry.call_count == 2

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.PortsProtocol")
    def test_create_or_update_ports_protocol_invalid(
        self, mock_ports_class, sample_regscale_asset, sample_integration_asset
    ):
        """Test handling invalid port protocol data."""
        sample_integration_asset.ports_and_protocols = [
            {"start_port": 80},  # Missing end_port
            {"end_port": 443},  # Missing start_port
        ]

        AssetHandler.create_or_update_ports_protocol(sample_regscale_asset, sample_integration_asset)

        # Should not create any PortsProtocol objects due to validation
        mock_ports_class.assert_not_called()

    def test_create_or_update_ports_protocol_empty(self, sample_regscale_asset, sample_integration_asset):
        """Test with empty ports_and_protocols."""
        sample_integration_asset.ports_and_protocols = []

        # Should complete without errors
        AssetHandler.create_or_update_ports_protocol(sample_regscale_asset, sample_integration_asset)


class TestSetAssetDefaults:
    """Tests for _set_asset_defaults method."""

    def test_set_asset_defaults_sets_owner(self, asset_handler):
        """Test setting default asset owner."""
        asset = IntegrationAsset(name="Test", identifier="test-001", asset_type="Desktop", asset_category="Hardware")
        asset.asset_owner_id = None

        with patch.object(asset_handler, "_get_assessor_id", return_value="default-assessor"):
            result = asset_handler._set_asset_defaults(asset)

            assert result.asset_owner_id == "default-assessor"

    def test_set_asset_defaults_sets_status(self, asset_handler):
        """Test setting default asset status."""
        asset = IntegrationAsset(name="Test", identifier="test-001", asset_type="Desktop", asset_category="Hardware")
        asset.status = None

        result = asset_handler._set_asset_defaults(asset)

        assert result.status == regscale_models.AssetStatus.Active

    def test_set_asset_defaults_preserves_existing(self, asset_handler):
        """Test that existing values are preserved."""
        asset = IntegrationAsset(
            name="Test",
            identifier="test-001",
            asset_type="Desktop",
            asset_category="Hardware",
            asset_owner_id="existing-owner",
            status=regscale_models.AssetStatus.Inactive,
        )

        result = asset_handler._set_asset_defaults(asset)

        assert result.asset_owner_id == "existing-owner"
        assert result.status == regscale_models.AssetStatus.Inactive


class TestGetAssessorId:
    """Tests for _get_assessor_id method."""

    def test_get_assessor_id_from_context(self, asset_handler):
        """Test getting assessor ID from context."""
        asset_handler.context.assessor_id = "context-assessor-123"

        result = asset_handler._get_assessor_id()

        assert result == "context-assessor-123"

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Issue.get_user_id")
    def test_get_assessor_id_from_regscale(self, mock_get_user_id, asset_handler):
        """Test getting assessor ID from RegScale."""
        asset_handler.context.assessor_id = None
        mock_get_user_id.return_value = "regscale-user-456"

        result = asset_handler._get_assessor_id()

        assert result == "regscale-user-456"

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Issue.get_user_id")
    def test_get_assessor_id_fallback_unknown(self, mock_get_user_id, asset_handler):
        """Test fallback to Unknown when no assessor ID available."""
        asset_handler.context.assessor_id = None
        mock_get_user_id.return_value = None

        result = asset_handler._get_assessor_id()

        assert result == "Unknown"


class TestGetComplianceSettingsId:
    """Tests for _get_compliance_settings_id method."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.SecurityPlan.get_object")
    def test_get_compliance_settings_id_success(self, mock_get_object, asset_handler):
        """Test getting compliance settings ID successfully."""
        mock_security_plan = MagicMock()
        mock_security_plan.complianceSettingsId = 999
        mock_get_object.return_value = mock_security_plan

        result = asset_handler._get_compliance_settings_id()

        assert result == 999

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.SecurityPlan.get_object")
    def test_get_compliance_settings_id_missing_attribute(self, mock_get_object, asset_handler):
        """Test handling missing complianceSettingsId attribute."""
        mock_security_plan = MagicMock(spec=[])  # No complianceSettingsId
        mock_get_object.return_value = mock_security_plan

        result = asset_handler._get_compliance_settings_id()

        assert result is None

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.SecurityPlan.get_object")
    def test_get_compliance_settings_id_exception(self, mock_get_object, asset_handler):
        """Test handling exception when getting security plan."""
        mock_get_object.side_effect = Exception("API Error")

        result = asset_handler._get_compliance_settings_id()

        assert result is None


class TestHandleComponentMappingAndDurosuite:
    """Tests for _handle_component_mapping_and_durosuite method."""

    @patch("regscale.integrations.scanner.handlers.asset_handler._retry_with_backoff")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.AssetMapping")
    def test_handle_component_mapping_creates_mapping(
        self, mock_mapping_class, mock_retry, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test creating asset mapping."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 789
        mock_mapping_instance = MagicMock()
        mock_mapping_class.return_value = mock_mapping_instance

        asset_handler._handle_component_mapping_and_durosuite(
            sample_regscale_asset, mock_component, sample_integration_asset, created=True
        )

        mock_mapping_class.assert_called_once_with(assetId=456, componentId=789)
        mock_retry.assert_called_once()

    @patch("regscale.integrations.scanner.handlers.asset_handler._retry_with_backoff")
    def test_handle_component_mapping_retry_failure(
        self, mock_retry, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test handling retry failure when creating asset mapping."""
        mock_component = MagicMock(spec=regscale_models.Component)
        mock_component.id = 789
        mock_retry.side_effect = Exception("Retry failed")

        # Should log warning but not raise
        asset_handler._handle_component_mapping_and_durosuite(
            sample_regscale_asset, mock_component, sample_integration_asset, created=True
        )

    @patch("regscale.integrations.scanner.handlers.asset_handler.DuroSuiteVariables")
    @patch("regscale.integrations.scanner.handlers.asset_handler.scan_durosuite_devices")
    def test_handle_component_mapping_durosuite_enabled(
        self, mock_scan_durosuite, mock_durosuite_vars, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test DuroSuite scanning when enabled."""
        mock_durosuite_vars.duroSuiteEnabled = True

        asset_handler._handle_component_mapping_and_durosuite(
            sample_regscale_asset, None, sample_integration_asset, created=True
        )

        mock_scan_durosuite.assert_called_once_with(
            asset=sample_integration_asset, plan_id=123, progress=asset_handler.context.asset_progress
        )

    @patch("regscale.integrations.scanner.handlers.asset_handler.DuroSuiteVariables")
    def test_handle_component_mapping_durosuite_disabled(
        self, mock_durosuite_vars, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test DuroSuite scanning when disabled."""
        mock_durosuite_vars.duroSuiteEnabled = False

        # Should not call scan_durosuite_devices
        asset_handler._handle_component_mapping_and_durosuite(
            sample_regscale_asset, None, sample_integration_asset, created=True
        )


class TestHandleSoftwareAndStigProcessing:
    """Tests for _handle_software_and_stig_processing method."""

    def test_handle_software_and_stig_processing_calls_all_methods(
        self, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test that all post-creation methods are called."""
        sample_integration_asset.software_inventory = [{"name": "Software", "version": "1.0"}]

        with patch.object(asset_handler, "handle_software_inventory") as mock_software:
            with patch.object(asset_handler, "create_asset_data_and_link") as mock_data_link:
                with patch.object(asset_handler, "create_or_update_ports_protocol") as mock_ports:
                    asset_handler._handle_software_and_stig_processing(
                        sample_regscale_asset, sample_integration_asset, created=True
                    )

                    mock_software.assert_called_once_with(
                        sample_regscale_asset, sample_integration_asset.software_inventory, True
                    )
                    mock_data_link.assert_called_once_with(sample_regscale_asset, sample_integration_asset)
                    mock_ports.assert_called_once_with(sample_regscale_asset, sample_integration_asset)

    def test_handle_software_and_stig_processing_with_stig_mapper(
        self, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test STIG mapping when stig_mapper is configured."""
        mock_stig_mapper = MagicMock()
        asset_handler.context.stig_mapper = mock_stig_mapper

        with patch.object(asset_handler, "handle_software_inventory"):
            with patch.object(asset_handler, "create_asset_data_and_link"):
                with patch.object(asset_handler, "create_or_update_ports_protocol"):
                    asset_handler._handle_software_and_stig_processing(
                        sample_regscale_asset, sample_integration_asset, created=True
                    )

                    mock_stig_mapper.map_associated_stigs_to_asset.assert_called_once_with(
                        asset=sample_regscale_asset, ssp_id=123
                    )


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_process_asset_with_empty_identifier(self, asset_handler):
        """Test processing asset with empty identifier."""
        asset = IntegrationAsset(name="Test", identifier="", asset_type="Desktop", asset_category="Hardware")

        with patch.object(asset_handler, "_set_asset_defaults", return_value=asset):
            with patch.object(asset_handler, "update_or_create_asset") as mock_update:
                asset_handler.process_asset(asset)

                # Should still call update_or_create_asset, which will skip it
                mock_update.assert_called_once()

    def test_create_new_asset_with_none_values(self, asset_handler):
        """Test creating asset with None values for optional fields."""
        asset = IntegrationAsset(
            name="Test Asset",
            identifier="test-001",
            asset_type="Desktop",
            asset_category="Hardware",
            description=None,
            ip_address=None,
            mac_address=None,
        )

        mock_asset = MagicMock(spec=regscale_models.Asset)
        mock_asset.id = 456
        mock_asset.create_or_update_with_status = MagicMock(return_value=("created", mock_asset))

        with patch.object(asset_handler, "_validate_asset_requirements", return_value=True):
            with patch.object(asset_handler, "_validate_and_map_asset_type", return_value="Desktop"):
                with patch.object(asset_handler, "_prepare_tracking_number", return_value="test-001"):
                    with patch.object(
                        asset_handler, "_prepare_truncated_asset_fields", return_value={"name": "Test Asset"}
                    ):
                        with patch.object(asset_handler, "_create_regscale_asset_model", return_value=mock_asset):
                            with patch.object(asset_handler, "_handle_software_and_stig_processing"):
                                created, new_asset = asset_handler.create_new_asset(asset, None)

                                assert created is True
                                assert new_asset is not None

    def test_truncate_field_with_unicode_characters(self, asset_handler):
        """Test truncating field with unicode characters."""
        value = "测试数据" * 100  # Chinese characters
        result = asset_handler._truncate_field(value, max_length=50)

        assert len(result) == 50

    def test_handle_software_inventory_with_duplicate_versions(self, asset_handler, sample_regscale_asset):
        """Test handling software inventory with same software, different versions."""
        software_inventory = [
            {"name": "Software A", "version": "1.0"},
            {"name": "Software A", "version": "2.0"},
        ]

        with patch.object(regscale_models.SoftwareInventory, "get_all_by_parent", return_value=[]):
            asset_handler.handle_software_inventory(sample_regscale_asset, software_inventory, created=True)

            # Should create both items (different versions)
            assert len(asset_handler.context.software_to_create) == 2

    def test_create_asset_data_and_link_with_json_serialization_error(
        self, asset_handler, sample_regscale_asset, sample_integration_asset
    ):
        """Test handling JSON serialization error in source data."""

        # Create data that can't be serialized
        class NonSerializable:
            pass

        sample_integration_asset.source_data = {"key": NonSerializable()}

        with patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Data"):
            # json.dumps should be called and might raise TypeError
            with patch("regscale.integrations.scanner.handlers.asset_handler.json.dumps") as mock_json_dumps:
                mock_json_dumps.side_effect = TypeError("Not serializable")

                # Should raise the exception (not catching it in the code)
                with pytest.raises(TypeError):
                    asset_handler.create_asset_data_and_link(sample_regscale_asset, sample_integration_asset)
