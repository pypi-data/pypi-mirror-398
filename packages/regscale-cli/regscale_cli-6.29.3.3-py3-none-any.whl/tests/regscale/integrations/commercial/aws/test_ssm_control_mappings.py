#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Systems Manager Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.ssm_control_mappings import (
    SSM_CONTROL_MAPPINGS,
    SSMControlMapper,
)


class TestSSMControlMappings:
    """Test SSM control mappings constants."""

    def test_ssm_control_mappings_exist(self):
        """Test that SSM control mappings dictionary exists and has content."""
        assert len(SSM_CONTROL_MAPPINGS) > 0
        assert "CM-2" in SSM_CONTROL_MAPPINGS
        assert "CM-6" in SSM_CONTROL_MAPPINGS
        assert "SI-2" in SSM_CONTROL_MAPPINGS
        assert "CM-3" in SSM_CONTROL_MAPPINGS
        assert "CM-8" in SSM_CONTROL_MAPPINGS

    def test_cm2_mapping_structure(self):
        """Test CM-2 mapping structure."""
        cm2 = SSM_CONTROL_MAPPINGS["CM-2"]
        assert "name" in cm2
        assert "description" in cm2
        assert "checks" in cm2
        assert "managed_instances" in cm2["checks"]
        assert "inventory_collection" in cm2["checks"]
        assert "state_manager" in cm2["checks"]

    def test_cm6_mapping_structure(self):
        """Test CM-6 mapping structure."""
        cm6 = SSM_CONTROL_MAPPINGS["CM-6"]
        assert "name" in cm6
        assert "description" in cm6
        assert "checks" in cm6
        assert "ssm_documents" in cm6["checks"]
        assert "parameters" in cm6["checks"]
        assert "associations" in cm6["checks"]

    def test_si2_mapping_structure(self):
        """Test SI-2 mapping structure."""
        si2 = SSM_CONTROL_MAPPINGS["SI-2"]
        assert "name" in si2
        assert "description" in si2
        assert "checks" in si2
        assert "patch_baselines" in si2["checks"]
        assert "patch_compliance" in si2["checks"]
        assert "maintenance_windows" in si2["checks"]

    def test_cm3_mapping_structure(self):
        """Test CM-3 mapping structure."""
        cm3 = SSM_CONTROL_MAPPINGS["CM-3"]
        assert "name" in cm3
        assert "description" in cm3
        assert "checks" in cm3
        assert "automation_documents" in cm3["checks"]

    def test_cm8_mapping_structure(self):
        """Test CM-8 mapping structure."""
        cm8 = SSM_CONTROL_MAPPINGS["CM-8"]
        assert "name" in cm8
        assert "description" in cm8
        assert "checks" in cm8
        assert "inventory_data" in cm8["checks"]


class TestSSMControlMapperInitialization:
    """Test SSMControlMapper initialization."""

    def test_init_with_nist_framework(self):
        """Test initialization with NIST framework."""
        mapper = SSMControlMapper(framework="NIST800-53R5")
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == SSM_CONTROL_MAPPINGS

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = SSMControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == SSM_CONTROL_MAPPINGS


