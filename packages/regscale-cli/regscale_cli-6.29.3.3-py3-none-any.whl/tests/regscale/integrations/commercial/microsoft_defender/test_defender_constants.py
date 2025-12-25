#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Microsoft Defender constants"""
import pytest

from regscale.integrations.commercial.microsoft_defender import defender_constants


class TestDefenderConstants:
    """Test class for Microsoft Defender constants"""

    def test_date_format_constant(self):
        """Test DATE_FORMAT constant exists and has correct value"""
        assert hasattr(defender_constants, "DATE_FORMAT")
        assert defender_constants.DATE_FORMAT == "%Y-%m-%dT%H:%M:%S"

    def test_identification_type_constant(self):
        """Test IDENTIFICATION_TYPE constant exists and has correct value"""
        assert hasattr(defender_constants, "IDENTIFICATION_TYPE")
        assert defender_constants.IDENTIFICATION_TYPE == "Vulnerability Assessment"

    def test_cloud_recs_constant(self):
        """Test CLOUD_RECS constant exists and has correct value"""
        assert hasattr(defender_constants, "CLOUD_RECS")
        assert defender_constants.CLOUD_RECS == "Microsoft Defender for Cloud Recommendation"

    def test_app_json_constant(self):
        """Test APP_JSON constant exists and has correct value"""
        assert hasattr(defender_constants, "APP_JSON")
        assert defender_constants.APP_JSON == "application/json"

    def test_afd_endpoints_constant(self):
        """Test AFD_ENDPOINTS constant exists and has correct value"""
        assert hasattr(defender_constants, "AFD_ENDPOINTS")
        assert defender_constants.AFD_ENDPOINTS == "microsoft.cdn/profiles/afdendpoints"

    def test_resources_query_constant(self):
        """Test RESOURCES_QUERY constant exists and contains expected content"""
        assert hasattr(defender_constants, "RESOURCES_QUERY")
        assert isinstance(defender_constants.RESOURCES_QUERY, str)
        assert "resources" in defender_constants.RESOURCES_QUERY
        assert "subscriptionId" in defender_constants.RESOURCES_QUERY
        assert "{SUBSCRIPTION_ID}" in defender_constants.RESOURCES_QUERY
        assert "resourceName = name" in defender_constants.RESOURCES_QUERY
        assert "resourceType = type" in defender_constants.RESOURCES_QUERY
        assert "resourceLocation = location" in defender_constants.RESOURCES_QUERY
        assert "resourceGroup = resourceGroup" in defender_constants.RESOURCES_QUERY
        assert "resourceId = id" in defender_constants.RESOURCES_QUERY

    def test_container_scan_query_constant(self):
        """Test CONTAINER_SCAN_QUERY constant exists and contains expected content"""
        assert hasattr(defender_constants, "CONTAINER_SCAN_QUERY")
        assert isinstance(defender_constants.CONTAINER_SCAN_QUERY, str)
        assert "securityresources" in defender_constants.CONTAINER_SCAN_QUERY
        assert "microsoft.security/assessments" in defender_constants.CONTAINER_SCAN_QUERY
        assert "{RESOURCE_GROUP}" in defender_constants.CONTAINER_SCAN_QUERY
        assert "subassessments" in defender_constants.CONTAINER_SCAN_QUERY
        assert "severity" in defender_constants.CONTAINER_SCAN_QUERY

    def test_db_scan_query_constant(self):
        """Test DB_SCAN_QUERY constant exists and contains expected content"""
        assert hasattr(defender_constants, "DB_SCAN_QUERY")
        assert isinstance(defender_constants.DB_SCAN_QUERY, str)
        assert "securityresources" in defender_constants.DB_SCAN_QUERY
        assert "microsoft.security/assessments/subassessments" in defender_constants.DB_SCAN_QUERY
        assert "{ASSESSMENT_KEY}" in defender_constants.DB_SCAN_QUERY
        assert "{SUBSCRIPTION_ID}" in defender_constants.DB_SCAN_QUERY
        assert "Unhealthy" in defender_constants.DB_SCAN_QUERY

    def test_resources_query_formatting(self):
        """Test that RESOURCES_QUERY can be formatted with subscription ID"""
        subscription_id = "test-subscription-123"
        formatted_query = defender_constants.RESOURCES_QUERY.format(SUBSCRIPTION_ID=subscription_id)

        assert subscription_id in formatted_query
        assert "{SUBSCRIPTION_ID}" not in formatted_query

    def test_container_scan_query_formatting(self):
        """Test that CONTAINER_SCAN_QUERY can be formatted with resource group"""
        resource_group = "test-resource-group"
        formatted_query = defender_constants.CONTAINER_SCAN_QUERY.format(RESOURCE_GROUP=resource_group)

        assert resource_group in formatted_query
        assert "{RESOURCE_GROUP}" not in formatted_query

    def test_db_scan_query_formatting(self):
        """Test that DB_SCAN_QUERY can be formatted with assessment key and subscription ID"""
        assessment_key = "test-assessment-key"
        subscription_id = "test-subscription-123"
        formatted_query = defender_constants.DB_SCAN_QUERY.format(
            ASSESSMENT_KEY=assessment_key, SUBSCRIPTION_ID=subscription_id
        )

        assert assessment_key in formatted_query
        assert subscription_id in formatted_query
        assert "{ASSESSMENT_KEY}" not in formatted_query
        assert "{SUBSCRIPTION_ID}" not in formatted_query

    def test_all_constants_are_strings(self):
        """Test that all constants are strings"""
        constants_to_check = [
            "DATE_FORMAT",
            "IDENTIFICATION_TYPE",
            "CLOUD_RECS",
            "APP_JSON",
            "AFD_ENDPOINTS",
            "RESOURCES_QUERY",
            "CONTAINER_SCAN_QUERY",
            "DB_SCAN_QUERY",
        ]

        for constant_name in constants_to_check:
            constant_value = getattr(defender_constants, constant_name)
            assert isinstance(constant_value, str), f"{constant_name} should be a string"

    def test_query_constants_multiline(self):
        """Test that query constants are properly formatted multiline strings"""
        query_constants = ["RESOURCES_QUERY", "CONTAINER_SCAN_QUERY", "DB_SCAN_QUERY"]

        for constant_name in query_constants:
            query = getattr(defender_constants, constant_name)
            # Should contain newlines indicating multiline format
            assert "\n" in query, f"{constant_name} should be a multiline string"
            # Should not start or end with excessive whitespace
            assert not query.startswith("\n\n"), f"{constant_name} should not start with excessive newlines"
            assert not query.endswith("\n\n\n"), f"{constant_name} should not end with excessive newlines"

    def test_resources_query_kusto_syntax(self):
        """Test that RESOURCES_QUERY contains valid Kusto query syntax"""
        query = defender_constants.RESOURCES_QUERY

        # Check for key Kusto operators and functions
        assert "extend" in query
        assert "case(" in query
        assert "project" in query
        assert "tostring(" in query
        # Check for proper field references
        assert "resourceType =~" in query
        assert "properties" in query

    def test_container_scan_query_kusto_syntax(self):
        """Test that CONTAINER_SCAN_QUERY contains valid Kusto query syntax"""
        query = defender_constants.CONTAINER_SCAN_QUERY

        # Check for key Kusto operators
        assert "summarize" in query
        assert "join" in query
        assert "kind=inner" in query
        assert "extract(" in query
        assert "where" in query
        assert "parse_json(" in query
        assert "order by" in query

    def test_db_scan_query_kusto_syntax(self):
        """Test that DB_SCAN_QUERY contains valid Kusto query syntax"""
        query = defender_constants.DB_SCAN_QUERY

        # Check for key Kusto operators and functions
        assert "extend" in query
        assert "extract(" in query
        assert "strcat(" in query
        assert "iff(" in query
        assert "project" in query
        assert "where" in query

    # ==============================
    # NEW TESTS FOR ENTRA CONSTANTS
    # ==============================

    def test_entra_endpoints_constant(self):
        """Test ENTRA_ENDPOINTS constant exists and has correct structure"""
        assert hasattr(defender_constants, "ENTRA_ENDPOINTS")
        entra_endpoints = defender_constants.ENTRA_ENDPOINTS
        assert isinstance(entra_endpoints, dict)
        assert len(entra_endpoints) > 0

        # Test a few key endpoints exist
        expected_endpoints = [
            "users",
            "guest_users",
            "groups_and_members",
            "security_groups",
            "role_assignments",
            "role_definitions",
            "pim_assignments",
            "pim_eligibility",
            "conditional_access",
            "auth_methods_policy",
            "user_mfa_registration",
            "mfa_registered_users",
            "sign_in_logs",
            "directory_audits",
            "provisioning_logs",
            "access_review_definitions",
            "access_review_instances",
            "access_review_decisions",
        ]

        for endpoint in expected_endpoints:
            assert endpoint in entra_endpoints, f"Missing endpoint: {endpoint}"

    def test_entra_endpoints_url_format(self):
        """Test ENTRA_ENDPOINTS URLs have correct format"""
        entra_endpoints = defender_constants.ENTRA_ENDPOINTS
        for key, url in entra_endpoints.items():
            assert isinstance(url, str), f"URL for {key} should be string"
            assert url.startswith("/"), f"URL for {key} should start with forward slash (relative URL)"
            assert (
                "?" in url or "$" in url or url.count("/") > 1
            ), f"URL for {key} should contain query parameters or path segments"

    def test_evidence_to_controls_mapping_constant(self):
        """Test EVIDENCE_TO_CONTROLS_MAPPING constant exists and has correct structure"""
        assert hasattr(defender_constants, "EVIDENCE_TO_CONTROLS_MAPPING")
        mapping = defender_constants.EVIDENCE_TO_CONTROLS_MAPPING
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

        # Test each evidence type maps to a list of control IDs
        for evidence_type, controls in mapping.items():
            assert isinstance(evidence_type, str), f"Evidence type should be string: {evidence_type}"
            assert isinstance(controls, list), f"Controls should be list for {evidence_type}"
            assert len(controls) > 0, f"Controls list should not be empty for {evidence_type}"

            # Test each control ID is a string
            for control in controls:
                assert isinstance(control, str), f"Control ID should be string: {control} for {evidence_type}"

    def test_evidence_to_controls_mapping_coverage(self):
        """Test EVIDENCE_TO_CONTROLS_MAPPING covers expected evidence types"""
        mapping = defender_constants.EVIDENCE_TO_CONTROLS_MAPPING
        expected_evidence_types = [
            "users",
            "users_delta",
            "guest_users",
            "groups_and_members",
            "security_groups",
            "role_assignments",
            "role_definitions",
            "pim_assignments",
            "pim_eligibility",
            "conditional_access",
            "auth_methods_policy",
            "user_mfa_registration",
            "mfa_registered_users",
            "sign_in_logs",
            "directory_audits",
            "provisioning_logs",
            "access_review_definitions",
        ]

        for evidence_type in expected_evidence_types:
            assert evidence_type in mapping, f"Missing evidence type mapping: {evidence_type}"

    def test_endpoint_parameters_mapping_constant(self):
        """Test ENDPOINT_PARAMETERS_MAPPING constant exists and has correct structure"""
        if hasattr(defender_constants, "ENDPOINT_PARAMETERS_MAPPING"):
            mapping = defender_constants.ENDPOINT_PARAMETERS_MAPPING
            assert isinstance(mapping, dict)

            # Test that certain endpoints requiring parameters are included
            for endpoint, params in mapping.items():
                assert isinstance(params, list), f"Parameters should be list for {endpoint}"
                for param in params:
                    assert isinstance(param, str), f"Parameter should be string: {param} for {endpoint}"

    def test_specific_entra_endpoint_formats(self):
        """Test specific endpoint URLs have expected formats"""
        entra_endpoints = defender_constants.ENTRA_ENDPOINTS

        # Test users endpoint
        if "users" in entra_endpoints:
            users_url = entra_endpoints["users"]
            assert "$select=" in users_url or "$" in users_url

        # Test sign-in logs endpoint
        if "sign_in_logs" in entra_endpoints:
            signin_url = entra_endpoints["sign_in_logs"]
            assert "auditLogs/signIns" in signin_url

        # Test groups and members endpoint
        if "groups_and_members" in entra_endpoints:
            groups_url = entra_endpoints["groups_and_members"]
            assert "groups" in groups_url

    def test_control_mappings_have_appropriate_controls(self):
        """Test that evidence types have appropriate control mappings"""
        mapping = defender_constants.EVIDENCE_TO_CONTROLS_MAPPING

        # Test that user-related evidence maps to access control (AC) controls
        user_evidence_types = ["users", "guest_users", "users_delta"]
        for evidence_type in user_evidence_types:
            if evidence_type in mapping:
                controls = mapping[evidence_type]
                # Should have at least some controls
                assert len(controls) > 0, f"User evidence {evidence_type} should have controls"

        # Test that authentication evidence maps to appropriate controls
        auth_evidence_types = ["user_mfa_registration", "mfa_registered_users", "auth_methods_policy"]
        for evidence_type in auth_evidence_types:
            if evidence_type in mapping:
                controls = mapping[evidence_type]
                # Should have at least some controls
                assert len(controls) > 0, f"Auth evidence {evidence_type} should have controls"

    def test_no_duplicate_controls_in_mappings(self):
        """Test that there are no duplicate controls in evidence mappings"""
        mapping = defender_constants.EVIDENCE_TO_CONTROLS_MAPPING
        for evidence_type, controls in mapping.items():
            unique_controls = set(controls)
            assert len(unique_controls) == len(controls), f"Duplicate controls found in {evidence_type}: {controls}"

    def test_entra_constants_not_empty(self):
        """Test that all Entra constants are properly initialized and not empty"""
        # ENTRA_ENDPOINTS should exist and not be empty
        assert hasattr(defender_constants, "ENTRA_ENDPOINTS")
        entra_endpoints = defender_constants.ENTRA_ENDPOINTS
        assert entra_endpoints is not None
        assert len(entra_endpoints) > 0

        # EVIDENCE_TO_CONTROLS_MAPPING should exist and not be empty
        assert hasattr(defender_constants, "EVIDENCE_TO_CONTROLS_MAPPING")
        evidence_mapping = defender_constants.EVIDENCE_TO_CONTROLS_MAPPING
        assert evidence_mapping is not None
        assert len(evidence_mapping) > 0

        # Note: EVIDENCE_TYPE_MAPPINGS doesn't exist in current implementation
