#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for Wiz finding processors module."""

import logging
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from regscale.integrations.commercial.wizv2.processors.finding import (
    WizComplianceItem,
    FindingConsolidator,
    FindingToIssueProcessor,
)
from regscale.integrations.scanner_integration import IntegrationFinding
from regscale.models import regscale_models

logger = logging.getLogger("regscale")

PATH = "regscale.integrations.commercial.wizv2.processors.finding"


# =============================
# WizComplianceItem Tests
# =============================


class TestWizComplianceItem:
    """Test WizComplianceItem wrapper class."""

    def test_initialization(self):
        """Test creating WizComplianceItem wrapper."""
        mock_item = MagicMock()
        mock_item.resource_id = "res-123"
        mock_item.control_id = "AC-2(1)"
        mock_item.is_fail = True

        wrapper = WizComplianceItem(mock_item)

        assert wrapper._item == mock_item

    def test_resource_id_property(self):
        """Test resource_id property returns correct value."""
        mock_item = MagicMock()
        mock_item.resource_id = "resource-456"

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.resource_id == "resource-456"

    def test_resource_id_property_missing_attribute(self):
        """Test resource_id property when attribute is missing."""
        mock_item = MagicMock(spec=[])

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.resource_id == ""

    def test_control_id_property(self):
        """Test control_id property returns correct value."""
        mock_item = MagicMock()
        mock_item.control_id = "SC-7"

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.control_id == "SC-7"

    def test_control_id_property_missing_attribute(self):
        """Test control_id property when attribute is missing."""
        mock_item = MagicMock(spec=[])

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.control_id == ""

    def test_is_fail_property(self):
        """Test is_fail property returns correct value."""
        mock_item = MagicMock()
        mock_item.is_fail = True

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.is_fail is True

    def test_is_fail_property_missing_attribute(self):
        """Test is_fail property when attribute is missing."""
        mock_item = MagicMock(spec=[])

        wrapper = WizComplianceItem(mock_item)

        assert wrapper.is_fail is False

    def test_get_all_control_ids_with_method(self):
        """Test get_all_control_ids when wrapped item has the method."""
        mock_item = MagicMock()
        mock_item.control_id = "AC-2"
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2", "AC-2(1)", "AC-2(2)"])

        wrapper = WizComplianceItem(mock_item)
        result = wrapper.get_all_control_ids()

        assert result == ["AC-2", "AC-2(1)", "AC-2(2)"]
        mock_item._get_all_control_ids_for_compliance_item.assert_called_once_with(mock_item)

    def test_get_all_control_ids_fallback_single_control(self):
        """Test get_all_control_ids falls back to control_id."""
        mock_item = MagicMock()
        mock_item.control_id = "SC-7"
        del mock_item._get_all_control_ids_for_compliance_item

        wrapper = WizComplianceItem(mock_item)
        result = wrapper.get_all_control_ids()

        assert result == ["SC-7"]

    def test_get_all_control_ids_fallback_no_control(self):
        """Test get_all_control_ids when no control_id exists."""
        mock_item = MagicMock(spec=[])

        wrapper = WizComplianceItem(mock_item)
        result = wrapper.get_all_control_ids()

        assert result == []


# =============================
# FindingConsolidator Tests
# =============================


