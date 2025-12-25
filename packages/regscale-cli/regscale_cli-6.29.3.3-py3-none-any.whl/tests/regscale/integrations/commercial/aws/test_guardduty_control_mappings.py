#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS GuardDuty Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.guardduty_control_mappings import (
    CVE_RELATED_FINDING_TYPES,
    GUARDDUTY_CONTROL_MAPPINGS,
    SEVERITY_MAPPING,
    GuardDutyControlMapper,
)


class TestGuardDutyControlMapper:
    """Test GuardDutyControlMapper class."""

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = GuardDutyControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == GUARDDUTY_CONTROL_MAPPINGS

    def test_init_custom_framework(self):
        """Test initialization with custom framework."""
        mapper = GuardDutyControlMapper(framework="ISO27001")
        assert mapper.framework == "ISO27001"
        assert mapper.mappings == GUARDDUTY_CONTROL_MAPPINGS

    def test_get_mapped_controls(self):
        """Test getting list of mapped controls."""
        mapper = GuardDutyControlMapper()
        controls = mapper.get_mapped_controls()
        assert isinstance(controls, list)
        assert len(controls) > 0
        assert "SI-4" in controls
        assert "IR-4" in controls
        assert "IR-5" in controls
        assert "SI-3" in controls
        assert "RA-5" in controls

    def test_get_control_description_valid(self):
        """Test getting control description for valid control."""
        mapper = GuardDutyControlMapper()
        description = mapper.get_control_description("SI-4")
        assert description is not None
        assert "System Monitoring" in description
        assert "Monitor the system to detect attacks" in description

    def test_get_control_description_invalid(self):
        """Test getting control description for invalid control."""
        mapper = GuardDutyControlMapper()
        description = mapper.get_control_description("INVALID-CONTROL")
        assert description is None

    def test_get_check_details_valid(self):
        """Test getting check details for valid control."""
        mapper = GuardDutyControlMapper()
        checks = mapper.get_check_details("SI-4")
        assert checks is not None
        assert isinstance(checks, dict)
        assert "detector_enabled" in checks
        assert "findings_processed" in checks
        assert checks["detector_enabled"]["weight"] == 100

    def test_get_check_details_invalid(self):
        """Test getting check details for invalid control."""
        mapper = GuardDutyControlMapper()
        checks = mapper.get_check_details("INVALID-CONTROL")
        assert checks is None


class TestAssessGuardDutyCompliance:
    """Test assess_guardduty_compliance method."""

    def test_assess_compliance_all_pass(self):
        """Test assessment when all controls pass."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {
                    "DetectorId": "test-detector",
                    "Status": "ENABLED",
                    "DataSources": {"S3Logs": {"Status": "ENABLED"}},
                }
            ],
            "Findings": [],
        }
        results = mapper.assess_guardduty_compliance(guardduty_data)
        assert results["SI-4"] == "PASS"
        assert results["IR-4"] == "PASS"
        assert results["IR-5"] == "PASS"
        assert results["SI-3"] == "PASS"
        assert results["RA-5"] == "PASS"

    def test_assess_compliance_non_nist_framework(self):
        """Test assessment with non-NIST framework returns empty results."""
        mapper = GuardDutyControlMapper(framework="ISO27001")
        guardduty_data = {"Detectors": []}
        results = mapper.assess_guardduty_compliance(guardduty_data)
        assert results == {}


class TestAssessSI4:
    """Test _assess_si4 (System Monitoring) compliance."""

    def test_si4_pass_detectors_enabled(self):
        """Test SI-4 passes when detectors are enabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Detectors": [{"DetectorId": "test-detector", "Status": "ENABLED"}]}
        result = mapper._assess_si4(guardduty_data)
        assert result == "PASS"

    def test_si4_pass_multiple_detectors_enabled(self):
        """Test SI-4 passes when multiple detectors are enabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {"DetectorId": "detector1", "Status": "ENABLED"},
                {"DetectorId": "detector2", "Status": "ENABLED"},
            ]
        }
        result = mapper._assess_si4(guardduty_data)
        assert result == "PASS"

    def test_si4_fail_no_detectors(self):
        """Test SI-4 fails when no detectors configured."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Detectors": []}
        result = mapper._assess_si4(guardduty_data)
        assert result == "FAIL"

    def test_si4_fail_detector_disabled(self):
        """Test SI-4 fails when detector is disabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Detectors": [{"DetectorId": "test-detector", "Status": "DISABLED"}]}
        result = mapper._assess_si4(guardduty_data)
        assert result == "FAIL"

    def test_si4_fail_mixed_detector_status(self):
        """Test SI-4 fails when some detectors are disabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {"DetectorId": "detector1", "Status": "ENABLED"},
                {"DetectorId": "detector2", "Status": "DISABLED"},
            ]
        }
        result = mapper._assess_si4(guardduty_data)
        assert result == "FAIL"