class TestAssessSSMCompliance:
    """Test assess_ssm_compliance method."""

    def test_assess_compliant_ssm_configuration(self):
        """Test assessing a fully compliant SSM configuration."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [
                {"InstanceId": "i-123", "PingStatus": "Online", "PatchSummary": {"Missing": 0}},
                {"InstanceId": "i-456", "PingStatus": "Online", "PatchSummary": {"Missing": 0}},
            ],
            "Associations": [{"AssociationId": "assoc-1"}],
            "Documents": [
                {"Name": "ConfigDoc", "DocumentType": "Command"},
                {"Name": "AutoDoc", "DocumentType": "Automation"},
            ],
            "Parameters": [{"Name": "param1", "Type": "String"}],
            "PatchBaselines": [{"BaselineId": "pb-123", "OperatingSystem": "AMAZON_LINUX_2"}],
            "MaintenanceWindows": [{"WindowId": "mw-123"}],
        }

        results = mapper.assess_ssm_compliance(ssm_data)

        assert results["CM-2"] == "PASS"
        assert results["CM-6"] == "PASS"
        assert results["SI-2"] == "PASS"
        assert results["CM-3"] == "PASS"
        assert results["CM-8"] == "PASS"

    def test_assess_ssm_without_managed_instances(self):
        """Test assessing SSM without managed instances."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [],
            "Associations": [{"AssociationId": "assoc-1"}],
            "Documents": [{"Name": "Doc1", "DocumentType": "Command"}],
            "Parameters": [{"Name": "param1"}],
            "PatchBaselines": [{"BaselineId": "pb-123"}],
        }

        results = mapper.assess_ssm_compliance(ssm_data)

        assert results["CM-2"] == "FAIL"
        assert results["CM-8"] == "FAIL"

    def test_assess_ssm_without_patch_baselines(self):
        """Test assessing SSM without patch baselines."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [{"InstanceId": "i-123", "PingStatus": "Online"}],
            "Associations": [{"AssociationId": "assoc-1"}],
            "Documents": [{"Name": "Doc1", "DocumentType": "Automation"}],
            "Parameters": [{"Name": "param1"}],
            "PatchBaselines": [],
        }

        results = mapper.assess_ssm_compliance(ssm_data)

        assert results["SI-2"] == "FAIL"


class TestAssessCM2:
    """Test _assess_cm2 method."""

    def test_ssm_with_online_instances_and_associations_passes(self):
        """Test SSM with online instances and associations passes."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [{"InstanceId": "i-123", "PingStatus": "Online"}],
            "Associations": [{"AssociationId": "assoc-1"}],
        }

        result = mapper._assess_cm2(ssm_data)
        assert result == "PASS"

    def test_ssm_without_managed_instances_fails(self):
        """Test SSM without managed instances fails."""
        mapper = SSMControlMapper()
        ssm_data = {"ManagedInstances": [], "Associations": [{"AssociationId": "assoc-1"}]}

        result = mapper._assess_cm2(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_offline_instances_fails(self):
        """Test SSM with only offline instances fails."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [{"InstanceId": "i-123", "PingStatus": "ConnectionLost"}],
            "Associations": [{"AssociationId": "assoc-1"}],
        }

        result = mapper._assess_cm2(ssm_data)
        assert result == "FAIL"

    def test_ssm_without_associations_fails(self):
        """Test SSM without associations fails."""
        mapper = SSMControlMapper()
        ssm_data = {"ManagedInstances": [{"InstanceId": "i-123", "PingStatus": "Online"}], "Associations": []}

        result = mapper._assess_cm2(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_mixed_instance_status_passes(self):
        """Test SSM with mixed instance status passes if at least one is online."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [
                {"InstanceId": "i-123", "PingStatus": "Online"},
                {"InstanceId": "i-456", "PingStatus": "ConnectionLost"},
            ],
            "Associations": [{"AssociationId": "assoc-1"}],
        }

        result = mapper._assess_cm2(ssm_data)
        assert result == "PASS"


