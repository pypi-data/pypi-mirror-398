#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Organizations Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.org_control_mappings import (
    COMPLIANT_ACCOUNT_STATUSES,
    ISO_27001_MAPPINGS,
    ORG_CONTROL_MAPPINGS,
    OrgControlMapper,
    RESTRICTIVE_SCP_PATTERNS,
)


class TestOrgControlMappings:
    """Test Organizations control mappings constants."""

    def test_org_control_mappings_exist(self):
        """Test that Organizations control mappings dictionary exists and has content."""
        assert len(ORG_CONTROL_MAPPINGS) > 0
        assert "AC-1" in ORG_CONTROL_MAPPINGS
        assert "PM-9" in ORG_CONTROL_MAPPINGS
        assert "AC-2" in ORG_CONTROL_MAPPINGS
        assert "AC-6" in ORG_CONTROL_MAPPINGS

    def test_ac1_mapping_structure(self):
        """Test AC-1 mapping structure."""
        ac1 = ORG_CONTROL_MAPPINGS["AC-1"]
        assert "name" in ac1
        assert "description" in ac1
        assert "checks" in ac1
        assert "scp_attached" in ac1["checks"]
        assert "organizational_structure" in ac1["checks"]

    def test_pm9_mapping_structure(self):
        """Test PM-9 mapping structure."""
        pm9 = ORG_CONTROL_MAPPINGS["PM-9"]
        assert "name" in pm9
        assert "description" in pm9
        assert "checks" in pm9
        assert "account_governance" in pm9["checks"]
        assert "policy_enforcement" in pm9["checks"]

    def test_ac2_mapping_structure(self):
        """Test AC-2 mapping structure."""
        ac2 = ORG_CONTROL_MAPPINGS["AC-2"]
        assert "name" in ac2
        assert "description" in ac2
        assert "checks" in ac2
        assert "active_accounts" in ac2["checks"]
        assert "account_tracking" in ac2["checks"]

    def test_ac6_mapping_structure(self):
        """Test AC-6 mapping structure."""
        ac6 = ORG_CONTROL_MAPPINGS["AC-6"]
        assert "name" in ac6
        assert "description" in ac6
        assert "checks" in ac6
        assert "restrictive_scps" in ac6["checks"]

    def test_iso_27001_mappings_exist(self):
        """Test ISO 27001 mappings exist."""
        assert len(ISO_27001_MAPPINGS) > 0
        assert "A.6.1.1" in ISO_27001_MAPPINGS
        assert "A.6.1.2" in ISO_27001_MAPPINGS

    def test_restrictive_scp_patterns(self):
        """Test restrictive SCP patterns list."""
        assert "DenyAllOutsideRegion" in RESTRICTIVE_SCP_PATTERNS
        assert "DenyRootAccount" in RESTRICTIVE_SCP_PATTERNS
        assert "RequireMFA" in RESTRICTIVE_SCP_PATTERNS
        assert "DenyCloudTrailDelete" in RESTRICTIVE_SCP_PATTERNS

    def test_compliant_account_statuses(self):
        """Test compliant account statuses list."""
        assert "ACTIVE" in COMPLIANT_ACCOUNT_STATUSES


class TestOrgControlMapperInitialization:
    """Test OrgControlMapper initialization."""

    def test_init_with_nist_framework(self):
        """Test initialization with NIST framework."""
        mapper = OrgControlMapper(framework="NIST800-53R5")
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == ORG_CONTROL_MAPPINGS

    def test_init_with_iso_framework(self):
        """Test initialization with ISO framework."""
        mapper = OrgControlMapper(framework="ISO27001")
        assert mapper.framework == "ISO27001"
        assert mapper.mappings == ISO_27001_MAPPINGS

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = OrgControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == ORG_CONTROL_MAPPINGS


class TestAssessOrganizationCompliance:
    """Test assess_organization_compliance method."""

    def test_assess_compliant_organization(self):
        """Test assessing a compliant organization."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [
                {"Name": "FullAWSAccess"},
                {"Name": "DenyRootAccount"},
                {"Name": "RestrictRegions"},
            ],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}, {"Name": "Development"}],
            "accounts": [
                {"Id": "123456789012", "Status": "ACTIVE", "Email": "prod@example.com"},
                {"Id": "123456789013", "Status": "ACTIVE", "Email": "dev@example.com"},
            ],
        }

        results = mapper.assess_organization_compliance(org_data)

        assert results["AC-1"] == "PASS"
        assert results["PM-9"] == "PASS"
        assert results["AC-2"] == "PASS"
        assert results["AC-6"] == "PASS"

    def test_assess_organization_no_scps(self):
        """Test assessing organization with no restrictive SCPs."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
            "accounts": [{"Id": "123456789012", "Status": "ACTIVE", "Email": "prod@example.com"}],
        }

        results = mapper.assess_organization_compliance(org_data)

        assert results["AC-1"] == "FAIL"
        assert results["PM-9"] == "FAIL"
        assert results["AC-2"] == "PASS"
        assert results["AC-6"] == "FAIL"

    def test_assess_organization_flat_structure(self):
        """Test assessing organization with flat structure."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "DenyRootAccount"}],
            "organizational_units": [{"Name": "Root"}],
            "accounts": [{"Id": "123456789012", "Status": "ACTIVE", "Email": "admin@example.com"}],
        }

        results = mapper.assess_organization_compliance(org_data)

        assert results["AC-1"] == "FAIL"
        assert results["PM-9"] == "FAIL"

    def test_assess_organization_with_inactive_accounts(self):
        """Test assessing organization with inactive accounts."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "DenyRootAccount"}],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
            "accounts": [
                {"Id": "123456789012", "Status": "ACTIVE", "Email": "prod@example.com"},
                {"Id": "123456789013", "Status": "SUSPENDED", "Email": "old@example.com"},
            ],
        }

        results = mapper.assess_organization_compliance(org_data)

        assert results["AC-2"] == "FAIL"


