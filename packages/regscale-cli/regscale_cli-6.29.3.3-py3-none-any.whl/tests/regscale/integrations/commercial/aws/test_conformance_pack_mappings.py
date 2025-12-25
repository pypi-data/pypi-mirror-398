#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Config Conformance Pack Mappings."""

import pytest

from regscale.integrations.commercial.aws.conformance_pack_mappings import (
    extract_control_ids_from_rule_name,
    extract_control_ids_from_tags,
    get_control_mappings_for_framework,
    map_rule_to_controls,
    NIST_80053_R5_MAPPINGS,
)


class TestExtractControlIdsFromRuleName:
    """Test extracting control IDs from rule names."""

    def test_extract_single_control(self):
        """Test extracting a single control ID."""
        rule_name = "ac-2-iam-user-mfa-enabled"
        control_ids = extract_control_ids_from_rule_name(rule_name)
        assert "AC-2" in control_ids

    def test_extract_multiple_controls(self):
        """Test extracting multiple control IDs."""
        rule_name = "AC-2-AU-3-combined-rule"
        control_ids = extract_control_ids_from_rule_name(rule_name)
        assert "AC-2" in control_ids
        assert "AU-3" in control_ids

    def test_extract_control_with_enhancement(self):
        """Test extracting control with enhancement - currently only extracts base control."""
        rule_name = "ia-2-1-mfa-enabled-for-console-access"
        control_ids = extract_control_ids_from_rule_name(rule_name)
        # Note: Current implementation extracts base control only (IA-2), not enhancement (IA-2(1))
        assert "IA-2" in control_ids

    def test_no_controls_in_name(self):
        """Test rule name with no control IDs."""
        rule_name = "encrypted-volumes"
        control_ids = extract_control_ids_from_rule_name(rule_name)
        assert len(control_ids) == 0

    def test_case_insensitive(self):
        """Test case-insensitive extraction."""
        rule_name = "ac-2-iam-user-mfa-enabled"
        control_ids = extract_control_ids_from_rule_name(rule_name)
        assert "AC-2" in control_ids


class TestExtractControlIdsFromTags:
    """Test extracting control IDs from tags."""

    def test_extract_single_control_from_controlid_tag(self):
        """Test extracting single control from ControlID tag."""
        tags = {"ControlID": "AC-2"}
        control_ids = extract_control_ids_from_tags(tags)
        assert "AC-2" in control_ids

    def test_extract_multiple_controls_from_controlid_tag(self):
        """Test extracting multiple controls from ControlID tag."""
        tags = {"ControlID": "AC-2,AU-3,SI-2"}
        control_ids = extract_control_ids_from_tags(tags)
        assert "AC-2" in control_ids
        assert "AU-3" in control_ids
        assert "SI-2" in control_ids

    def test_extract_from_controlids_tag(self):
        """Test extracting from ControlIDs (plural) tag."""
        tags = {"ControlIDs": "AC-2,AU-3"}
        control_ids = extract_control_ids_from_tags(tags)
        assert "AC-2" in control_ids
        assert "AU-3" in control_ids

    def test_extract_from_control_id_hyphen_tag(self):
        """Test extracting from Control-ID tag."""
        tags = {"Control-ID": "AC-2"}
        control_ids = extract_control_ids_from_tags(tags)
        assert "AC-2" in control_ids

    def test_no_control_tags(self):
        """Test tags with no control IDs."""
        tags = {"Environment": "Production", "Owner": "Security"}
        control_ids = extract_control_ids_from_tags(tags)
        assert len(control_ids) == 0

    def test_empty_tags(self):
        """Test empty tags dictionary."""
        control_ids = extract_control_ids_from_tags({})
        assert len(control_ids) == 0