class TestAssessCM6:
    """Test _assess_cm6 method."""

    def test_ssm_with_documents_parameters_and_associations_passes(self):
        """Test SSM with documents, parameters, and associations passes."""
        mapper = SSMControlMapper()
        ssm_data = {
            "Documents": [{"Name": "Doc1"}],
            "Parameters": [{"Name": "param1"}],
            "Associations": [{"AssociationId": "assoc-1"}],
        }

        result = mapper._assess_cm6(ssm_data)
        assert result == "PASS"

    def test_ssm_without_documents_fails(self):
        """Test SSM without documents fails."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [], "Parameters": [{"Name": "param1"}], "Associations": [{"AssociationId": "assoc-1"}]}

        result = mapper._assess_cm6(ssm_data)
        assert result == "FAIL"

    def test_ssm_without_parameters_fails(self):
        """Test SSM without parameters fails."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [{"Name": "Doc1"}], "Parameters": [], "Associations": [{"AssociationId": "assoc-1"}]}

        result = mapper._assess_cm6(ssm_data)
        assert result == "FAIL"

    def test_ssm_without_associations_fails(self):
        """Test SSM without associations fails."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [{"Name": "Doc1"}], "Parameters": [{"Name": "param1"}], "Associations": []}

        result = mapper._assess_cm6(ssm_data)
        assert result == "FAIL"


class TestAssessSI2:
    """Test _assess_si2 method."""

    def test_ssm_with_patch_baselines_and_compliant_instances_passes(self):
        """Test SSM with patch baselines and compliant instances passes."""
        mapper = SSMControlMapper()
        ssm_data = {
            "PatchBaselines": [{"BaselineId": "pb-123"}],
            "ManagedInstances": [{"InstanceId": "i-123", "PatchSummary": {"Missing": 0}}],
            "MaintenanceWindows": [{"WindowId": "mw-123"}],
        }

        result = mapper._assess_si2(ssm_data)
        assert result == "PASS"

    def test_ssm_without_patch_baselines_fails(self):
        """Test SSM without patch baselines fails."""
        mapper = SSMControlMapper()
        ssm_data = {
            "PatchBaselines": [],
            "ManagedInstances": [{"InstanceId": "i-123", "PatchSummary": {"Missing": 0}}],
            "MaintenanceWindows": [],
        }

        result = mapper._assess_si2(ssm_data)
        assert result == "FAIL"

    def test_ssm_without_patch_data_fails(self):
        """Test SSM without patch data on instances fails."""
        mapper = SSMControlMapper()
        ssm_data = {
            "PatchBaselines": [{"BaselineId": "pb-123"}],
            "ManagedInstances": [{"InstanceId": "i-123"}],
            "MaintenanceWindows": [],
        }

        result = mapper._assess_si2(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_missing_patches_fails(self):
        """Test SSM with missing patches fails."""
        mapper = SSMControlMapper()
        ssm_data = {
            "PatchBaselines": [{"BaselineId": "pb-123"}],
            "ManagedInstances": [
                {"InstanceId": "i-123", "PatchSummary": {"Missing": 5}},
                {"InstanceId": "i-456", "PatchSummary": {"Missing": 3}},
            ],
            "MaintenanceWindows": [],
        }

        result = mapper._assess_si2(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_patch_baselines_but_no_instances_passes(self):
        """Test SSM with patch baselines but no instances passes."""
        mapper = SSMControlMapper()
        ssm_data = {"PatchBaselines": [{"BaselineId": "pb-123"}], "ManagedInstances": [], "MaintenanceWindows": []}

        result = mapper._assess_si2(ssm_data)
        assert result == "PASS"

    def test_ssm_without_maintenance_windows_passes_with_note(self):
        """Test SSM without maintenance windows passes but notes recommendation."""
        mapper = SSMControlMapper()
        ssm_data = {
            "PatchBaselines": [{"BaselineId": "pb-123"}],
            "ManagedInstances": [{"InstanceId": "i-123", "PatchSummary": {"Missing": 0}}],
            "MaintenanceWindows": [],
        }

        result = mapper._assess_si2(ssm_data)
        assert result == "PASS"


class TestAssessCM3:
    """Test _assess_cm3 method."""

    def test_ssm_with_automation_documents_passes(self):
        """Test SSM with automation documents passes."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [{"Name": "AutoDoc", "DocumentType": "Automation"}]}

        result = mapper._assess_cm3(ssm_data)
        assert result == "PASS"

    def test_ssm_without_automation_documents_fails(self):
        """Test SSM without automation documents fails."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [{"Name": "CommandDoc", "DocumentType": "Command"}]}

        result = mapper._assess_cm3(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_no_documents_fails(self):
        """Test SSM with no documents fails."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": []}

        result = mapper._assess_cm3(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_multiple_automation_documents_passes(self):
        """Test SSM with multiple automation documents passes."""
        mapper = SSMControlMapper()
        ssm_data = {
            "Documents": [
                {"Name": "AutoDoc1", "DocumentType": "Automation"},
                {"Name": "AutoDoc2", "DocumentType": "Automation"},
                {"Name": "CommandDoc", "DocumentType": "Command"},
            ]
        }

        result = mapper._assess_cm3(ssm_data)
        assert result == "PASS"


class TestAssessCM8:
    """Test _assess_cm8 method."""

    def test_ssm_with_online_instances_passes(self):
        """Test SSM with online instances passes."""
        mapper = SSMControlMapper()
        ssm_data = {"ManagedInstances": [{"InstanceId": "i-123", "PingStatus": "Online"}]}

        result = mapper._assess_cm8(ssm_data)
        assert result == "PASS"

    def test_ssm_without_managed_instances_fails(self):
        """Test SSM without managed instances fails."""
        mapper = SSMControlMapper()
        ssm_data = {"ManagedInstances": []}

        result = mapper._assess_cm8(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_offline_instances_fails(self):
        """Test SSM with only offline instances fails."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [
                {"InstanceId": "i-123", "PingStatus": "ConnectionLost"},
                {"InstanceId": "i-456", "PingStatus": "Inactive"},
            ]
        }

        result = mapper._assess_cm8(ssm_data)
        assert result == "FAIL"

    def test_ssm_with_mixed_instance_status_passes(self):
        """Test SSM with mixed instance status passes if at least one is online."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [
                {"InstanceId": "i-123", "PingStatus": "Online"},
                {"InstanceId": "i-456", "PingStatus": "ConnectionLost"},
            ]
        }

        result = mapper._assess_cm8(ssm_data)
        assert result == "PASS"


