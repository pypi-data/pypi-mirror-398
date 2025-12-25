#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Finding Dataclass Module.

This module contains the IntegrationFinding dataclass used for representing
findings from various scanner integrations in the RegScale CLI.
"""
from __future__ import annotations

import dataclasses
import logging
from dataclasses import field
from typing import Any, Dict, List, Optional, Union

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.models import regscale_models

logger = logging.getLogger("regscale")


@dataclasses.dataclass
class IntegrationFinding:
    """
    Dataclass for integration findings.

    :param list[str] control_labels: A list of control labels associated with the finding.
    :param str title: The title of the finding.
    :param str category: The category of the finding.
    :param regscale_models.IssueSeverity severity: The severity of the finding, based on regscale_models.IssueSeverity.
    :param str description: A description of the finding.
    :param regscale_models.ControlTestResultStatus status: The status of the finding, based on
    regscale_models.ControlTestResultStatus.
    :param str priority: The priority of the finding, defaults to "Medium".
    :param str issue_type: The type of issue, defaults to "Risk".
    :param str issue_title: The title of the issue, defaults to an empty string.
    :param str date_created: The creation date of the finding, defaults to the current datetime.
    :param str due_date: The due date of the finding, defaults to 60 days from the current datetime.
    :param str date_last_updated: The last update date of the finding, defaults to the current datetime.
    :param str external_id: An external identifier for the finding, defaults to an empty string.
    :param str gaps: A description of any gaps identified, defaults to an empty string.
    :param str observations: Observations related to the finding, defaults to an empty string.
    :param str evidence: Evidence supporting the finding, defaults to an empty string.
    :param str identified_risk: The risk identified by the finding, defaults to an empty string.
    :param str impact: The impact of the finding, defaults to an empty string.
    :param str recommendation_for_mitigation: Recommendations for mitigating the finding, defaults to an empty string.
    :param str asset_identifier: The identifier of the asset associated with the finding, defaults to an empty string.
    :param str issue_asset_identifier_value: This is the value of all the assets affected by the issue, defaults to an
    empty string.
    :param Optional[str] cci_ref: The Common Configuration Enumeration reference for the finding, defaults to None.
    :param str rule_id: The rule ID of the finding, defaults to an empty string.
    :param str rule_version: The version of the rule associated with the finding, defaults to an empty string.
    :param str results: The results of the finding, defaults to an empty string.
    :param Optional[str] comments: Additional comments related to the finding, defaults to None.
    :param Optional[str] source_report: The source report of the finding, defaults to None.
    :param Optional[str] point_of_contact: The point of contact for the finding, used to create property defaults to None.
    :param Optional[str] milestone_changes: Milestone Changes for the finding, defaults to None.
    :param Optional[str] adjusted_risk_rating: The adjusted risk rating of the finding, defaults to None.
    :param Optional[str] risk_adjustment: The risk adjustment of the finding, (Should be Yes, No, Pending), defaults to No.
    :param Optional[str] operational_requirements: The operational requirements of the finding, defaults to None.
    :param Optional[str] deviation_rationale: The rationale for any deviations from the finding, defaults to None.
    :param str baseline: The baseline of the finding, defaults to an empty string.
    :param str poam_comments: Comments related to the Plan of Action and Milestones (POAM) for the finding, defaults to
    :param Optional[int] vulnerability_id: The ID of the vulnerability associated with the finding, defaults to None.
    an empty string.
    :param Optional[str] basis_for_adjustment: The basis for adjusting the finding, defaults to None.
    :param Optional[str] vulnerability_number: STIG vulnerability number
    :param Optional[str] vulnerability_type: The type of vulnerability, defaults to None.
    :param Optional[str] plugin_id: The ID of the plugin associated with the finding, defaults to None.
    :param Optional[str] plugin_name: The name of the plugin associated with the finding, defaults to None.
    :param Optional[str] dns: The DNS name associated with the finding, defaults to None.
    :param int severity_int: The severity integer of the finding, defaults to 0.
    :param Optional[str] cve: The CVE of the finding, defaults to None.
    :param Optional[float] cvss_v3_score: The CVSS v3 score of the finding, defaults to None.
    :param Optional[float] cvss_v2_score: The CVSS v2 score of the finding, defaults to None.
    :param Optional[str] cvss_score: The CVSS score of the finding, defaults to None.
    :param Optional[str] cvss_v3_base_score: The CVSS v3 base score of the finding, defaults to None.
    :param Optional[str] ip_address: The IP address associated with the finding, defaults to None.
    :param Optional[str] first_seen: The first seen date of the finding, defaults to the current datetime.
    :param Optional[str] last_seen: The last seen date of the finding, defaults to the current datetime.
    :param Optional[str] oval_def: The OVAL definition of the finding, defaults to None.
    :param Optional[str] scan_date: The scan date of the finding, defaults to the current datetime.
    :param Optional[str] rule_id_full: The full rule ID of the finding, defaults to an empty string.
    :param Optional[str] group_id: The group ID of the finding, defaults to an empty string.
    :param Optional[str] vulnerable_asset: The vulnerable asset of the finding, defaults to None.
    :param Optional[str] remediation: The remediation of the finding, defaults to None.
    :param Optional[str] source_rule_id: The source rule ID of the finding, defaults to None.
    :param Optional[str] poam_id: The POAM ID of the finding, defaults to None.
    :param Optional[str] cvss_v3_vector: The CVSS v3 vector of the finding, defaults to None.
    :param Optional[str] cvss_v2_vector: The CVSS v2 vector of the finding, defaults to None.
    :param Optional[str] affected_os: The affected OS of the finding, defaults to None.
    :param Optional[str] image_digest: The image digest of the finding, defaults to None.
    :param Optional[str] affected_packages: The affected packages of the finding, defaults to None.
    :param Optional[str] installed_versions: The installed versions of the finding, defaults to None.
    :param Optional[str] fixed_versions: The fixed versions of the finding, defaults to None.
    :param Optional[str] fix_status: The fix status of the finding, defaults to None.
    :param Optional[str] build_version: The build version of the finding, defaults to None.
    """

    control_labels: List[str]
    title: str
    category: str
    severity: regscale_models.IssueSeverity
    description: str
    status: Union[regscale_models.ControlTestResultStatus, regscale_models.ChecklistStatus, regscale_models.IssueStatus]
    priority: str = "Medium"
    plugin_name: Optional[str] = None  # Moved to optional fields

    # Vulns
    first_seen: str = field(default_factory=get_current_datetime)
    last_seen: str = field(default_factory=get_current_datetime)
    cve: Optional[str] = None
    cvss_v3_score: Optional[float] = None
    cvss_v2_score: Optional[float] = None
    ip_address: Optional[str] = None
    plugin_id: Optional[str] = None
    plugin_text: Optional[str] = None
    dns: Optional[str] = None
    severity_int: int = 0
    security_check: Optional[str] = None
    cvss_v3_vector: Optional[str] = None
    cvss_v2_vector: Optional[str] = None
    affected_os: Optional[str] = None
    package_path: Optional[str] = None
    image_digest: Optional[str] = None
    affected_packages: Optional[str] = None
    installed_versions: Optional[str] = None
    fixed_versions: Optional[str] = None
    fix_status: Optional[str] = None
    build_version: Optional[str] = None

    # Issues
    issue_title: str = ""
    issue_type: str = "Risk"
    date_created: str = field(default_factory=get_current_datetime)
    date_last_updated: str = field(default_factory=get_current_datetime)
    due_date: str = ""  # dataclasses.field(default_factory=lambda: date_str(days_from_today(60)))
    external_id: str = ""
    gaps: str = ""
    observations: str = ""
    evidence: str = ""
    identified_risk: str = ""
    impact: str = ""
    recommendation_for_mitigation: str = ""
    asset_identifier: str = ""
    issue_asset_identifier_value: Optional[str] = None
    comments: Optional[str] = None
    source_report: Optional[str] = None
    point_of_contact: Optional[str] = None
    milestone_changes: Optional[str] = None
    planned_milestone_changes: Optional[str] = None
    adjusted_risk_rating: Optional[str] = None
    risk_adjustment: str = "No"

    # Compliance fields
    assessment_id: Optional[int] = None
    operational_requirements: Optional[str] = None
    deviation_rationale: Optional[str] = None
    is_cwe: bool = False
    affected_controls: Optional[str] = None
    identification: Optional[str] = "Vulnerability Assessment"

    poam_comments: Optional[str] = None
    vulnerability_id: Optional[int] = None
    _control_implementation_ids: List[int] = field(default_factory=list)

    # Stig
    checklist_status: regscale_models.ChecklistStatus = field(default=regscale_models.ChecklistStatus.NOT_REVIEWED)
    cci_ref: Optional[str] = None
    rule_id: str = ""
    rule_version: str = ""
    results: str = ""
    baseline: str = ""
    vulnerability_number: str = ""
    oval_def: str = ""
    scan_date: str = ""
    rule_id_full: str = ""
    group_id: str = ""

    # Wiz
    vulnerable_asset: Optional[str] = None
    remediation: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_v3_base_score: Optional[float] = None
    source_rule_id: Optional[str] = None
    vulnerability_type: Optional[str] = None

    # CoalFire POAM
    basis_for_adjustment: Optional[str] = None
    poam_id: Optional[str] = None

    # Additional fields from Wiz integration
    vpr_score: Optional[float] = None

    # Extra data field for miscellaneous data
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and adjust types after initialization."""
        # Set default date values if empty
        if not self.first_seen:
            self.first_seen = get_current_datetime()
        if not self.last_seen:
            self.last_seen = get_current_datetime()
        if not self.scan_date:
            self.scan_date = get_current_datetime()

        # Validate the values of the dataclass
        if not self.title:
            self.title = "Unknown Issue"
        if not self.description:
            self.description = "No description provided"

        if self.plugin_name is None:
            self.plugin_name = self.cve or self.title
        if self.plugin_id is None:
            self.plugin_id = self.plugin_name

    def get_issue_status(self) -> regscale_models.IssueStatus:
        """
        Get the issue status based on the finding status.

        :return: The issue status
        :rtype: regscale_models.IssueStatus
        """
        return (
            regscale_models.IssueStatus.Closed
            if (
                self.status == regscale_models.ControlTestResultStatus.PASS
                or self.status == regscale_models.IssueStatus.Closed
            )
            else regscale_models.IssueStatus.Open
        )

    def __eq__(self, other: Any) -> bool:
        """
        Check if the finding is equal to another finding.

        :param Any other: The other finding to compare
        :return: Whether the findings are equal
        :rtype: bool
        """
        if not isinstance(other, IntegrationFinding):
            return NotImplemented
        return (self.title, self.category, self.external_id) == (other.title, other.category, other.external_id)

    def __hash__(self) -> int:
        """
        Get the hash of the finding.

        :return: Hash of the finding
        :rtype: int
        """
        return hash((self.title, self.category, self.external_id))

    def is_valid(self) -> bool:
        """
        Determine if the finding is valid based on the presence of `date_last_updated` and `risk_adjustment`.

        :return: True if the finding is valid, False otherwise.
        :rtype: bool
        """
        # Check if these fields are not empty or None
        if not self.date_last_updated:
            logger.warning("Finding %s is missing date_last_updated, skipping..", self.poam_id)
            return False

        if not self.risk_adjustment:
            logger.warning("Finding %s is missing risk_adjustment, skipping..", self.poam_id)
            return False

        # Additional validation logic can be added here if needed
        # For example, ensure risk_adjustment is one of the allowed values ("Yes", "No", "Pending")
        allowed_risk_adjustments = {"Yes", "No", "Pending"}
        if self.risk_adjustment not in allowed_risk_adjustments:
            logger.warning("Finding %s has a disallowed risk adjustment, skipping..", self.poam_id)
            return False

        return True
