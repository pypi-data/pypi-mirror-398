import os
import zipfile
from unittest.mock import patch, MagicMock

import pytest

from regscale.core.utils.date import date_str, days_from_today
from regscale.integrations.commercial.stigv2.ckl_parser import (
    parse_checklist,
    Checklist,
    Asset,
    STIG,
    STIGInfo,
    Vuln,
    get_components_from_checklist,
    get_all_components_from_checklists,
)
from regscale.integrations.commercial.stigv2.stig_integration import StigIntegration

sample_asset = Asset(
    role="None",
    asset_type="Computing",
    host_name="FacierComplainingnessDisulphuret",
    host_ip="",
)


class TestStigIntegration:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, test_data_dir, test_tmp_dir):
        # Setup
        self.chaos_stig_dir = test_tmp_dir / "stig" / "ChaosStigs"
        os.makedirs(self.chaos_stig_dir, exist_ok=True)
        chaos_stig_zip_file = test_data_dir / "stig" / "ChaosStigs.zip"
        with zipfile.ZipFile(chaos_stig_zip_file, "r") as zip_ref:
            for zip_info in zip_ref.infolist():
                if not zip_info.is_dir():
                    zip_info.filename = os.path.basename(zip_info.filename)
                    zip_ref.extract(zip_info, self.chaos_stig_dir)

        self.cisco_stig_file = self.chaos_stig_dir / (
            "Perimeter Router Security Technical Implementation "
            "Guide Cisco V8R32 - FacierComplainingnessDisulphuret.ckl"
        )

    def test_parse_checklist(self):
        checklists = []

        for file in os.listdir(self.chaos_stig_dir):
            if file.endswith(".ckl"):
                checklists.append(parse_checklist(self.chaos_stig_dir / file))
        assert len(checklists) == 1500, "There should 1500 checklists processed."

        cisco_checklist = parse_checklist(self.cisco_stig_file)
        assert len(cisco_checklist.stigs[0].vulns) == 145, "There should be 145 fields in the vuln."
        cisco_checklist.stigs[0].vulns = [cisco_checklist.stigs[0].vulns[0]]
        assert cisco_checklist == Checklist(
            assets=[
                Asset(
                    role="None",
                    asset_type="Computing",
                    host_name="FacierComplainingnessDisulphuret",
                    host_ip="101.116.163.60",
                    host_mac="96:47:ba:29:58:bd",
                    host_fqdn="faciercomplainingnessdisulphuret.cosmos.navy.mil",
                    tech_area=None,
                    target_key="510",
                    web_or_database=False,
                    web_db_site=None,
                    web_db_instance=None,
                )
            ],
            stigs=[
                STIG(
                    baseline="Perimeter Router Security Technical Implementation Guide Cisco V8R32",
                    stig_info=STIGInfo(
                        version="8",
                        classification="UNCLASSIFIED",
                        customname=None,
                        stigid="Network_-_Perimeter_Router_Cisco",
                        description="Perimeter Router Security Technical Implementation Guide – Cisco",
                        filename="U_Network_Perimeter_Router_Cisco_STIG_V8R32_Manual-xccdf.xml",
                        releaseinfo="Release: 32 Benchmark Date: 25 Jan 2019",
                        title="Perimeter Router Security Technical Implementation Guide Cisco",
                        uuid="459468bf-6c90-49ff-8389-28df0ff0e556",
                        notice="terms-of-use",
                        source=None,
                    ),
                    vulns=[
                        Vuln(
                            vuln_num="V-3000",
                            severity="low",
                            group_title="Interface ACL deny statements are not logged.",
                            rule_id="SV-15474r3_rule",
                            rule_ver="NET1020",
                            rule_title="The network device must log all access control lists (ACL) deny statements.",
                            check_content="Review the network device interface ACLs to verify all deny statements are "
                            "logged.\n\nCisco IOS example:\ninterface FastEthernet 0/0 \ndescription external"
                            " interface peering with ISP or non-DoD network\nip address 199.36.92.1 255.255"
                            ".255.252\nip access-group 100 in\n…\naccess-list 100 deny icmp any any fragments"
                            " log\naccess-list 100 deny ip 169.254.0.0 0.0.255.255 any log\naccess-list 100 "
                            "deny ip 10.0.0.0 0.255.255.255 any log\naccess-list 100 deny ip 172.16.0.0 "
                            "0.15.255.255 any log\naccess-list 100 deny ip 192.168.0.0 0.0.255.255 any "
                            "log\naccess-list 100 permit icmp any host 199.36.92.1 echo-reply\naccess-list "
                            "100 permit icmp any host 199.36.90.10 echo-reply\naccess-list 100 deny icmp "
                            "any any log\naccess-list 100 deny ip any any log",
                            fix_text="Configure interface ACLs to log all deny statements.",
                            check_content_ref="M",
                            weight="10.0",
                            stigref="Perimeter Router Security Technical Implementation Guide Cisco :: Version 8, Release:"
                            " 32 Benchmark Date: 25 Jan 2019",
                            targetkey="510",
                            stig_uuid="459468bf-6c90-49ff-8389-28df0ff0e556",
                            vuln_discuss="Auditing and logging are key components of any security architecture.  It is "
                            "essential for security personnel to know what is being done, attempted to be "
                            "done, and by whom in order to compile an accurate risk assessment.  Auditing "
                            "the actions on network devices provides a means to recreate an attack, or "
                            "identify a configuration mistake on the device.",
                            ia_controls="ECAT-1, ECAT-2, ECSC-1",
                            class_=None,
                            cci_ref=[],
                            false_positives=None,
                            false_negatives=None,
                            documentable="false",
                            mitigations=None,
                            potential_impact=None,
                            third_party_tools=None,
                            mitigation_control=None,
                            responsibility="Information Assurance Officer",
                            security_override_guidance=None,
                            legacy_id=None,
                            status="NotAFinding",
                            finding_details="The network device does log all access control lists (ACL) deny statements.",
                            comments="The network device does log all access control lists (ACL) deny statements.",
                            severity_override="",
                            severity_justification="",
                        )
                    ],
                )
            ],
        )

    @pytest.mark.parametrize(
        "checklist_titles, expected_components",
        [
            (
                Checklist(
                    assets=[sample_asset],
                    stigs=[
                        STIG(
                            baseline="Perimeter Router Security Technical Implementation Guide Cisco",
                            stig_info=STIGInfo(
                                title="Perimeter Router Security Technical Implementation Guide Cisco",
                                version="8",
                                classification="UNCLASSIFIED",
                                stigid="Network_-_Perimeter_Router_Cisco",
                                filename="U_Network_Perimeter_Router_Cisco_STIG_V8R32_Manual-xccdf.xml",
                                releaseinfo="Release: 32 Benchmark Date: 25 Jan 2019",
                                uuid="459468bf-6c90-49ff-8389-28df0ff0e556",
                                notice="terms-of-use",
                            ),
                        )
                    ],
                ),
                [
                    {
                        "Network_-_Perimeter_Router_Cisco": "Perimeter Router Security Technical Implementation Guide Cisco"
                    }
                ],
            ),
            (
                Checklist(
                    assets=[sample_asset],
                    stigs=[
                        STIG(
                            baseline="Data Center Security Technical Implementation Guide",
                            stig_info=STIGInfo(
                                title="Data Center Security Technical Implementation Guide",
                                version="2",
                                classification="UNCLASSIFIED",
                                stigid="Data_Center_Cisco",
                                filename="U_Data_Center_Cisco_STIG_V2R1_Manual-xccdf.xml",
                                releaseinfo="Release: 1 Benchmark Date: 15 Feb 2021",
                                uuid="a1b2c3d4-5678-90ab-cdef-1234567890ab",
                                notice="terms-of-use",
                            ),
                        ),
                        STIG(
                            baseline="Wireless Network (STIG)",
                            stig_info=STIGInfo(
                                title="Wireless Network (STIG)",
                                version="3",
                                classification="UNCLASSIFIED",
                                stigid="Wireless_Network",
                                filename="U_Wireless_Network_STIG_V3R1_Manual-xccdf.xml",
                                releaseinfo="Release: 1 Benchmark Date: 05 May 2022",
                                uuid="09876543-21ab-cdef-ghij-klmnopqrstuv",
                                notice="terms-of-use",
                            ),
                        ),
                    ],
                ),
                [
                    {"Data_Center_Cisco": "Data Center Security Technical Implementation Guide"},
                    {"Wireless_Network": "Wireless Network (STIG)"},
                ],
            ),
            (
                Checklist(
                    assets=[sample_asset],
                    stigs=[
                        STIG(
                            baseline="Non-STIG Title Without Expected Phrases",
                            stig_info=STIGInfo(
                                title="Non-STIG Title Without Expected Phrases",
                                version="N/A",
                                classification="UNCLASSIFIED",
                                stigid="Non-STIG",
                                filename="N/A",
                                releaseinfo="N/A",
                                uuid="N/A",
                                notice="N/A",
                            ),
                        )
                    ],
                ),
                [{"Non-STIG": "Non-STIG Title Without Expected Phrases"}],
            ),
        ],
    )
    def test_get_components_from_checklist(self, checklist_titles, expected_components):
        assert list(get_components_from_checklist(checklist_titles)) == expected_components

    @pytest.mark.parametrize(
        "checklists, expected_unique_components",
        [
            (
                [
                    Checklist(
                        asset=sample_asset,
                        stigs=[
                            STIG(
                                baseline="Perimeter Router Security Technical Implementation Guide Cisco",
                                stig_info=STIGInfo(
                                    title="Perimeter Router Security Technical Implementation Guide Cisco",
                                    version="8",
                                    classification="UNCLASSIFIED",
                                    stigid="Network_-_Perimeter_Router_Cisco",
                                    filename="U_Network_Perimeter_Router_Cisco_STIG_V8R32_Manual-xccdf.xml",
                                    releaseinfo="Release: 32 Benchmark Date: 25 Jan 2019",
                                    uuid="459468bf-6c90-49ff-8389-28df0ff0e556",
                                    notice="terms-of-use",
                                ),
                            )
                        ],
                    ),
                    Checklist(
                        asset=sample_asset,
                        stigs=[
                            STIG(
                                baseline="Perimeter Router Security Technical Implementation Guide Cisco",
                                stig_info=STIGInfo(
                                    title="Perimeter Router Security Technical Implementation Guide Cisco",
                                    version="8",
                                    classification="UNCLASSIFIED",
                                    stigid="Network_-_Perimeter_Router_Cisco",
                                    filename="U_Network_Perimeter_Router_Cisco_STIG_V8R32_Manual-xccdf.xml",
                                    releaseinfo="Release: 32 Benchmark Date: 25 Jan 2019",
                                    uuid="459468bf-6c90-49ff-8389-28df0ff0e556",
                                    notice="terms-of-use",
                                ),
                            )
                        ],
                    ),
                ],
                {"Network_-_Perimeter_Router_Cisco": "Perimeter Router Security Technical Implementation Guide Cisco"},
            ),
            (
                [
                    Checklist(
                        asset=sample_asset,
                        stigs=[
                            STIG(
                                baseline="Data Center Security Technical Implementation Guide",
                                stig_info=STIGInfo(
                                    title="Data Center Security Technical Implementation Guide",
                                    version="2",
                                    classification="UNCLASSIFIED",
                                    stigid="Data_Center_Cisco",
                                    filename="U_Data_Center_Cisco_STIG_V2R1_Manual-xccdf.xml",
                                    releaseinfo="Release: 1 Benchmark Date: 15 Feb 2021",
                                    uuid="a1b2c3d4-5678-90ab-cdef-1234567890ab",
                                    notice="terms-of-use",
                                ),
                            )
                        ],
                    ),
                    Checklist(
                        asset=sample_asset,
                        stigs=[
                            STIG(
                                baseline="Wireless Network (STIG)",
                                stig_info=STIGInfo(
                                    title="Wireless Network (STIG)",
                                    version="3",
                                    classification="UNCLASSIFIED",
                                    stigid="Wireless_Network",
                                    filename="U_Wireless_Network_STIG_V3R1_Manual-xccdf.xml",
                                    releaseinfo="Release: 1 Benchmark Date: 05 May 2022",
                                    uuid="09876543-21ab-cdef-ghij-klmnopqrstuv",
                                    notice="terms-of-use",
                                ),
                            )
                        ],
                    ),
                    Checklist(
                        asset=sample_asset,
                        stigs=[
                            STIG(
                                baseline="Data Center Security Technical Implementation Guide",
                                stig_info=STIGInfo(
                                    title="Wireless Network (STIG)",
                                    version="3",
                                    classification="UNCLASSIFIED",
                                    stigid="Wireless_Network",
                                    filename="U_Wireless_Network_STIG_V3R1_Manual-xccdf.xml",
                                    releaseinfo="Release: 1 Benchmark Date: 05 May 2022",
                                    uuid="09876543-21ab-cdef-ghij-klmnopqrstuv",
                                    notice="terms-of-use",
                                ),
                            )
                        ],
                    ),
                ],
                {
                    "Data_Center_Cisco": "Data Center Security Technical Implementation Guide",
                    "Wireless_Network": "Wireless Network (STIG)",
                },
            ),
        ],
    )
    def test_get_all_components_from_checklists(self, checklists, expected_unique_components):
        assert get_all_components_from_checklists(checklists) == expected_unique_components

    @patch("regscale.integrations.commercial.stigv2.stig_integration.find_stig_files")
    def test_fetch_findings(self, mock_find_stig_files, test_tmp_dir):
        mock_find_stig_files.return_value = [self.cisco_stig_file]

        stig_integration = StigIntegration(plan_id=1)
        findings = list(stig_integration.fetch_findings(self.chaos_stig_dir))

        assert len(findings) == 145
        mock_find_stig_files.assert_called_once_with(self.chaos_stig_dir)

    def test_process_vulnerabilities(self):
        stig_integration = StigIntegration(plan_id=1)
        mock_checklist = MagicMock()
        mock_checklist.assets = [MagicMock(host_fqdn="example.com")]
        mock_vuln = MagicMock()
        mock_vuln.cci_ref = []  # Set cci_ref to an empty list to ensure a finding with the default CCI is created
        mock_stig = MagicMock()

        findings = list(stig_integration.process_vulnerabilities(mock_checklist, mock_vuln, mock_stig))

        assert len(findings) == 1, "Should yield one finding per vulnerability."
        assert findings[0].asset_identifier == "example.com", "Asset identifier should match the host_fqdn."

    def test_create_integration_finding(self):
        stig_integration = StigIntegration(plan_id=1)
        mock_vuln = MagicMock(
            rule_title="Test Rule",
            group_title="Test Group",
            severity="low",
            check_content="Check Content",
            vuln_discuss="Vulnerability Discussion",
            fix_text="Fix Text",
            status="NotAFinding",
            vuln_num="V-12345",
            cci_ref="CCI-123",
            rule_id="Rule-123",
            rule_ver="999",
            comments="Test Comment",
            stigref="STIG Reference",
        )

        mock_stig = MagicMock(
            stig_info=STIGInfo(
                releaseinfo="Release Info",
                classification="UNCLASSIFIED",
                title="Test Title",
                stigid="Test STIG",
                version="1",
                filename="Test File",
                uuid="Test UUID",
                notice="Test Notice",
            )
        )

        finding = next(stig_integration.create_integration_finding("example.com", mock_vuln, mock_stig))

        assert finding.title == "Test Rule 999 Release Info V-12345", "Title should match the rule title."
        assert finding.severity == stig_integration.finding_severity_map["low"], "Severity should be mapped correctly."
        assert (
            finding.status == stig_integration.finding_status_map["NotAFinding"]
        ), "Status should be mapped correctly."
        assert finding.due_date == date_str(days_from_today(364)), "Due date should be 394 days from today."