class TestGetControlDescription:
    """Test get_control_description method."""

    def test_get_cm2_description(self):
        """Test getting CM-2 description."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("CM-2")

        assert description is not None
        assert "Baseline Configuration" in description

    def test_get_cm6_description(self):
        """Test getting CM-6 description."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("CM-6")

        assert description is not None
        assert "Configuration Settings" in description

    def test_get_si2_description(self):
        """Test getting SI-2 description."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("SI-2")

        assert description is not None
        assert "Flaw Remediation" in description

    def test_get_cm3_description(self):
        """Test getting CM-3 description."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("CM-3")

        assert description is not None
        assert "Configuration Change Control" in description

    def test_get_cm8_description(self):
        """Test getting CM-8 description."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("CM-8")

        assert description is not None
        assert "System Component Inventory" in description

    def test_get_unknown_control_description(self):
        """Test getting description for unknown control."""
        mapper = SSMControlMapper()
        description = mapper.get_control_description("UNKNOWN-1")

        assert description is None


class TestGetMappedControls:
    """Test get_mapped_controls method."""

    def test_get_mapped_controls(self):
        """Test getting all mapped controls."""
        mapper = SSMControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == 5
        assert "CM-2" in controls
        assert "CM-6" in controls
        assert "SI-2" in controls
        assert "CM-3" in controls
        assert "CM-8" in controls

    def test_controls_are_unique(self):
        """Test that returned controls are unique."""
        mapper = SSMControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == len(set(controls))


class TestGetCheckDetails:
    """Test get_check_details method."""

    def test_get_cm2_check_details(self):
        """Test getting CM-2 check details."""
        mapper = SSMControlMapper()
        details = mapper.get_check_details("CM-2")

        assert details is not None
        assert "managed_instances" in details
        assert "inventory_collection" in details
        assert "state_manager" in details
        assert details["managed_instances"]["weight"] == 100

    def test_get_si2_check_details(self):
        """Test getting SI-2 check details."""
        mapper = SSMControlMapper()
        details = mapper.get_check_details("SI-2")

        assert details is not None
        assert "patch_baselines" in details
        assert "patch_compliance" in details
        assert "maintenance_windows" in details

    def test_get_cm3_check_details(self):
        """Test getting CM-3 check details."""
        mapper = SSMControlMapper()
        details = mapper.get_check_details("CM-3")

        assert details is not None
        assert "automation_documents" in details

    def test_get_unknown_control_check_details(self):
        """Test getting check details for unknown control."""
        mapper = SSMControlMapper()
        details = mapper.get_check_details("UNKNOWN-1")

        assert details is None

    def test_check_details_structure(self):
        """Test check details have required structure."""
        mapper = SSMControlMapper()
        details = mapper.get_check_details("CM-2")

        for check_name, check_data in details.items():
            assert "weight" in check_data
            assert "pass_criteria" in check_data
            assert "fail_criteria" in check_data


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_ssm_data(self):
        """Test assessment with completely empty SSM data."""
        mapper = SSMControlMapper()
        ssm_data = {}

        results = mapper.assess_ssm_compliance(ssm_data)

        # All controls should fail with empty data
        assert results["CM-2"] == "FAIL"
        assert results["CM-6"] == "FAIL"
        assert results["SI-2"] == "FAIL"
        assert results["CM-3"] == "FAIL"
        assert results["CM-8"] == "FAIL"

    def test_ssm_data_with_none_values(self):
        """Test assessment with None values in SSM data."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": None,
            "Associations": None,
            "Documents": None,
            "Parameters": None,
            "PatchBaselines": None,
        }

        # The source code doesn't handle None values, so this will raise TypeError
        # Testing that the code fails appropriately when given None instead of lists
        with pytest.raises(TypeError):
            mapper.assess_ssm_compliance(ssm_data)

    def test_missing_ping_status(self):
        """Test instances without PingStatus attribute."""
        mapper = SSMControlMapper()
        ssm_data = {
            "ManagedInstances": [{"InstanceId": "i-123"}],
            "Associations": [{"AssociationId": "assoc-1"}],
        }

        result = mapper._assess_cm2(ssm_data)
        # Should fail because no instances have Online status
        assert result == "FAIL"

    def test_missing_document_type(self):
        """Test documents without DocumentType attribute."""
        mapper = SSMControlMapper()
        ssm_data = {"Documents": [{"Name": "Doc1"}]}

        result = mapper._assess_cm3(ssm_data)
        # Should fail because no Automation documents found
        assert result == "FAIL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