class TestAssessIR4:
    """Test _assess_ir4 (Incident Handling) compliance."""

    def test_ir4_pass_no_high_severity_findings(self):
        """Test IR-4 passes when no high severity findings."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Findings": [
                {"Id": "finding1", "Severity": 3.5},
                {"Id": "finding2", "Severity": 5.0},
            ]
        }
        result = mapper._assess_ir4(guardduty_data)
        assert result == "PASS"

    def test_ir4_pass_empty_findings(self):
        """Test IR-4 passes when no findings."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Findings": []}
        result = mapper._assess_ir4(guardduty_data)
        assert result == "PASS"

    def test_ir4_fail_high_severity_findings(self):
        """Test IR-4 fails when high severity findings present."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Findings": [{"Id": "finding1", "Severity": 7.5}]}
        result = mapper._assess_ir4(guardduty_data)
        assert result == "FAIL"

    def test_ir4_fail_critical_severity_findings(self):
        """Test IR-4 fails when critical severity findings present."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Findings": [{"Id": "finding1", "Severity": 9.5}]}
        result = mapper._assess_ir4(guardduty_data)
        assert result == "FAIL"

    def test_ir4_fail_multiple_high_critical_findings(self):
        """Test IR-4 fails with multiple high/critical findings."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Findings": [
                {"Id": "finding1", "Severity": 7.5},
                {"Id": "finding2", "Severity": 9.0},
                {"Id": "finding3", "Severity": 3.0},
            ]
        }
        result = mapper._assess_ir4(guardduty_data)
        assert result == "FAIL"


class TestAssessIR5:
    """Test _assess_ir5 (Incident Monitoring) compliance."""

    def test_ir5_pass_findings_tracked(self):
        """Test IR-5 passes when findings are tracked."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Findings": [{"Id": "finding1"}, {"Id": "finding2"}]}
        result = mapper._assess_ir5(guardduty_data)
        assert result == "PASS"

    def test_ir5_pass_no_findings(self):
        """Test IR-5 passes when no findings (acceptable state)."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Findings": []}
        result = mapper._assess_ir5(guardduty_data)
        assert result == "PASS"


class TestAssessSI3:
    """Test _assess_si3 (Malicious Code Protection) compliance."""

    def test_si3_pass_detectors_enabled_no_malware(self):
        """Test SI-3 passes when detectors enabled and no malware findings."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [{"DetectorId": "test-detector", "Status": "ENABLED"}],
            "Findings": [{"Type": "UnauthorizedAccess:EC2/SSHBruteForce"}],
        }
        result = mapper._assess_si3(guardduty_data)
        assert result == "PASS"

    def test_si3_pass_detectors_enabled_with_malware_findings(self):
        """Test SI-3 passes when detectors enabled (even with malware findings - detection working)."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [{"DetectorId": "test-detector", "Status": "ENABLED"}],
            "Findings": [
                {"Type": "Trojan:EC2/PhishingDomainRequest.Reputation"},
                {"Type": "CryptoCurrency:EC2/BitcoinTool.B"},
            ],
        }
        result = mapper._assess_si3(guardduty_data)
        assert result == "PASS"

    def test_si3_fail_no_detectors(self):
        """Test SI-3 fails when no detectors configured."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Detectors": [], "Findings": []}
        result = mapper._assess_si3(guardduty_data)
        assert result == "FAIL"

    def test_si3_fail_all_detectors_disabled(self):
        """Test SI-3 fails when all detectors are disabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {"DetectorId": "detector1", "Status": "DISABLED"},
                {"DetectorId": "detector2", "Status": "DISABLED"},
            ],
            "Findings": [],
        }
        result = mapper._assess_si3(guardduty_data)
        assert result == "FAIL"


class TestAssessRA5:
    """Test _assess_ra5 (Vulnerability Monitoring) compliance."""

    def test_ra5_pass_threat_intel_enabled(self):
        """Test RA-5 passes when threat intelligence enabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {
                    "DetectorId": "test-detector",
                    "DataSources": {"S3Logs": {"Status": "ENABLED"}},
                }
            ]
        }
        result = mapper._assess_ra5(guardduty_data)
        assert result == "PASS"

    def test_ra5_fail_threat_intel_disabled(self):
        """Test RA-5 fails when threat intelligence not enabled."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {
            "Detectors": [
                {
                    "DetectorId": "test-detector",
                    "DataSources": {"S3Logs": {"Status": "DISABLED"}},
                }
            ]
        }
        result = mapper._assess_ra5(guardduty_data)
        assert result == "FAIL"

    def test_ra5_fail_no_data_sources(self):
        """Test RA-5 fails when no data sources configured."""
        mapper = GuardDutyControlMapper()
        guardduty_data = {"Detectors": [{"DetectorId": "test-detector"}]}
        result = mapper._assess_ra5(guardduty_data)
        assert result == "FAIL"


class TestGetSeverityLevel:
    """Test _get_severity_level method."""

    def test_low_severity(self):
        """Test mapping low severity scores."""
        mapper = GuardDutyControlMapper()
        assert mapper._get_severity_level(0.1) == "LOW"
        assert mapper._get_severity_level(2.0) == "LOW"
        assert mapper._get_severity_level(3.9) == "LOW"

    def test_medium_severity(self):
        """Test mapping medium severity scores."""
        mapper = GuardDutyControlMapper()
        assert mapper._get_severity_level(4.0) == "MEDIUM"
        assert mapper._get_severity_level(5.5) == "MEDIUM"
        assert mapper._get_severity_level(6.9) == "MEDIUM"

    def test_high_severity(self):
        """Test mapping high severity scores."""
        mapper = GuardDutyControlMapper()
        assert mapper._get_severity_level(7.0) == "HIGH"
        assert mapper._get_severity_level(8.0) == "HIGH"
        assert mapper._get_severity_level(8.9) == "HIGH"

    def test_critical_severity(self):
        """Test mapping critical severity scores."""
        mapper = GuardDutyControlMapper()
        assert mapper._get_severity_level(9.0) == "CRITICAL"
        assert mapper._get_severity_level(9.5) == "CRITICAL"
        assert mapper._get_severity_level(10.0) == "CRITICAL"

    def test_out_of_range_severity(self):
        """Test severity score outside expected range."""
        mapper = GuardDutyControlMapper()
        assert mapper._get_severity_level(0.0) == "LOW"
        assert mapper._get_severity_level(11.0) == "LOW"
        assert mapper._get_severity_level(-1.0) == "LOW"


class TestIsMalwareFinding:
    """Test _is_malware_finding method."""

    def test_trojan_finding(self):
        """Test detection of Trojan findings."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "Trojan:EC2/PhishingDomainRequest.Reputation"}
        assert mapper._is_malware_finding(finding) is True

    def test_backdoor_finding(self):
        """Test detection of Backdoor findings."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "Backdoor:EC2/C&CActivity.B"}
        assert mapper._is_malware_finding(finding) is True

    def test_cryptocurrency_finding(self):
        """Test detection of CryptoCurrency findings."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "CryptoCurrency:EC2/BitcoinTool.B"}
        assert mapper._is_malware_finding(finding) is True

    def test_malware_finding(self):
        """Test detection of Malware findings."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "Malware:EC2/MaliciousFile"}
        assert mapper._is_malware_finding(finding) is True

    def test_bitcoin_finding(self):
        """Test detection of Bitcoin findings."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "CryptoCurrency:EC2/BitcoinTool.B!DNS"}
        assert mapper._is_malware_finding(finding) is True

    def test_non_malware_finding(self):
        """Test non-malware finding returns False."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": "UnauthorizedAccess:EC2/SSHBruteForce"}
        assert mapper._is_malware_finding(finding) is False

    def test_empty_type(self):
        """Test finding with empty type."""
        mapper = GuardDutyControlMapper()
        finding = {"Type": ""}
        assert mapper._is_malware_finding(finding) is False


class TestHasCVEReference:
    """Test has_cve_reference method."""

    def test_cve_in_description(self):
        """Test CVE detection in description."""
        mapper = GuardDutyControlMapper()
        finding = {"Description": "This vulnerability is related to CVE-2023-12345"}
        assert mapper.has_cve_reference(finding) is True

    def test_cve_in_title(self):
        """Test CVE detection in title."""
        mapper = GuardDutyControlMapper()
        finding = {"Title": "Exploit for CVE-2024-56789 detected"}
        assert mapper.has_cve_reference(finding) is True

    def test_cve_in_additional_info(self):
        """Test CVE detection in additional info."""
        mapper = GuardDutyControlMapper()
        finding = {"Service": {"AdditionalInfo": {"vulnerability": "CVE-2023-99999"}}}
        assert mapper.has_cve_reference(finding) is True

    def test_no_cve_reference(self):
        """Test finding without CVE reference."""
        mapper = GuardDutyControlMapper()
        finding = {
            "Description": "Unauthorized access detected",
            "Title": "Security Alert",
        }
        assert mapper.has_cve_reference(finding) is False

    def test_empty_finding(self):
        """Test empty finding dictionary."""
        mapper = GuardDutyControlMapper()
        finding = {}
        assert mapper.has_cve_reference(finding) is False


class TestExtractCVEsFromFinding:
    """Test extract_cves_from_finding method."""

    def test_extract_single_cve(self):
        """Test extracting single CVE."""
        mapper = GuardDutyControlMapper()
        finding = {"Description": "This vulnerability is CVE-2023-12345"}
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 1
        assert "CVE-2023-12345" in cves

    def test_extract_multiple_cves(self):
        """Test extracting multiple CVEs."""
        mapper = GuardDutyControlMapper()
        finding = {
            "Description": "Related to CVE-2023-12345 and CVE-2024-56789",
            "Title": "Also see CVE-2023-99999",
        }
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 3
        assert "CVE-2023-12345" in cves
        assert "CVE-2024-56789" in cves
        assert "CVE-2023-99999" in cves

    def test_extract_cves_case_insensitive(self):
        """Test CVE extraction is case-insensitive and normalized."""
        mapper = GuardDutyControlMapper()
        finding = {"Description": "cve-2023-12345 and CVE-2024-56789"}
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 2
        assert all(cve.startswith("CVE-") for cve in cves)

    def test_extract_cves_deduplicated(self):
        """Test duplicate CVEs are removed."""
        mapper = GuardDutyControlMapper()
        finding = {
            "Description": "CVE-2023-12345 detected",
            "Title": "Alert for CVE-2023-12345",
        }
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 1
        assert "CVE-2023-12345" in cves

    def test_extract_cves_various_formats(self):
        """Test extracting CVEs with different number lengths."""
        mapper = GuardDutyControlMapper()
        finding = {"Description": "CVE-2023-1234 (4 digits), CVE-2023-12345 (5 digits), CVE-2023-1234567 (7 digits)"}
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 3
        assert "CVE-2023-1234" in cves
        assert "CVE-2023-12345" in cves
        assert "CVE-2023-1234567" in cves

    def test_no_cves_found(self):
        """Test finding with no CVEs."""
        mapper = GuardDutyControlMapper()
        finding = {"Description": "General security alert"}
        cves = mapper.extract_cves_from_finding(finding)
        assert len(cves) == 0


class TestGuardDutyControlMappings:
    """Test GUARDDUTY_CONTROL_MAPPINGS structure."""

    def test_mappings_exist(self):
        """Test that mappings dictionary exists and has content."""
        assert len(GUARDDUTY_CONTROL_MAPPINGS) > 0

    def test_si4_mapping_structure(self):
        """Test SI-4 mapping structure."""
        assert "SI-4" in GUARDDUTY_CONTROL_MAPPINGS
        si4 = GUARDDUTY_CONTROL_MAPPINGS["SI-4"]
        assert "name" in si4
        assert "description" in si4
        assert "checks" in si4
        assert "detector_enabled" in si4["checks"]
        assert "findings_processed" in si4["checks"]

    def test_ir4_mapping_structure(self):
        """Test IR-4 mapping structure."""
        assert "IR-4" in GUARDDUTY_CONTROL_MAPPINGS
        ir4 = GUARDDUTY_CONTROL_MAPPINGS["IR-4"]
        assert len(ir4["checks"]) >= 2
        assert "high_severity_findings" in ir4["checks"]
        assert "incident_response" in ir4["checks"]

    def test_all_controls_have_required_fields(self):
        """Test all control mappings have required fields."""
        for control_id, control_data in GUARDDUTY_CONTROL_MAPPINGS.items():
            assert "name" in control_data
            assert "description" in control_data
            assert "checks" in control_data
            assert isinstance(control_data["checks"], dict)
            for check_name, check_data in control_data["checks"].items():
                assert "weight" in check_data
                assert "pass_criteria" in check_data
                assert "fail_criteria" in check_data


class TestSeverityMapping:
    """Test SEVERITY_MAPPING constant."""

    def test_severity_mapping_exists(self):
        """Test severity mapping dictionary exists."""
        assert len(SEVERITY_MAPPING) == 4

    def test_severity_mapping_structure(self):
        """Test severity mapping has correct structure."""
        assert "LOW" in SEVERITY_MAPPING
        assert "MEDIUM" in SEVERITY_MAPPING
        assert "HIGH" in SEVERITY_MAPPING
        assert "CRITICAL" in SEVERITY_MAPPING

    def test_severity_ranges_valid(self):
        """Test severity ranges are valid tuples."""
        for level, (min_val, max_val) in SEVERITY_MAPPING.items():
            assert isinstance(min_val, float)
            assert isinstance(max_val, float)
            assert min_val < max_val


class TestCVERelatedFindingTypes:
    """Test CVE_RELATED_FINDING_TYPES constant."""

    def test_cve_finding_types_exist(self):
        """Test CVE-related finding types list exists."""
        assert len(CVE_RELATED_FINDING_TYPES) > 0

    def test_cve_finding_types_structure(self):
        """Test CVE-related finding types are strings."""
        for finding_type in CVE_RELATED_FINDING_TYPES:
            assert isinstance(finding_type, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