class TestAssessAC1:
    """Test _assess_ac1 method."""

    def test_organization_with_restrictive_scps_and_ous_passes(self):
        """Test organization with restrictive SCPs and OUs passes."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}, {"Name": "DenyRootAccount"}],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
        }

        result = mapper._assess_ac1(org_data)
        assert result == "PASS"

    def test_organization_without_restrictive_scps_fails(self):
        """Test organization without restrictive SCPs fails."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
        }

        result = mapper._assess_ac1(org_data)
        assert result == "FAIL"

    def test_organization_without_ous_fails(self):
        """Test organization without organizational units fails."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "DenyRootAccount"}],
            "organizational_units": [{"Name": "Root"}],
        }

        result = mapper._assess_ac1(org_data)
        assert result == "FAIL"

    def test_organization_with_empty_scps_list(self):
        """Test organization with empty SCPs list."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [],
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
        }

        result = mapper._assess_ac1(org_data)
        assert result == "FAIL"


class TestAssessPM9:
    """Test _assess_pm9 method."""

    def test_organization_with_env_separation_and_restrictive_scps_passes(self):
        """Test organization with environment separation and restrictive SCPs passes."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}, {"Name": "Development"}],
            "service_control_policies": [{"Name": "RestrictRegions"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "PASS"

    def test_organization_with_prod_ou_passes(self):
        """Test organization with prod OU passes."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Prod"}],
            "service_control_policies": [{"Name": "DenyLeaveOrganization"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "PASS"

    def test_organization_with_sandbox_ou_passes(self):
        """Test organization with sandbox OU passes."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Sandbox"}],
            "service_control_policies": [{"Name": "RequireMFA"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "PASS"

    def test_organization_without_env_separation_fails(self):
        """Test organization without environment separation fails."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Applications"}],
            "service_control_policies": [{"Name": "RestrictRegions"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "FAIL"

    def test_organization_without_restrictive_scps_fails(self):
        """Test organization without restrictive SCPs fails."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Production"}],
            "service_control_policies": [{"Name": "FullAWSAccess"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "FAIL"

    def test_organization_with_test_ou_passes(self):
        """Test organization with test OU passes."""
        mapper = OrgControlMapper()
        org_data = {
            "organizational_units": [{"Name": "Root"}, {"Name": "Test"}],
            "service_control_policies": [{"Name": "DenyGuardDutyDisable"}],
        }

        result = mapper._assess_pm9(org_data)
        assert result == "PASS"


class TestAssessAC2:
    """Test _assess_ac2 method."""

    def test_organization_with_all_active_accounts_passes(self):
        """Test organization with all active accounts passes."""
        mapper = OrgControlMapper()
        org_data = {
            "accounts": [
                {"Id": "123456789012", "Status": "ACTIVE", "Email": "account1@example.com"},
                {"Id": "123456789013", "Status": "ACTIVE", "Email": "account2@example.com"},
            ]
        }

        result = mapper._assess_ac2(org_data)
        assert result == "PASS"

    def test_organization_with_no_accounts_fails(self):
        """Test organization with no accounts fails."""
        mapper = OrgControlMapper()
        org_data = {"accounts": []}

        result = mapper._assess_ac2(org_data)
        assert result == "FAIL"

    def test_organization_with_suspended_accounts_fails(self):
        """Test organization with suspended accounts fails."""
        mapper = OrgControlMapper()
        org_data = {
            "accounts": [
                {"Id": "123456789012", "Status": "ACTIVE", "Email": "active@example.com"},
                {"Id": "123456789013", "Status": "SUSPENDED", "Email": "suspended@example.com"},
            ]
        }

        result = mapper._assess_ac2(org_data)
        assert result == "FAIL"

    def test_organization_with_accounts_missing_email_fails(self):
        """Test organization with accounts missing email fails."""
        mapper = OrgControlMapper()
        org_data = {
            "accounts": [
                {"Id": "123456789012", "Status": "ACTIVE", "Email": "account1@example.com"},
                {"Id": "123456789013", "Status": "ACTIVE", "Email": ""},
            ]
        }

        result = mapper._assess_ac2(org_data)
        assert result == "FAIL"

    def test_organization_with_accounts_without_email_key_fails(self):
        """Test organization with accounts without email key fails."""
        mapper = OrgControlMapper()
        org_data = {"accounts": [{"Id": "123456789012", "Status": "ACTIVE"}]}

        result = mapper._assess_ac2(org_data)
        assert result == "FAIL"


class TestAssessAC6:
    """Test _assess_ac6 method."""

    def test_organization_with_restrictive_scps_passes(self):
        """Test organization with restrictive SCPs passes."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}, {"Name": "DenyRootAccount"}],
        }

        result = mapper._assess_ac6(org_data)
        assert result == "PASS"

    def test_organization_with_deny_in_scp_name_passes(self):
        """Test organization with Deny in SCP name passes."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}, {"Name": "DenyS3PublicAccess"}],
        }

        result = mapper._assess_ac6(org_data)
        assert result == "PASS"

    def test_organization_with_only_full_access_fails(self):
        """Test organization with only FullAWSAccess SCP fails."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}],
        }

        result = mapper._assess_ac6(org_data)
        assert result == "FAIL"

    def test_organization_without_restrictive_scps_fails(self):
        """Test organization without restrictive SCPs fails."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "FullAWSAccess"}, {"Name": "AllowAllServices"}],
        }

        result = mapper._assess_ac6(org_data)
        assert result == "FAIL"

    def test_organization_with_restrictregions_passes(self):
        """Test organization with RestrictRegions SCP passes."""
        mapper = OrgControlMapper()
        org_data = {
            "service_control_policies": [{"Name": "RestrictRegions"}],
        }

        result = mapper._assess_ac6(org_data)
        assert result == "PASS"


class TestGetControlDescription:
    """Test get_control_description method."""

    def test_get_ac1_description(self):
        """Test getting AC-1 description."""
        mapper = OrgControlMapper()
        description = mapper.get_control_description("AC-1")

        assert description is not None
        assert "Policy and Procedures" in description

    def test_get_pm9_description(self):
        """Test getting PM-9 description."""
        mapper = OrgControlMapper()
        description = mapper.get_control_description("PM-9")

        assert description is not None
        assert "Risk Management Strategy" in description

    def test_get_ac2_description(self):
        """Test getting AC-2 description."""
        mapper = OrgControlMapper()
        description = mapper.get_control_description("AC-2")

        assert description is not None
        assert "Account Management" in description

    def test_get_ac6_description(self):
        """Test getting AC-6 description."""
        mapper = OrgControlMapper()
        description = mapper.get_control_description("AC-6")

        assert description is not None
        assert "Least Privilege" in description

    def test_get_unknown_control_description(self):
        """Test getting description for unknown control."""
        mapper = OrgControlMapper()
        description = mapper.get_control_description("UNKNOWN-1")

        assert description is None

    def test_get_iso_control_description(self):
        """Test getting ISO control description."""
        mapper = OrgControlMapper(framework="ISO27001")
        description = mapper.get_control_description("A.6.1.1")

        assert description is not None
        assert "security roles" in description.lower()


class TestGetMappedControls:
    """Test get_mapped_controls method."""

    def test_get_nist_controls(self):
        """Test getting NIST controls."""
        mapper = OrgControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) > 0
        assert "AC-1" in controls
        assert "PM-9" in controls
        assert "AC-2" in controls
        assert "AC-6" in controls

    def test_get_iso_controls(self):
        """Test getting ISO controls."""
        mapper = OrgControlMapper(framework="ISO27001")
        controls = mapper.get_mapped_controls()

        assert len(controls) > 0
        assert "A.6.1.1" in controls
        assert "A.6.1.2" in controls

    def test_controls_are_unique(self):
        """Test that returned controls are unique."""
        mapper = OrgControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == len(set(controls))


class TestGetCheckDetails:
    """Test get_check_details method."""

    def test_get_ac1_check_details(self):
        """Test getting AC-1 check details."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("AC-1")

        assert details is not None
        assert "scp_attached" in details
        assert "organizational_structure" in details
        assert details["scp_attached"]["weight"] == 100

    def test_get_pm9_check_details(self):
        """Test getting PM-9 check details."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("PM-9")

        assert details is not None
        assert "account_governance" in details
        assert "policy_enforcement" in details

    def test_get_ac2_check_details(self):
        """Test getting AC-2 check details."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("AC-2")

        assert details is not None
        assert "active_accounts" in details
        assert "account_tracking" in details

    def test_get_ac6_check_details(self):
        """Test getting AC-6 check details."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("AC-6")

        assert details is not None
        assert "restrictive_scps" in details

    def test_get_unknown_control_check_details(self):
        """Test getting check details for unknown control."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("UNKNOWN-1")

        assert details is None

    def test_check_details_structure(self):
        """Test check details have required structure."""
        mapper = OrgControlMapper()
        details = mapper.get_check_details("AC-1")

        for check_name, check_data in details.items():
            assert "weight" in check_data
            assert "pass_criteria" in check_data
            assert "fail_criteria" in check_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