class TestGetControlMappingsForFramework:
    """Test getting control mappings for framework."""

    def test_nist_800_53_r5_framework(self):
        """Test NIST 800-53 R5 framework mappings."""
        mappings = get_control_mappings_for_framework("NIST800-53R5")
        assert len(mappings) > 0
        assert "iam-password-policy" in mappings
        assert "AC-2" in mappings["iam-password-policy"]

    def test_nist_alternate_formats(self):
        """Test alternate NIST framework format names."""
        mappings1 = get_control_mappings_for_framework("NIST800-53R5")
        mappings2 = get_control_mappings_for_framework("NIST-800-53-R5")
        mappings3 = get_control_mappings_for_framework("NIST_800_53_R5")

        assert mappings1 == mappings2 == mappings3

    def test_unknown_framework(self):
        """Test unknown framework returns empty mappings."""
        mappings = get_control_mappings_for_framework("UNKNOWN_FRAMEWORK")
        assert len(mappings) == 0


class TestMapRuleToControls:
    """Test mapping rules to controls."""

    def test_map_via_framework_mappings(self):
        """Test mapping via framework-specific mappings."""
        control_ids = map_rule_to_controls(rule_name="iam-password-policy", framework="NIST800-53R5")

        assert "AC-2" in control_ids
        assert "IA-5" in control_ids

    def test_map_via_tags_priority(self):
        """Test that tags take priority over framework mappings."""
        rule_tags = {"ControlID": "AC-5"}
        control_ids = map_rule_to_controls(
            rule_name="iam-password-policy", rule_tags=rule_tags, framework="NIST800-53R5"
        )

        # Should include both framework mapping and tag
        assert "AC-2" in control_ids  # From framework mapping
        assert "IA-5" in control_ids  # From framework mapping
        assert "AC-5" in control_ids  # From tags

    def test_map_via_rule_name_pattern(self):
        """Test mapping via pattern matching in rule name."""
        control_ids = map_rule_to_controls(rule_name="custom-ac-2-check-rule", framework="NIST800-53R5")

        assert "AC-2" in control_ids

    def test_map_via_description_pattern(self):
        """Test mapping via pattern matching in description."""
        control_ids = map_rule_to_controls(
            rule_name="custom-check", rule_description="This rule checks AC-2 compliance", framework="NIST800-53R5"
        )

        assert "AC-2" in control_ids

    def test_no_mapping_found(self):
        """Test rule with no mappable controls."""
        control_ids = map_rule_to_controls(
            rule_name="unknown-custom-rule", rule_description="Some custom check", framework="NIST800-53R5"
        )

        assert len(control_ids) == 0

    def test_deduplicate_controls(self):
        """Test that duplicate controls are removed."""
        rule_tags = {"ControlID": "AC-2,AU-3"}
        control_ids = map_rule_to_controls(
            rule_name="ac-2-au-3-combined-check", rule_tags=rule_tags, framework="NIST800-53R5"
        )

        # Should have AC-2 and AU-3 only once each
        assert control_ids.count("AC-2") == 1
        assert control_ids.count("AU-3") == 1


class TestNIST80053R5Mappings:
    """Test NIST 800-53 R5 mappings structure."""

    def test_mappings_exist(self):
        """Test that mappings dictionary exists and has content."""
        assert len(NIST_80053_R5_MAPPINGS) > 0

    def test_cloudtrail_mapping(self):
        """Test CloudTrail rule mappings."""
        assert "cloudtrail-enabled" in NIST_80053_R5_MAPPINGS
        assert "AU-2" in NIST_80053_R5_MAPPINGS["cloudtrail-enabled"]
        assert "AU-3" in NIST_80053_R5_MAPPINGS["cloudtrail-enabled"]

    def test_iam_password_policy_mapping(self):
        """Test IAM password policy mappings."""
        assert "iam-password-policy" in NIST_80053_R5_MAPPINGS
        assert "AC-2" in NIST_80053_R5_MAPPINGS["iam-password-policy"]
        assert "IA-5" in NIST_80053_R5_MAPPINGS["iam-password-policy"]

    def test_encryption_mappings(self):
        """Test encryption-related mappings."""
        assert "encrypted-volumes" in NIST_80053_R5_MAPPINGS
        assert "SC-13" in NIST_80053_R5_MAPPINGS["encrypted-volumes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