class TestFindingConsolidator:
    """Test FindingConsolidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_integration = MagicMock()
        self.consolidator = FindingConsolidator(self.mock_integration)

    def test_initialization(self):
        """Test FindingConsolidator initialization."""
        assert self.consolidator.integration == self.mock_integration
        assert self.consolidator.asset_consolidator is not None

    def test_create_consolidated_findings_empty_list(self):
        """Test creating findings with empty list."""
        result = list(self.consolidator.create_consolidated_findings([]))

        assert result == []

    def test_create_consolidated_findings_no_control_groups(self):
        """Test creating findings when no control groups are created."""
        mock_item = MagicMock()
        mock_item.resource_id = ""
        mock_item.control_id = ""
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=[])

        result = list(self.consolidator.create_consolidated_findings([mock_item]))

        assert result == []

    @patch(f"{PATH}.FindingConsolidator._create_consolidated_finding_for_control")
    def test_create_consolidated_findings_success(self, mock_create_finding):
        """Test creating consolidated findings successfully."""
        # Create mock compliance items
        item1 = MagicMock()
        item1.resource_id = "res-1"
        item1.control_id = "AC-2"
        item1._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        item2 = MagicMock()
        item2.resource_id = "res-2"
        item2.control_id = "AC-2"
        item2._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        # Mock finding creation
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_create_finding.return_value = mock_finding

        result = list(self.consolidator.create_consolidated_findings([item1, item2]))

        assert len(result) == 1
        assert result[0] == mock_finding
        mock_create_finding.assert_called_once()

    @patch(f"{PATH}.FindingConsolidator._create_consolidated_finding_for_control")
    def test_create_consolidated_findings_multiple_controls(self, mock_create_finding):
        """Test creating findings for multiple controls."""
        item1 = MagicMock()
        item1.resource_id = "res-1"
        item1._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2", "SC-7"])

        mock_finding1 = MagicMock(spec=IntegrationFinding)
        mock_finding2 = MagicMock(spec=IntegrationFinding)
        mock_create_finding.side_effect = [mock_finding1, mock_finding2]

        result = list(self.consolidator.create_consolidated_findings([item1]))

        assert len(result) == 2
        assert mock_create_finding.call_count == 2

    def test_group_by_control_empty_list(self):
        """Test grouping empty compliance items."""
        result = self.consolidator._group_by_control([])

        assert result == {}

    def test_group_by_control_single_control_single_resource(self):
        """Test grouping single control with single resource."""
        mock_item = MagicMock()
        mock_item.resource_id = "res-123"
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        result = self.consolidator._group_by_control([mock_item])

        assert "AC-2" in result
        assert "res-123" in result["AC-2"]
        assert result["AC-2"]["res-123"] == mock_item

    def test_group_by_control_multiple_resources_same_control(self):
        """Test grouping multiple resources for same control."""
        item1 = MagicMock()
        item1.resource_id = "res-1"
        item1._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        item2 = MagicMock()
        item2.resource_id = "res-2"
        item2._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        result = self.consolidator._group_by_control([item1, item2])

        assert len(result["AC-2"]) == 2
        assert "res-1" in result["AC-2"]
        assert "res-2" in result["AC-2"]

    def test_group_by_control_case_normalization(self):
        """Test that control IDs are normalized to uppercase."""
        item1 = MagicMock()
        item1.resource_id = "res-1"
        item1._get_all_control_ids_for_compliance_item = MagicMock(return_value=["ac-2"])

        item2 = MagicMock()
        item2.resource_id = "res-2"
        item2._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        result = self.consolidator._group_by_control([item1, item2])

        assert "AC-2" in result
        assert len(result["AC-2"]) == 2

    def test_group_by_control_resource_id_normalization(self):
        """Test that resource IDs are normalized to lowercase."""
        item1 = MagicMock()
        item1.resource_id = "RES-1"
        item1._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        item2 = MagicMock()
        item2.resource_id = "res-1"
        item2._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        result = self.consolidator._group_by_control([item1, item2])

        # Should only have one resource (first occurrence wins)
        assert len(result["AC-2"]) == 1
        assert "res-1" in result["AC-2"]

    def test_group_by_control_multiple_controls_per_item(self):
        """Test grouping item that maps to multiple controls."""
        mock_item = MagicMock()
        mock_item.resource_id = "res-1"
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2", "SC-7", "AU-2"])

        result = self.consolidator._group_by_control([mock_item])

        assert len(result) == 3
        assert "AC-2" in result
        assert "SC-7" in result
        assert "AU-2" in result
        assert result["AC-2"]["res-1"] == mock_item
        assert result["SC-7"]["res-1"] == mock_item
        assert result["AU-2"]["res-1"] == mock_item

    def test_group_by_control_skip_empty_resource_id(self):
        """Test that items without resource_id are skipped."""
        mock_item = MagicMock()
        mock_item.resource_id = ""
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=["AC-2"])

        result = self.consolidator._group_by_control([mock_item])

        assert result == {}

    def test_group_by_control_skip_empty_control_ids(self):
        """Test that items without control IDs are skipped."""
        mock_item = MagicMock()
        mock_item.resource_id = "res-1"
        mock_item._get_all_control_ids_for_compliance_item = MagicMock(return_value=[])

        result = self.consolidator._group_by_control([mock_item])

        assert result == {}

    @patch(f"{PATH}.FindingConsolidator._update_finding_with_assets")
    @patch(f"{PATH}.FindingConsolidator._create_base_finding")
    @patch(f"{PATH}.FindingConsolidator._build_asset_mappings")
    def test_create_consolidated_finding_for_control_success(
        self, mock_build_mappings, mock_create_base, mock_update_finding
    ):
        """Test creating consolidated finding successfully."""
        resources = {"res-1": MagicMock(), "res-2": MagicMock()}
        asset_mappings = {"res-1": {"name": "Asset 1", "wiz_id": "res-1"}}

        mock_build_mappings.return_value = asset_mappings
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_create_base.return_value = mock_finding

        result = self.consolidator._create_consolidated_finding_for_control("AC-2", resources)

        assert result == mock_finding
        mock_build_mappings.assert_called_once()
        mock_create_base.assert_called_once()
        mock_update_finding.assert_called_once_with(mock_finding, asset_mappings)

    @patch(f"{PATH}.FindingConsolidator._build_asset_mappings")
    def test_create_consolidated_finding_for_control_no_assets(self, mock_build_mappings):
        """Test creating finding when no assets exist in RegScale."""
        resources = {"res-1": MagicMock()}
        mock_build_mappings.return_value = {}

        result = self.consolidator._create_consolidated_finding_for_control("AC-2", resources)

        assert result is None

    @patch(f"{PATH}.FindingConsolidator._create_base_finding")
    @patch(f"{PATH}.FindingConsolidator._build_asset_mappings")
    def test_create_consolidated_finding_for_control_base_finding_fails(self, mock_build_mappings, mock_create_base):
        """Test handling when base finding creation fails."""
        resources = {"res-1": MagicMock()}
        asset_mappings = {"res-1": {"name": "Asset 1", "wiz_id": "res-1"}}

        mock_build_mappings.return_value = asset_mappings
        mock_create_base.return_value = None

        result = self.consolidator._create_consolidated_finding_for_control("AC-2", resources)

        assert result is None

    def test_build_asset_mappings_all_assets_exist(self):
        """Test building asset mappings when all assets exist."""
        self.mock_integration._asset_exists_in_regscale.return_value = True

        mock_asset1 = MagicMock()
        mock_asset1.name = "Asset 1"
        mock_asset2 = MagicMock()
        mock_asset2.name = "Asset 2"

        self.mock_integration.get_asset_by_identifier.side_effect = [mock_asset1, mock_asset2]

        result = self.consolidator._build_asset_mappings(["res-1", "res-2"])

        assert len(result) == 2
        assert result["res-1"]["name"] == "Asset 1"
        assert result["res-1"]["wiz_id"] == "res-1"
        assert result["res-2"]["name"] == "Asset 2"
        assert result["res-2"]["wiz_id"] == "res-2"

    def test_build_asset_mappings_some_assets_missing(self):
        """Test building asset mappings when some assets don't exist."""
        self.mock_integration._asset_exists_in_regscale.side_effect = [True, False, True]

        mock_asset1 = MagicMock()
        mock_asset1.name = "Asset 1"
        mock_asset3 = MagicMock()
        mock_asset3.name = "Asset 3"

        self.mock_integration.get_asset_by_identifier.side_effect = [mock_asset1, mock_asset3]

        result = self.consolidator._build_asset_mappings(["res-1", "res-2", "res-3"])

        assert len(result) == 2
        assert "res-1" in result
        assert "res-2" not in result
        assert "res-3" in result

    def test_build_asset_mappings_asset_has_no_name(self):
        """Test building asset mappings when asset has no name."""
        self.mock_integration._asset_exists_in_regscale.return_value = True

        mock_asset = MagicMock(spec=[])
        self.mock_integration.get_asset_by_identifier.return_value = mock_asset

        result = self.consolidator._build_asset_mappings(["res-1"])

        # Should fall back to resource ID
        assert result["res-1"]["name"] == "res-1"
        assert result["res-1"]["wiz_id"] == "res-1"

    def test_build_asset_mappings_get_asset_returns_none(self):
        """Test building asset mappings when get_asset returns None."""
        self.mock_integration._asset_exists_in_regscale.return_value = True
        self.mock_integration.get_asset_by_identifier.return_value = None

        result = self.consolidator._build_asset_mappings(["res-1"])

        # Should fall back to resource ID
        assert result["res-1"]["name"] == "res-1"
        assert result["res-1"]["wiz_id"] == "res-1"

    def test_create_base_finding_with_specific_control_method(self):
        """Test creating base finding using specific control method."""
        mock_item = MagicMock()
        mock_finding = MagicMock(spec=IntegrationFinding)

        self.mock_integration._create_finding_for_specific_control = MagicMock(return_value=mock_finding)

        result = self.consolidator._create_base_finding(mock_item, "AC-2")

        assert result == mock_finding
        self.mock_integration._create_finding_for_specific_control.assert_called_once_with(mock_item, "AC-2")

    def test_create_base_finding_fallback_to_generic_method(self):
        """Test creating base finding using generic method."""
        mock_item = MagicMock()
        mock_finding = MagicMock(spec=IntegrationFinding)

        del self.mock_integration._create_finding_for_specific_control
        self.mock_integration.create_finding_from_compliance_item = MagicMock(return_value=mock_finding)

        result = self.consolidator._create_base_finding(mock_item, "AC-2")

        assert result == mock_finding
        self.mock_integration.create_finding_from_compliance_item.assert_called_once_with(mock_item)

    def test_create_base_finding_exception_handling(self):
        """Test exception handling during base finding creation."""
        mock_item = MagicMock()

        self.mock_integration._create_finding_for_specific_control = MagicMock(side_effect=Exception("Creation failed"))

        result = self.consolidator._create_base_finding(mock_item, "AC-2")

        assert result is None

    def test_update_finding_with_assets(self):
        """Test updating finding with consolidated asset information."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.description = "Control failure"

        asset_mappings = {"res-1": {"name": "Asset 1"}, "res-2": {"name": "Asset 2"}}

        self.consolidator._update_finding_with_assets(mock_finding, asset_mappings)

        # Verify asset_identifier was set (mocked consolidator would have been called)
        assert mock_finding.asset_identifier is not None
        # Description should be updated with multiple assets
        assert "2 assets" in mock_finding.description


# =============================
# FindingToIssueProcessor Tests
# =============================


class TestFindingToIssueProcessor:
    """Test FindingToIssueProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_integration = MagicMock()
        self.processor = FindingToIssueProcessor(self.mock_integration)

    def test_initialization(self):
        """Test FindingToIssueProcessor initialization."""
        assert self.processor.integration == self.mock_integration

    def test_process_findings_to_issues_empty_list(self):
        """Test processing empty findings list."""
        created, skipped = self.processor.process_findings_to_issues([])

        assert created == 0
        assert skipped == 0

    @patch(f"{PATH}.FindingToIssueProcessor._process_single_finding")
    def test_process_findings_to_issues_all_successful(self, mock_process_single):
        """Test processing findings where all succeed."""
        mock_process_single.return_value = True

        findings = [MagicMock(spec=IntegrationFinding) for _ in range(3)]
        created, skipped = self.processor.process_findings_to_issues(findings)  # type: ignore[arg-type]

        assert created == 3
        assert skipped == 0
        assert mock_process_single.call_count == 3

    @patch(f"{PATH}.FindingToIssueProcessor._process_single_finding")
    def test_process_findings_to_issues_some_skipped(self, mock_process_single):
        """Test processing findings where some are skipped."""
        mock_process_single.side_effect = [True, False, True, False]

        findings = [MagicMock(spec=IntegrationFinding) for _ in range(4)]
        created, skipped = self.processor.process_findings_to_issues(findings)  # type: ignore[arg-type]

        assert created == 2
        assert skipped == 2

    @patch(f"{PATH}.FindingToIssueProcessor._process_single_finding")
    def test_process_findings_to_issues_exception_handling(self, mock_process_single):
        """Test exception handling during finding processing."""
        mock_process_single.side_effect = [True, Exception("Processing error"), True]

        findings = [MagicMock(spec=IntegrationFinding) for _ in range(3)]
        created, skipped = self.processor.process_findings_to_issues(findings)  # type: ignore[arg-type]

        assert created == 2
        assert skipped == 1

    @patch(f"{PATH}.FindingToIssueProcessor._verify_assets_exist")
    def test_process_single_finding_assets_not_found(self, mock_verify):
        """Test processing single finding when assets don't exist."""
        mock_verify.return_value = False
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.external_id = "finding-123"

        result = self.processor._process_single_finding(mock_finding)

        assert result is False
        mock_verify.assert_called_once_with(mock_finding)

    @patch(f"{PATH}.FindingToIssueProcessor._verify_assets_exist")
    def test_process_single_finding_success(self, mock_verify):
        """Test successfully processing single finding."""
        mock_verify.return_value = True
        mock_finding = MagicMock(spec=IntegrationFinding)

        self.mock_integration.get_issue_title.return_value = "Issue Title"
        mock_issue = MagicMock(spec=regscale_models.Issue)
        self.mock_integration.create_or_update_issue_from_finding.return_value = mock_issue

        result = self.processor._process_single_finding(mock_finding)

        assert result is True
        self.mock_integration.get_issue_title.assert_called_once_with(mock_finding)
        self.mock_integration.create_or_update_issue_from_finding.assert_called_once()

    @patch(f"{PATH}.FindingToIssueProcessor._verify_assets_exist")
    def test_process_single_finding_issue_creation_fails(self, mock_verify):
        """Test processing when issue creation returns None."""
        mock_verify.return_value = True
        mock_finding = MagicMock(spec=IntegrationFinding)

        self.mock_integration.get_issue_title.return_value = "Issue Title"
        self.mock_integration.create_or_update_issue_from_finding.return_value = None

        result = self.processor._process_single_finding(mock_finding)

        assert result is False

    @patch(f"{PATH}.FindingToIssueProcessor._verify_assets_exist")
    def test_process_single_finding_exception_during_creation(self, mock_verify):
        """Test exception handling during issue creation."""
        mock_verify.return_value = True
        mock_finding = MagicMock(spec=IntegrationFinding)

        self.mock_integration.get_issue_title.side_effect = Exception("Title generation failed")

        result = self.processor._process_single_finding(mock_finding)

        assert result is False

    def test_verify_assets_exist_no_asset_identifier(self):
        """Test verification when finding has no asset_identifier."""
        mock_finding = MagicMock(spec=[])

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is False

    def test_verify_assets_exist_empty_asset_identifier(self):
        """Test verification when asset_identifier is empty."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = ""

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is False

    def test_verify_assets_exist_single_asset_exists(self):
        """Test verification for single existing asset."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Asset 1 (res-123)"

        self.mock_integration._asset_exists_in_regscale.return_value = True

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is True
        self.mock_integration._asset_exists_in_regscale.assert_called_once_with("res-123")

    def test_verify_assets_exist_single_asset_not_exists(self):
        """Test verification when single asset doesn't exist."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Asset 1 (res-123)"

        self.mock_integration._asset_exists_in_regscale.return_value = False

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is False

    def test_verify_assets_exist_multiple_assets_all_exist(self):
        """Test verification for multiple existing assets."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Asset 1 (res-1)\nAsset 2 (res-2)\nAsset 3 (res-3)"

        self.mock_integration._asset_exists_in_regscale.return_value = True

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is True
        assert self.mock_integration._asset_exists_in_regscale.call_count == 3

    def test_verify_assets_exist_multiple_assets_one_missing(self):
        """Test verification when one asset in multiple is missing."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Asset 1 (res-1)\nAsset 2 (res-2)"

        self.mock_integration._asset_exists_in_regscale.side_effect = [True, False]

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is False

    def test_verify_assets_exist_skip_empty_lines(self):
        """Test verification skips empty lines in asset_identifier."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Asset 1 (res-1)\n\n\nAsset 2 (res-2)"

        self.mock_integration._asset_exists_in_regscale.return_value = True

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is True
        # Should only check 2 assets, not 4
        assert self.mock_integration._asset_exists_in_regscale.call_count == 2

    def test_verify_assets_exist_identifier_without_parentheses(self):
        """Test verification with identifier that has no parentheses."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "res-simple-id"

        self.mock_integration._asset_exists_in_regscale.return_value = True

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is True
        self.mock_integration._asset_exists_in_regscale.assert_called_once_with("res-simple-id")

    def test_verify_assets_exist_identifier_extraction(self):
        """Test proper extraction of resource ID from formatted identifier."""
        mock_finding = MagicMock(spec=IntegrationFinding)
        mock_finding.asset_identifier = "Complex Asset Name (res-complex-123)"

        self.mock_integration._asset_exists_in_regscale.return_value = True

        result = self.processor._verify_assets_exist(mock_finding)

        assert result is True
        self.mock_integration._asset_exists_in_regscale.assert_called_once_with("res-complex-123")


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
