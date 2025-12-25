#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Model for a RegScale Issue"""
import datetime
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from regscale.models import File

from urllib.parse import urljoin

from pathlib import Path
from pydantic import Field, field_serializer, field_validator
from requests import JSONDecodeError
from rich.progress import Progress

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.core.app.logz import create_logger
from regscale.core.app.utils.app_utils import check_file_path, get_current_datetime, reformat_str_date, save_data_to
from regscale.models.regscale_models.regscale_model import RegScaleModel
from regscale.utils.version import RegscaleVersion


# Module-level cache for open issues - avoids Pydantic conflicts
_OPEN_ISSUES_CACHE: Dict[int, Tuple[float, Dict[int, List["OpenIssueDict"]]]] = {}
_CACHE_TTL: float = 300.0  # 5 minutes TTL in seconds


class OpenIssueDict(TypedDict):
    """TypedDict for open issues"""

    id: int
    otherIdentifier: str
    integrationFindingId: str


class IssueSeverity(str, Enum):
    """Issue Severity"""

    NotAssigned = "IV - Not Assigned"
    Low = "III - Low - Other Weakness"
    Moderate = "II - Moderate - Reportable Condition"
    High = "I - High - Significant Deficiency"
    Critical = "0 - Critical - Critical Deficiency"

    def __str__(self) -> str:
        """
        Return the value of the Enum as a string

        :return: The value of the Enum as a string
        :rtype: str
        """
        return self.value


class IssueStatus(str, Enum):
    """Issue Status"""

    Draft = "Draft"
    PendingScreening = "Pending Screening"
    Open = "Open"
    PendingVerification = "Pending Verification"
    Closed = "Closed"
    Cancelled = "Cancelled"
    PendingDecommission = "Pending Decommission"
    SupplyChainProcurementDependency = "Supply Chain/Procurement Dependency"
    VendorDependency = "Vendor Dependency for Fix"
    Delayed = "Delayed"
    ExceptionWaiver = "Exception/Waiver"
    PendingApproval = "Pending Approval"

    def __str__(self) -> str:
        """
        Return the value of the Enum as a string

        :return: The value of the Enum as a string
        :rtype: str
        """
        return self.value


class IssueIdentification(str, Enum):
    """Issue Identification"""

    A123Review = "A-123 Review"
    AssessmentAuditInternal = "Assessment/Audit (Internal)"
    AssessmentAuditExternal = "Assessment/Audit (External)"
    CriticalControlReview = "Critical Control Review"
    FDCCUSGCB = "FDCC/USGCB"
    GAOAudit = "GAO Audit"
    IGAudit = "IG Audit"
    IncidentResponseLessonsLearned = "Incident Response Lessons Learned"
    ITAR = "ITAR"
    PenetrationTest = "Penetration Test"
    RiskAssessment = "Risk Assessment"
    SecurityAuthorization = "Security Authorization"
    SecurityControlAssessment = "Security Control Assessment"
    VulnerabilityAssessment = "Vulnerability Assessment"
    Other = "Other"

    def __str__(self) -> str:
        """
        Return the value of the Enum as a string

        :return: The value of the Enum as a string
        :rtype: str
        """
        return self.value


class Issue(RegScaleModel):
    """Issue Model"""

    _module_slug = "issues"
    _plural_name = "issues"
    _x_api_version = "2"
    _unique_fields = [
        ["integrationFindingId", "vulnerabilityId", "status"],
        ["otherIdentifier", "parentModule", "parentId", "status"],
    ]
    _exclude_graphql_fields = [
        "facility",
        "org",
        "createdBy",
        "lastUpdatedBy",
        "extra_data",
        "tenantsId",
        "issueOwner",
        "controlImplementationIds",
    ]

    title: Optional[str] = ""
    severityLevel: Union[IssueSeverity, str] = IssueSeverity.NotAssigned
    issueOwnerId: Optional[str] = Field(default_factory=RegScaleModel.get_user_id)
    dueDate: Optional[str] = ""
    id: int = 0
    tenantsId: int = 1
    uuid: Optional[str] = None
    dateCreated: Optional[str] = Field(default_factory=get_current_datetime)
    description: Optional[str] = None
    issueOwner: Optional[str] = None
    costEstimate: Optional[int] = None
    levelOfEffort: Optional[int] = None
    identification: Optional[str] = ""  # Has to be an empty string or else it will fail to create
    capStatus: Optional[str] = None
    sourceReport: Optional[str] = None
    status: Optional[Union[IssueStatus, str]] = None
    dateCompleted: Optional[str] = None
    activitiesObserved: Optional[str] = None
    failuresObserved: Optional[str] = None
    requirementsViolated: Optional[str] = None
    safetyImpact: Optional[str] = None
    securityImpact: Optional[str] = None
    qualityImpact: Optional[str] = None
    facility: Optional[str] = None
    facilityId: Optional[int] = None
    org: Optional[str] = None
    orgId: Optional[int] = None
    controlId: Optional[int] = None
    assessmentId: Optional[int] = None
    requirementId: Optional[int] = None
    securityPlanId: Optional[int] = None
    projectId: Optional[int] = None
    supplyChainId: Optional[int] = None
    policyId: Optional[int] = None
    componentId: Optional[int] = None
    incidentId: Optional[int] = None
    jiraId: Optional[str] = None
    serviceNowId: Optional[str] = None
    wizId: Optional[str] = None
    burpId: Optional[str] = None
    defenderId: Optional[str] = None
    defenderAlertId: Optional[str] = None
    defenderCloudId: Optional[str] = None
    salesforceId: Optional[str] = None
    prismaId: Optional[str] = None
    tenableId: Optional[str] = None
    tenableNessusId: Optional[str] = None
    qualysId: Optional[str] = None
    pluginId: Optional[str] = None
    cve: Optional[str] = None
    assetIdentifier: Optional[str] = None
    falsePositive: Optional[str] = None
    operationalRequirement: Optional[str] = None
    autoApproved: Optional[str] = None
    kevList: Optional[str] = None
    dateFirstDetected: Optional[str] = None
    changes: Optional[str] = None
    vendorDependency: Optional[str] = None
    vendorName: Optional[str] = None
    vendorLastUpdate: Optional[str] = None
    vendorActions: Optional[str] = None
    deviationRationale: Optional[str] = None
    parentId: Optional[int] = None
    parentModule: Optional[str] = None
    createdBy: Optional[str] = None
    createdById: Optional[str] = Field(default_factory=RegScaleModel.get_user_id)
    lastUpdatedBy: Optional[str] = None
    lastUpdatedById: Optional[str] = Field(default_factory=RegScaleModel.get_user_id)
    dateLastUpdated: Optional[str] = Field(default_factory=get_current_datetime)
    securityChecks: Optional[str] = None
    recommendedActions: Optional[str] = None
    isPublic: Optional[bool] = True
    dependabotId: Optional[str] = None
    isPoam: Optional[bool] = False
    originalRiskRating: Optional[str] = None
    adjustedRiskRating: Optional[str] = None
    bRiskAdjustment: Optional[bool] = None
    basisForAdjustment: Optional[str] = None
    poamComments: Optional[str] = None
    otherIdentifier: Optional[str] = None
    integrationFindingId: Optional[str] = None
    wizCicdScanId: Optional[str] = None
    wizCicdScanVuln: Optional[str] = None
    sonarQubeIssueId: Optional[str] = None
    qualityAssurerId: Optional[str] = None
    remediationDescription: Optional[str] = None
    manualDetectionSource: Optional[str] = None
    manualDetectionId: Optional[str] = None
    vulnerabilityId: Optional[int] = None
    riskAdjustment: Optional[str] = None
    controlImplementationIds: List[int] = Field(default_factory=list)
    affectedControls: Optional[str] = None

    @staticmethod
    def is_multiple_controls_supported() -> bool:
        """
        Check if multiple control is supported

        :return: True if multiple controls is supported
        :rtype: bool
        """
        return RegscaleVersion.meets_minimum_version("7.0.0", dev_is_latest=False)

    def __init__(self, **data: Any):
        # Handle aliases internally
        if "parent_id" in data:
            data["parentId"] = data.pop("parent_id")
        if "parent_module" in data:
            data["parentModule"] = data.pop("parent_module")
        super().__init__(**data)

    # Mapping from FedRAMP-style severity to simple server-compatible values
    _severity_to_simple: Dict[str, str] = {
        "IV - Not Assigned": "Low",  # Server doesn't have NotAssigned, map to Low
        "III - Low - Other Weakness": "Low",
        "II - Moderate - Reportable Condition": "Medium",
        "I - High - Significant Deficiency": "High",
        "0 - Critical - Critical Deficiency": "Critical",
    }

    @field_serializer("severityLevel")
    def serialize_severity_level(self, value: Union[IssueSeverity, str]) -> str:
        """
        Serialize severity level to simple server-compatible values.

        The server expects simple severity values like "Low", "Medium", "High", "Critical"
        but the CLI enum uses FedRAMP-style values like "III - Low - Other Weakness".
        This serializer converts the FedRAMP values to simple server values.

        :param value: The severity level (enum or string)
        :return: Simple severity string compatible with server
        :rtype: str
        """
        if value is None:
            return "Low"

        # If it's an enum, get its value
        str_value = value.value if isinstance(value, IssueSeverity) else str(value)

        # Check if it's a FedRAMP-style value that needs conversion
        if str_value in self._severity_to_simple:
            return self._severity_to_simple[str_value]

        # If it's already a simple value, return it as-is
        simple_values = {"Low", "Medium", "High", "Critical"}
        if str_value in simple_values:
            return str_value

        # Default fallback
        return "Low"

    @staticmethod
    def _get_additional_endpoints() -> dict:
        """
        Get additional endpoints for the Issues model.

        :return: A dictionary of additional endpoints
        :rtype: dict
        """
        return {
            "user_open_items_days": "/api/{model_slug}/userOpenItemsDays/{strUserId}/{intDays}",
            "set_quality_assurer": "/api/{model_slug}/setQualityAssurer/{intIssueId}/{strQaUserId}",
            "remove_quality_assurer": "/api/{model_slug}/removeQualityAssurer/{intIssueId}",
            "process_lineage": "/api/{model_slug}/processLineage/{intIssueId}",
            "get_count": "/api/{model_slug}/getCount",
            "get_by_date_range": "/api/{model_slug}/getByDateRange/{dtStart}/{dtEnd}",
            "get_by_date_range_and_date_field": "/api/{model_slug}/getByDateRangeAndDateField/{dateField}/{dtStart}/{dtEnd}",
            "graph_by_owner_then_status": "/api/{model_slug}/graphByOwnerThenStatus/{dateField}/{dtStart}/{dtEnd}",
            "group_by_owner_and_plan_then_status_forever": "/api/{model_slug}/groupByOwnerAndPlanThenStatusForever",
            "group_by_owner_and_plan_then_status": "/api/{model_slug}/groupByOwnerAndPlanThenStatus/{dateField}/{dtStart}/{dtEnd}",
            "group_by_owner_and_component_then_status": "/api/{model_slug}/groupByOwnerAndComponentThenStatus/{dateField}/{dtStart}/{dtEnd}",
            "group_by_owner_and_component_then_status_forever": "/api/{model_slug}/groupByOwnerAndComponentThenStatusForever",
            "group_by_owner_and_component_then_status_drilldown": "/api/{model_slug}/groupByOwnerAndComponentThenStatusDrilldown/{intId}/{ownerId}/{dateField}/{dtStart}/{dtEnd}",
            "group_by_owner_and_plan_then_status_drilldown": "/api/{model_slug}/groupByOwnerAndPlanThenStatusDrilldown/{intId}/{ownerId}/{dateField}/{dtStart}/{dtEnd}",
            "get_by_date_closed": "/api/{model_slug}/getByDateClosed/{dtStart}/{dtEnd}",
            "get_all_by_integration_field": "/api/{model_slug}/getAllByIntegrationField/{strFieldName}",
            "get_active_by_integration_field": "/api/{model_slug}/getActiveByIntegrationField/{strFieldName}",
            "get_filtered_list": "/api/{model_slug}/getFilteredList/{strFind}",
            "get_all_by_grand_parent": "/api/{model_slug}/getAllByGrandParent/{intParentId}/{strModule}",
            "query_by_custom_field": "/api/{model_slug}/queryByCustomField/{strFieldName}/{strValue}",
            "issue_timeline": "/api/{model_slug}/issueTimeline/{intId}/{strModule}/{strType}",
            "calendar_issues": "/api/{model_slug}/calendarIssues/{dtDate}/{fId}/{orgId}/{userId}",
            "graph": "/api/{model_slug}/graph",
            "graph_by_date": "/api/{model_slug}/graphByDate/{strGroupBy}/{year}",
            "filter_issues": "/api/{model_slug}/filterIssues",
            "update_issue_screening": "/api/{model_slug}/screening/{id}",
            "retrieve_issue": "/api/{model_slug}/{intId}",
            "emass_component_export": "/api/{model_slug}/emassComponentExport/{intId}",
            "emass_ssp_export": "/api/{model_slug}/emassSSPExport/{intId}",
            "find_by_other_identifier": "/api/{model_slug}/findByOtherIdentifier/{id}",
            "find_by_service_now_id": "/api/{model_slug}/findByServiceNowId/{id}",
            "find_by_salesforce_case": "/api/{model_slug}/findBySalesforceCase/{id}",
            "find_by_jira_id": "/api/{model_slug}/findByJiraId/{id}",
            "find_by_dependabot_id": "/api/{model_slug}/findByDependabotId/{id}",
            "find_by_prisma_id": "/api/{model_slug}/findByPrismaId/{id}",
            "find_by_wiz_id": "/api/{model_slug}/findByWizId/{id}",
            "find_by_wiz_cicd_scan_id": "/api/{model_slug}/findByWizCicdScanId/{wizCicdScanId}",
            "get_all_by_wiz_cicd_scan_vuln": "/api/{model_slug}/getAllByWizCicdScanVuln/{wizCicdScanVuln}",
            "get_active_by_wiz_cicd_scan_vuln": "/api/{model_slug}/getActiveByWizCicdScanVuln/{wizCicdScanVuln}",
            "find_by_sonar_qube_issue_id": "/api/{model_slug}/findBySonarQubeIssueId/{projectId}/{issueId}",
            "find_by_defender_365_id": "/api/{model_slug}/findByDefender365Id/{id}",
            "find_by_defender_365_alert_id": "/api/{model_slug}/findByDefender365AlertId/{id}",
            "find_by_defender_cloud_id": "/api/{model_slug}/findByDefenderCloudId/{id}",
            "report": "/api/{model_slug}/report/{strReport}",
            "schedule": "/api/{model_slug}/schedule/{dtStart}/{dtEnd}/{dvar}",
            "graph_due_date": "/api/{model_slug}/graphDueDate/{year}",
            "graph_date_identified": "/api/{model_slug}/graphDateIdentified/{year}/{status}",
            "graph_severity_level_by_date_identified": "/api/{model_slug}/graphSeverityLevelByDateIdentified/{year}",
            "graph_cost_by_date_identified": "/api/{model_slug}/graphCostByDateIdentified/{year}",
            "graph_facility_by_date_identified": "/api/{model_slug}/graphFacilityByDateIdentified/{year}",
            "get_severity_level_by_status": "/api/{model_slug}/getSeverityLevelByStatus/{dtStart}/{dtEnd}",
            "graph_due_date_by_status": "/api/{model_slug}/graphDueDateByStatus/{year}",
            "dashboard": "/api/{model_slug}/dashboard/{strGroupBy}",
            "drilldown": "/api/{model_slug}/drilldown/{strMonth}/{temporal}/{strCategory}/{chartType}",
            "main_dashboard": "/api/{model_slug}/mainDashboard/{intYear}",
            "main_dashboard_chart": "/api/{model_slug}/mainDashboardChart/{year}",
            "dashboard_by_parent": "/api/{model_slug}/dashboardByParent/{strGroupBy}/{intId}/{strModule}",
            "batch_create": "/api/{model_slug}/batchCreate",
            "batch_update": "/api/{model_slug}/batchUpdate",
            "batch_create_or_update": "/api/{model_slug}/batchCreateOrUpdate",
            "find_by_integration_finding_id": "/api/{model_slug}/findByIntegrationFindingId/{id}",
        }

    @classmethod
    def _is_cache_valid(cls, plan_id: int) -> bool:
        """
        Check if cached data for a plan_id is still valid

        :param int plan_id: The plan ID to check cache validity for
        :return: True if cache is valid, False otherwise
        :rtype: bool
        """
        if plan_id not in _OPEN_ISSUES_CACHE:
            return False

        cached_time, _ = _OPEN_ISSUES_CACHE[plan_id]
        return (time.time() - cached_time) < _CACHE_TTL

    @classmethod
    def _get_from_cache(cls, plan_id: int) -> Optional[Dict[int, List[OpenIssueDict]]]:
        """
        Get cached data for a plan_id if it exists and is valid

        :param int plan_id: The plan ID to get cached data for
        :return: Cached data if valid, None otherwise
        :rtype: Optional[Dict[int, List[OpenIssueDict]]]
        """
        if cls._is_cache_valid(plan_id):
            _, cached_data = _OPEN_ISSUES_CACHE[plan_id]
            return cached_data
        return None

    @classmethod
    def _cache_data(cls, plan_id: int, data: Dict[int, List[OpenIssueDict]]) -> None:
        """
        Cache data for a plan_id

        :param int plan_id: The plan ID to cache data for
        :param Dict[int, List[OpenIssueDict]] data: The data to cache
        :rtype: None
        """
        _OPEN_ISSUES_CACHE[plan_id] = (time.time(), data)

    @classmethod
    def clear_cache(cls, plan_id: Optional[int] = None) -> None:
        """
        Clear cache for a specific plan_id or all cached data

        :param Optional[int] plan_id: The plan ID to clear cache for, or None to clear all cache
        :rtype: None
        """
        if plan_id is not None:
            _OPEN_ISSUES_CACHE.pop(plan_id, None)
        else:
            _OPEN_ISSUES_CACHE.clear()

    @classmethod
    def find_by_other_identifier(cls, other_identifier: str) -> List["Issue"]:
        """
        Find an issue by its other identifier.

        :param str other_identifier: The other identifier to search for
        :return: The found Issues
        :rtype: List[Issue]
        """
        api_handler = cls._get_api_handler()
        endpoint = cls.get_endpoint("find_by_other_identifier").format(id=other_identifier)

        response = api_handler.get(endpoint)
        issues: List["Issue"] = cls._handle_list_response(response)
        return issues

    @classmethod
    def find_by_integration_finding_id(cls, integration_finding_id: str) -> List["Issue"]:
        """
        Find an issue by its integration finding id.

        :param str integration_finding_id: The integration finding id to search for
        :return: The found Issues
        :rtype: List[Issue]
        """
        endpoint = cls.get_endpoint("find_by_integration_finding_id").format(id=integration_finding_id)
        response = cls._get_api_handler().get(endpoint)
        issues: List["Issue"] = cls._handle_list_response(response)
        # Ensure we are returning the cached object if it exists to ensure bulk updates work
        issues = [cls.get_cached_object(cls._get_cache_key(issue, {})) or issue for issue in issues]
        return issues

    @classmethod
    def get_all_by_integration_field(cls, field: str) -> List["Issue"]:
        """
        Get all issues by integration field.

        :param str field: The integration field to search for
        :return: The found Issues
        :rtype: List[Issue]
        """
        endpoint = cls.get_endpoint("get_all_by_integration_field").format(strFieldName=field)
        response = cls._get_api_handler().get(endpoint)
        return cls._handle_list_response(response)

    @classmethod
    def get_all_by_manual_detection_source(cls, value: str) -> List["Issue"]:
        """
        Get all issues with the manual detection source

        :param str value: The manual detection source to search for
        :return: The found Issues
        :rtype: List[Issue]
        """
        query = f"""
            query {{
                issues(take: 50, skip: 0, where: {{ manualDetectionSource: {{eq: "{value}"}}}})
                {{
                items {{
                    {Issue.build_graphql_fields()}
                }}
                pageInfo {{
                    hasNextPage
                }}
                ,totalCount}}
            }}
        """
        try:
            existing_issues = cls._get_api_handler().graph(query=query)["issues"]["items"]
        except (JSONDecodeError, TypeError, KeyError):
            existing_issues = []
        return [Issue(**issue) for issue in existing_issues]

    @staticmethod
    def get_issues_by_asset_map(plan_id: int) -> Dict[str, List["Issue"]]:
        """
        Get a dictionary of issues grouped by asset identifier for a given security plan.

        :param int plan_id: The ID of the security plan
        :return: A dictionary where keys are asset identifiers and values are lists of associated issues
        :rtype: Dict[str, List[Issue]]
        """
        issues = Issue.fetch_issues_by_ssp(None, ssp_id=plan_id, status=IssueStatus.Open.value)
        issues_by_asset = defaultdict(list)
        for issue in issues:
            if issue.assetIdentifier:
                for asset_identifier in issue.assetIdentifier.split("\n"):
                    issues_by_asset[asset_identifier].append(issue)
        return issues_by_asset

    @classmethod
    def assign_risk_rating(cls, value: Any) -> str:
        """
        Function to assign risk rating for an issue in RegScale using the provided value

        :param Any value: The value to analyze to determine the issue's risk rating
        :return: String of risk rating for RegScale issue, or "" if not found
        :rtype: str
        """
        if isinstance(value, str):
            if "low" in value.lower():
                return "Low"
            if "medium" in value.lower() or "moderate" in value.lower():
                return "Moderate"
            if "high" in value.lower() or "critical" in value.lower():
                return "High"
        return ""

    @classmethod
    def get_due_date(
        cls,
        severity: Union[IssueSeverity, str],
        config: dict,
        key: str,
        start_date: Union[str, datetime.datetime, None] = None,
        dt_format: Optional[str] = "%Y-%m-%dT%H:%M:%S",
        default_days: Optional[int] = 60,
    ) -> str:
        """
        Function to return due date based on the severity of the issue; the values are in the init.yaml
        and if not, it will default to 60 days from the current date.

        :param Union[IssueSeverity, str] severity: Severity of the issue, can be an IssueSeverity enum or a string
        :param dict config: Application config
        :param str key: The key to use for init.yaml from the issues section to determine the due date
        :param Union[str, datetime.datetime, None] start_date: The date to start the due date calculation from, defaults to current date
        :param Optional[str] dt_format: String of the date format to use, defaults to "%Y-%m-%dT%H:%M:%S"
        :param Optional[int] default_days: Default number of days to return if no values match, defaults to 60
        :return: Due date for the issue
        :rtype: str
        """
        if isinstance(start_date, str):
            from regscale.core.utils.date import datetime_obj

            start_date = datetime_obj(start_date)
        elif start_date is None:
            start_date = datetime.datetime.now()

        # if the severity is an enum, get the value
        if isinstance(severity, IssueSeverity):
            severity = severity.value
        elif isinstance(severity, (int, float)):
            # Handle numeric severity values by converting through assign_severity
            severity = cls.assign_severity(severity)
        elif str(severity).lower() not in [sev.value.lower() for sev in IssueSeverity]:
            severity = cls.assign_severity(severity)

        if severity == IssueSeverity.Critical.value:
            days = cls._get_days_for_values(["critical"], config, key, default_days)
        elif severity == IssueSeverity.High.value:
            days = cls._get_days_for_values(["high"], config, key, default_days)
        elif severity == IssueSeverity.Moderate.value:
            days = cls._get_days_for_values(["moderate", "medium"], config, key, default_days)
        elif severity == IssueSeverity.Low.value:
            days = cls._get_days_for_values(["low", "minor"], config, key, default_days)
        else:
            days = default_days
        due_date = start_date + datetime.timedelta(days=days)
        return due_date.strftime(dt_format)

    @staticmethod
    def _get_days_for_values(possible_values: List[str], config: dict, key: str, default: Optional[int] = 30) -> int:
        """
        Get the number of days for the given possible values from the configuration.

        :param List[str] possible_values: List of possible values to check
        :param dict config: Application config
        :param str key: The key to use for init.yaml from the issues section to determine the due date
        :param Optional[int] default: Default number of days to return if no values match, defaults to 30
        :return: Number of days for the first matching value, or 0 if none match
        :rtype: int
        """
        for value in possible_values:
            days = config["issues"].get(key, {}).get(value, 0)
            if days > 0:
                return days
        return default

    @staticmethod
    def assign_severity(value: Optional[Any] = None) -> str:
        """
        Function to assign severity for an issue in RegScale using the provided value

        :param Optional[Any] value: The value to analyze to determine the issue's severity, defaults to None
        :return: String of severity level for RegScale issue
        :rtype: str
        """
        severity_levels = {
            "low": IssueSeverity.Low.value,
            "moderate": IssueSeverity.Moderate.value,
            "high": IssueSeverity.High.value,
            "critical": IssueSeverity.Critical.value,
        }
        severity = IssueSeverity.NotAssigned.value
        # see if the value is an int or float
        if isinstance(value, (int, float)):
            # check severity score and assign it to the appropriate RegScale severity
            if value >= 7:
                severity = severity_levels["high"]
            elif 4 <= value < 7:
                severity = severity_levels["moderate"]
            else:
                severity = severity_levels["low"]
        elif isinstance(value, str):
            if value.lower() in ["low", "lowest", "minor"]:
                severity = severity_levels["low"]
            elif value.lower() in ["medium", "moderate", "major"]:
                severity = severity_levels["moderate"]
            elif value.lower() in ["high", "highest", "blocker"]:
                severity = severity_levels["high"]
            elif value.lower() in ["critical"]:
                severity = severity_levels["critical"]
            elif value in list(severity_levels.values()):
                severity = value
        return severity

    @staticmethod
    def update_issue(app: Application, issue: "Issue") -> Optional["Issue"]:
        """
        Update an issue in RegScale

        :param Application app: Application Instance
        :param Issue issue: Issue to update in RegScale
        :return: Updated issue in RegScale
        :rtype: Optional[Issue]
        """
        if isinstance(issue, dict):
            issue = Issue(**issue)
        api = Api()
        issue_id = issue.id

        response = api.put(app.config["domain"] + f"/api/issues/{issue_id}", json=issue.dict())
        if response.status_code == 200:
            try:
                issue = Issue(**response.json())
            except JSONDecodeError:
                return None
        return issue

    @staticmethod
    def insert_issue(app: Application, issue: "Issue") -> Optional["Issue"]:
        """
        Insert an issue in RegScale

        :param Application app: Application Instance
        :param Issue issue: Issue to insert to RegScale
        :return: Newly created issue in RegScale
        :rtype: Optional[Issue]
        """
        if isinstance(issue, dict):
            issue = Issue(**issue)
        api = Api()
        logger = create_logger()
        response = api.post(app.config["domain"] + "/api/issues", json=issue.dict())
        if response.status_code == 200:
            try:
                issue = Issue(**response.json())
            except JSONDecodeError as jex:
                logger.error("Unable to read issue:\n%s", jex)
                return None
        else:
            logger.warning("Unable to insert issue: %s", issue.title)
        return issue

    @staticmethod
    def bulk_insert(
        app: Application,
        issues: List["Issue"],
        max_workers: Optional[int] = 10,
        batch_size: int = 100,
        batch: bool = False,
    ) -> List["Issue"]:
        """
        Bulk insert issues using the RegScale API and ThreadPoolExecutor

        :param Application app: Application Instance
        :param List["Issue"] issues: List of issues to insert
        :param Optional[int] max_workers: Max Workers, defaults to 10
        :param int batch_size: Number of issues to insert per batch, defaults to 100
        :param bool batch: Insert issues in batches, defaults to False
        :return: List of Issues from RegScale
        :rtype: List[Issue]
        """
        api = Api()
        url = urljoin(app.config["domain"], "/api/{model_slug}/batchcreate")
        results = []
        api.logger.info("Creating %i new issue(s) in RegScale...", len(issues))
        with Progress(transient=False) as progress:
            task = progress.add_task(f"Creating {len(issues)} new issue(s) in RegScale...", total=len(issues))
            if batch:
                # Chunk list into batches
                batches = [issues[i : i + batch_size] for i in range(0, len(issues), batch_size)]
                for my_batch in batches:
                    res = api.post(url=url.format(model_slug="issues"), json=[iss.dict() for iss in my_batch])
                    if not res.ok:
                        app.logger.error(
                            "%i: %s\nError creating batch of issues: %s",
                            res.status_code,
                            res.text,
                            res.reason,
                        )
                    results.append(res)
                    progress.update(task, advance=len(my_batch))
            else:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(
                            issue.create,
                        )
                        for issue in issues
                    ]
                    for future in as_completed(futures):
                        issue = future.result()
                        results.append(issue)
                        progress.update(task, advance=1)
        return results

    @staticmethod
    def bulk_update(
        app: Application,
        issues: List["Issue"],
        max_workers: int = 10,
        batch_size: int = 100,
        batch: bool = False,
    ) -> List["Issue"]:
        """
        Bulk update issues using the RegScale API and ThreadPoolExecutor

        :param Application app: Application Instance
        :param List["Issue"] issues: List of issues to update
        :param int max_workers: Max Workers, defaults to 10
        :param int batch_size: Number of issues to update per batch, defaults to 100
        :param bool batch: Update issues in batches, defaults to False
        :return: List of Issues from RegScale
        :rtype: List[Issue]
        """
        api = Api()
        url = urljoin(app.config["domain"], "/api/{model_slug}/batchupdate")
        results = []
        api.logger.info("Updating %i issue(s) in RegScale...", len(issues))
        with Progress(transient=False) as progress:
            task = progress.add_task(f"Updating {len(issues)} issue(s) in RegScale...", total=len(issues))
            if batch:
                # Chunk list into batches
                batches = [issues[i : i + batch_size] for i in range(0, len(issues), batch_size)]
                for my_batch in batches:
                    res = api.put(url=url.format(model_slug="issues"), json=[iss.dict() for iss in my_batch])
                    if not res.ok:
                        app.logger.error(
                            "%i: %s\nError creating batch of issues: %s",
                            res.status_code,
                            res.text,
                            res.reason,
                        )
                    results.append(res)
                    progress.update(task, advance=len(my_batch))
            else:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(issue.save) for issue in issues]
                    for future in as_completed(futures):
                        issue = future.result()
                        results.append(issue)
                        progress.update(task, advance=1)

        return results

    @staticmethod
    def fetch_issues_by_parent(
        app: Application,
        regscale_id: int,
        regscale_module: str,
    ) -> List["Issue"]:
        """
        Find all issues by parent id and parent module

        :param Application app: Application Instance
        :param int regscale_id: Parent ID
        :param str regscale_module: Parent Module
        :return: List of issues from RegScale
        :rtype: List[Issue]
        """
        api = Api()
        body = f"""
                query {{
                    issues(take: 50, skip: 0, where: {{ parentModule: {{eq: "{regscale_module}"}} parentId: {{
                      eq: {regscale_id}
                    }}}}) {{
                    items {{
                        {Issue.build_graphql_fields()}
                    }}
                    pageInfo {{
                        hasNextPage
                    }}
                    ,totalCount}}
                }}
                """
        try:
            existing_issues = api.graph(query=body)["issues"]["items"]
        except (JSONDecodeError, TypeError, KeyError):
            existing_issues = []
        return [Issue(**issue) for issue in existing_issues]

    @staticmethod
    def fetch_issues_by_ssp(
        app: Optional[Application],
        ssp_id: int,
        status: Optional[str] = None,
    ) -> List["Issue"]:
        """
        Find all issues by parent id and parent module (with concurrent pagination)

        :param Application app: Application Instance
        :param int ssp_id: RegScale SSP Id
        :param Optional[str] status: Issue Status, defaults to None
        :return: List of Issues from RegScale SSP
        :rtype: List[Issue]
        """
        import logging

        logger = logging.getLogger("regscale")

        api = Api()
        take = 50

        # Build where clause
        where_conditions = [f"securityPlanId: {{eq: {ssp_id}}}"]
        if status:
            where_conditions.append(f'status: {{eq: "{status}"}}')
        where_str = ", ".join(where_conditions)

        # Build query for first page
        def build_query(skip: int, page_size: int) -> str:
            return f"""
                query {{
                    issues(take: {page_size}, skip: {skip}, where: {{ {where_str} }}) {{
                        items {{
                            {Issue.build_graphql_fields()}
                        }}
                        pageInfo {{
                            hasNextPage
                        }}
                        totalCount
                    }}
                }}
            """

        # Fetch first page to get total count
        try:
            first_query = build_query(0, take)
            response = api.graph(query=first_query)
            items = response.get("issues", {}).get("items", [])
            total_count = response.get("issues", {}).get("totalCount", 0)

            logger.debug(f"fetch_issues_by_ssp: Fetched first page with {len(items)} items, total: {total_count}")

            # Convert first page items to Issue objects
            all_issues = [Issue(**issue) for issue in items]

            # If there are more pages, use concurrent pagination
            if total_count > take:
                logger.info(
                    f"fetch_issues_by_ssp: Fetching remaining pages concurrently (total: {total_count}, remaining: {total_count - take})"
                )
                try:
                    from regscale.core.utils.async_graphql_client import run_async_paginated_query

                    # Get API credentials
                    domain = api.config.get("domain", "")
                    token = api.config.get("token", "")
                    endpoint = f"{domain}/graphql"
                    headers = {"Authorization": f"{token}"}

                    logger.info(f"fetch_issues_by_ssp: About to call run_async_paginated_query for SSP {ssp_id}")

                    # Create query builder function
                    def query_builder(skip: int, page_size: int) -> str:
                        return build_query(skip, page_size)

                    # Define token refresh callback
                    def token_refresh() -> str:
                        return api.config.get("token", "")

                    # Fetch remaining pages concurrently
                    # Use max_concurrent=2 to avoid overwhelming the GraphQL API with 500 errors
                    remaining_items = run_async_paginated_query(
                        endpoint=endpoint,
                        headers=headers,
                        query_builder=query_builder,
                        topic_key="issues",
                        total_count=total_count - take,  # Subtract first page
                        page_size=take,
                        starting_skip=take,  # Start from second page
                        max_concurrent=2,
                        timeout=60,
                        task_name=f"SSP {ssp_id} Issues",
                        token_refresh_callback=token_refresh,
                    )

                    logger.info("fetch_issues_by_ssp: run_async_paginated_query returned successfully")

                    # Convert remaining items to Issue objects
                    all_issues.extend([Issue(**issue) for issue in remaining_items])
                    logger.info(
                        f"fetch_issues_by_ssp: Fetched {len(remaining_items)} items from remaining pages, total: {len(all_issues)}"
                    )
                except Exception as e:
                    logger.error(
                        f"fetch_issues_by_ssp: Error during concurrent pagination: {type(e).__name__}: {e}",
                        exc_info=True,
                    )
                    logger.warning(f"fetch_issues_by_ssp: Falling back to first page only ({len(all_issues)} issues)")
                    # Continue with just the first page of results rather than failing completely

            return all_issues

        except (JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"fetch_issues_by_ssp: Error fetching issues: {e}")
            return []

    @staticmethod
    def fetch_all_issues(
        app: Application,
    ) -> List["Issue"]:
        """
        Find all issues in RegScale

        :param Application app: Application Instance
        :return: List of Issues from RegScale
        :rtype: List[Issue]
        """
        api = Api()
        body = f"""
                    query {{
                        issues(take: 50, skip: 0) {{
                        items {{
                            {Issue.build_graphql_fields()}
                        }}
                        pageInfo {{
                            hasNextPage
                        }}
                        ,totalCount}}
                    }}
                    """
        try:
            api.logger.info("Retrieving all issues from RegScale...")
            existing_issues = api.graph(query=body)["issues"]["items"]
            api.logger.info("Retrieved %i issue(s) from RegScale.", len(existing_issues))
        except (JSONDecodeError, KeyError):
            existing_issues = []
        return [Issue(**issue) for issue in existing_issues]

    @staticmethod
    def fetch_issue_by_id(
        app: Application,
        issue_id: int,
    ) -> Optional["Issue"]:
        """
        Find a RegScale issue by its id

        :param Application app: Application Instance
        :param int issue_id: RegScale Issue Id
        :return: Issue from RegScale or None if it doesn't exist
        :rtype: Optional[Issue]
        """
        api = Api()
        issue_response = api.get(url=f"{app.config['domain']}/api/issues/{issue_id}")
        issue = None
        try:
            issue = Issue(**issue_response.json())
        except JSONDecodeError:
            logger = create_logger()
            logger.warning("Unable to find issue with id %i", issue_id)
        return issue

    @staticmethod
    def fetch_issues_and_attachments_by_parent(
        parent_id: int,
        parent_module: str,
        fetch_attachments: Optional[bool] = True,
        save_issues: Optional[bool] = True,
    ) -> Tuple[List["Issue"], Optional[Dict[int, List["File"]]]]:
        """
        Fetch all issues from RegScale for the provided parent record

        :param int parent_id: Parent record ID in RegScale
        :param str parent_module: Parent record module in RegScale
        :param Optional[Application] app: Application object, deprecated 3.26.2024, defaults to None
        :param Optional[bool] fetch_attachments: Whether to fetch attachments from RegScale, defaults to True
        :param Optional[bool] save_issues: Save RegScale issues to a .json in artifacts, defaults to True
        :return: List of RegScale issues, dictionary of issue's attachments as File objects
        :rtype: Tuple[List[Issue], Optional[Dict[int, List[File]]]]
        """
        from regscale.models import File

        attachments: Optional[Dict[int, List[File]]] = None
        logger = create_logger()
        # get the existing issues for the parent record that are already in RegScale
        logger.info("Fetching full issue list from RegScale %s #%i.", parent_module, parent_id)
        issues_data = Issue().get_all_by_parent(
            parent_id=parent_id,
            parent_module=parent_module,
        )

        # check for null/not found response
        if len(issues_data) == 0:
            logger.warning(
                "No existing issues for this RegScale record #%i in %s.",
                parent_id,
                parent_module,
            )
        else:
            if fetch_attachments:
                # get the attachments for the issue
                api = Api()
                attachments = {
                    issue.id: files
                    for issue in issues_data
                    if (
                        files := File.get_files_for_parent_from_regscale(
                            parent_id=issue.id,
                            parent_module="issues",
                            api=api,
                        )
                    )
                }
            logger.info(
                "Found %i issue(s) from RegScale %s #%i for processing.",
                len(issues_data),
                parent_module,
                parent_id,
            )
            if save_issues:
                # write issue data to a json file
                check_file_path("artifacts")
                file_name = "existingRegScaleIssues.json"
                file_path = Path("./artifacts") / file_name
                save_data_to(
                    file=file_path,
                    data=[issue.dict() for issue in issues_data],
                    output_log=False,
                )
                logger.info(
                    "Saved RegScale issue(s) for %s #%i, see %s", parent_module, parent_id, str(file_path.absolute())
                )
        return issues_data, attachments

    @classmethod
    def get_open_issues_ids_by_implementation_id(
        cls, plan_id: int, is_component: Optional[bool] = False
    ) -> Dict[int, List[OpenIssueDict]]:
        """
        Get all open issues by implementation id for a given security plan with optimized performance and caching

        :param int plan_id: The ID of the parent
        :param bool is_component: Optional[bool] Defaults to False
        :return: A dictionary of control ids and their associated issue ids
        :rtype: Dict[int, List[OpenIssueDict]]
        """
        import logging

        logger = logging.getLogger("regscale")

        # Check cache first
        cached_data = cls._check_cache(plan_id, logger)
        if cached_data is not None:
            return cached_data

        # Fetch open issues from API
        control_issues = cls._fetch_open_issues_from_api(plan_id, is_component, logger)

        # Cache the results if caching is enabled
        if not cls._is_cache_disabled():
            cls._cache_data(plan_id, control_issues)

        return control_issues

    @classmethod
    def _check_cache(cls, plan_id: int, logger) -> Optional[Dict[int, List[OpenIssueDict]]]:
        """
        Check cache for open issues data

        :param int plan_id: The ID of the parent
        :param logger: Logger instance
        :return: Cached data if available and valid, None otherwise
        :rtype: Optional[Dict[int, List[OpenIssueDict]]]
        """
        if cls._is_cache_disabled():
            return None

        cached_data = cls._get_from_cache(plan_id)
        if cached_data is not None:
            logger.info(f"Using cached open issues data for security plan {plan_id}")
        return cached_data

    @classmethod
    def _fetch_open_issues_from_api(cls, plan_id: int, is_component: bool, logger) -> Dict[int, List[OpenIssueDict]]:
        """
        Fetch open issues from API with pagination

        :param int plan_id: The ID of the parent
        :param bool is_component: Whether parent is a component
        :param logger: Logger instance
        :return: Dictionary of control IDs to open issues
        :rtype: Dict[int, List[OpenIssueDict]]
        """
        start_time = time.time()
        module_str = "component" if is_component else "security plan"
        logger.info(f"Fetching open issues for controls and for {module_str} {plan_id}...")

        control_issues: Dict[int, List[OpenIssueDict]] = defaultdict(list)

        try:
            total_fetched = cls._paginate_and_process_issues(plan_id, is_component, control_issues, logger)
            cls._log_completion(plan_id, total_fetched, len(control_issues), start_time, logger)
        except Exception as e:
            logger.error(f"Error fetching open issues for security plan {plan_id}: {e}")
            return defaultdict(list)

        return control_issues

    @classmethod
    def _paginate_and_process_issues(
        cls,
        plan_id: int,
        is_component: bool,
        control_issues: Dict[int, List[OpenIssueDict]],
        logger,
    ) -> int:
        """
        Paginate through API results and process issues using concurrent requests

        :param int plan_id: The ID of the parent
        :param bool is_component: Whether parent is a component
        :param Dict[int, List[OpenIssueDict]] control_issues: Dictionary to populate with results
        :param logger: Logger instance
        :return: Total number of items fetched
        :rtype: int
        """
        take = 50
        supports_multiple_controls = cls.is_multiple_controls_supported()
        fields = cls._get_query_fields(supports_multiple_controls)

        # First fetch to get total count
        query = cls._build_query(plan_id, is_component, 0, take, fields)
        response = cls._get_api_handler().graph(query)

        items = response.get(cls.get_module_string(), {}).get("items", [])
        total_count = response.get(cls.get_module_string(), {}).get("totalCount", 0)

        # Process first page
        cls._process_issue_items(items, supports_multiple_controls, control_issues)
        logger.info("Fetched first page with %d items, total: %d", len(items), total_count)

        # Use concurrent pagination for remaining pages if there are more
        if total_count > take:
            logger.info("Fetching remaining pages concurrently...")
            from regscale.core.utils.async_graphql_client import run_async_paginated_query

            # Get API credentials
            api_handler = cls._get_api_handler()
            domain = api_handler.config.get("domain", "")
            token = api_handler.config.get("token", "")
            endpoint = f"{domain}/graphql"
            headers = {"Authorization": f"{token}"}

            # Create query builder
            def query_builder(skip: int, page_size: int) -> str:
                return cls._build_query(plan_id, is_component, skip, page_size, fields)

            # Define token refresh callback
            def token_refresh() -> str:
                # Re-read token from config in case it was refreshed
                return api_handler.config.get("token", "")

            # Fetch remaining pages concurrently
            remaining_items = run_async_paginated_query(
                endpoint=endpoint,
                headers=headers,
                query_builder=query_builder,
                topic_key=cls.get_module_string(),
                total_count=total_count - take,  # Subtract first page
                page_size=take,
                starting_skip=take,  # Start from second page
                max_concurrent=5,
                timeout=60,
                task_name="Open Issues",
                token_refresh_callback=token_refresh,
            )

            # Process remaining items
            for batch_items in [remaining_items[i : i + 100] for i in range(0, len(remaining_items), 100)]:
                cls._process_issue_items(batch_items, supports_multiple_controls, control_issues)
            logger.info("Fetched %d items from remaining pages", len(remaining_items))

        return total_count

    @classmethod
    def _get_query_fields(cls, supports_multiple_controls: bool) -> str:
        """
        Get GraphQL query fields based on control support

        :param bool supports_multiple_controls: Whether multiple controls are supported
        :return: GraphQL field selection string
        :rtype: str
        """
        if supports_multiple_controls:
            return "id, otherIdentifier, integrationFindingId, controlImplementations { id }"
        return "id, controlId, otherIdentifier, integrationFindingId"

    @classmethod
    def _build_query(cls, plan_id: int, is_component: bool, skip: int, take: int, fields: str) -> str:
        """
        Build GraphQL query for fetching open issues

        :param int plan_id: The ID of the parent
        :param bool is_component: Whether parent is a component
        :param int skip: Number of items to skip
        :param int take: Number of items to take
        :param str fields: GraphQL fields to select
        :return: GraphQL query string
        :rtype: str
        """
        parent_field = "componentId" if is_component else "securityPlanId"
        return f"""
            query GetOpenIssuesByPlanOrComponent {{
                {cls.get_module_string()}(
                    skip: {skip},
                    take: {take},
                    where: {{
                        {parent_field}: {{eq: {plan_id}}},
                        status: {{eq: "Open"}}
                    }}
                ) {{
                    items {{ {fields} }}
                    pageInfo {{ hasNextPage }}
                    totalCount
                }}
            }}
        """

    @classmethod
    def _log_progress(cls, skip: int, take: int, items_count: int, total_count: int, logger) -> None:
        """
        Log progress for large datasets

        :param int skip: Number of items skipped
        :param int take: Batch size
        :param int items_count: Number of items in current batch
        :param int total_count: Total count of items
        :param logger: Logger instance
        :rtype: None
        """
        if total_count > 1000:
            logger.info(
                f"Processing batch {skip // take + 1} - fetched {items_count} items ({skip + items_count}/{total_count})"
            )

    @classmethod
    def _process_issue_items(
        cls,
        items: List[Dict[str, Any]],
        supports_multiple_controls: bool,
        control_issues: Dict[int, List[OpenIssueDict]],
    ) -> None:
        """
        Process issue items and populate control_issues dictionary

        :param List[Dict[str, Any]] items: List of issue items from API
        :param bool supports_multiple_controls: Whether multiple controls are supported
        :param Dict[int, List[OpenIssueDict]] control_issues: Dictionary to populate
        :rtype: None
        """
        for item in items:
            issue_dict = OpenIssueDict(
                id=item["id"],
                otherIdentifier=item.get("otherIdentifier", ""),
                integrationFindingId=item.get("integrationFindingId", ""),
            )

            if supports_multiple_controls:
                cls._add_issue_to_multiple_controls(item, issue_dict, control_issues)
            else:
                cls._add_issue_to_single_control(item, issue_dict, control_issues)

    @classmethod
    def _add_issue_to_multiple_controls(
        cls,
        item: Dict[str, Any],
        issue_dict: OpenIssueDict,
        control_issues: Dict[int, List[OpenIssueDict]],
    ) -> None:
        """
        Add issue to multiple control implementations

        :param Dict[str, Any] item: Issue item from API
        :param OpenIssueDict issue_dict: Issue dictionary
        :param Dict[int, List[OpenIssueDict]] control_issues: Dictionary to populate
        :rtype: None
        """
        if item.get("controlImplementations"):
            for control in item.get("controlImplementations", []):
                control_issues[control["id"]].append(issue_dict)

    @classmethod
    def _add_issue_to_single_control(
        cls,
        item: Dict[str, Any],
        issue_dict: OpenIssueDict,
        control_issues: Dict[int, List[OpenIssueDict]],
    ) -> None:
        """
        Add issue to single control

        :param Dict[str, Any] item: Issue item from API
        :param OpenIssueDict issue_dict: Issue dictionary
        :param Dict[int, List[OpenIssueDict]] control_issues: Dictionary to populate
        :rtype: None
        """
        if item.get("controlId"):
            control_issues[item["controlId"]].append(issue_dict)

    @classmethod
    def _log_completion(cls, plan_id: int, total_fetched: int, control_count: int, start_time: float, logger) -> None:
        """
        Log completion statistics

        :param int plan_id: The ID of the parent
        :param int total_fetched: Total number of items fetched
        :param int control_count: Number of controls with issues
        :param float start_time: Start time of the operation
        :param logger: Logger instance
        :rtype: None
        """
        elapsed_time = time.time() - start_time
        logger.info(
            f"Finished fetching {total_fetched} open issue(s) for {control_count} control(s) "
            f"in security plan {plan_id} - took {elapsed_time:.2f} seconds"
        )

    @classmethod
    def get_sort_position_dict(cls) -> Dict[str, int]:
        """
        Overrides the base method.

        :return: The sort position in the list of properties
        :rtype: Dict[str, int]
        """
        return {
            "id": 1,
            "title": 2,
            "severityLevel": 3,
            "issueOwnerId": 4,
            "dueDate": 5,
            "uuid": -1,
            "dateCreated": 6,
            "description": 7,
            "issueOwner": -1,
            "costEstimate": 9,
            "levelOfEffort": 10,
            "identification": 11,
            "capStatus": 12,
            "sourceReport": 13,
            "status": 14,
            "dateCompleted": 15,
            "activitiesObserved": 16,
            "failuresObserved": 17,
            "requirementsViolated": 18,
            "safetyImpact": 19,
            "securityImpact": 20,
            "qualityImpact": 21,
            "facility": -1,
            "facilityId": -1,
            "org": -1,
            "orgId": -1,
            "controlId": 26,
            "assessmentId": 27,
            "requirementId": 28,
            "securityPlanId": 29,
            "projectId": 30,
            "supplyChainId": 31,
            "policyId": 32,
            "componentId": 33,
            "incidentId": 34,
            "jiraId": 35,
            "serviceNowId": 36,
            "wizId": 37,
            "burpId": 38,
            "defenderId": 39,
            "defenderAlertId": 40,
            "defenderCloudId": 41,
            "salesforceId": 42,
            "prismaId": 43,
            "tenableId": 44,
            "tenableNessusId": 45,
            "qualysId": 46,
            "pluginId": 47,
            "cve": 48,
            "assetIdentifier": 49,
            "falsePositive": 50,
            "operationalRequirement": 51,
            "autoApproved": 52,
            "kevList": 53,
            "dateFirstDetected": 54,
            "changes": 55,
            "vendorDependency": 56,
            "vendorName": 57,
            "vendorLastUpdate": 58,
            "vendorActions": 59,
            "deviationRationale": 60,
            "parentId": 61,
            "parentModule": 62,
            "createdBy": -1,
            "createdById": -1,
            "lastUpdatedBy": -1,
            "lastUpdatedById": -1,
            "dateLastUpdated": -1,
            "securityChecks": 63,
            "recommendedActions": 64,
            "isPublic": 65,
            "dependabotId": 66,
            "isPoam": 67,
            "originalRiskRating": 68,
            "adjustedRiskRating": 69,
            "bRiskAdjustment": 70,
            "basisForAdjustment": 71,
        }

    @classmethod
    def get_enum_values(cls, field_name: str) -> List[Union[IssueSeverity, IssueStatus, IssueIdentification, str]]:
        """
        Overrides the base method.

        :param str field_name: The property name to provide enum values for
        :return: List of enum values or strings
        :rtype: List[Union[IssueSeverity, IssueStatus, IssueIdentification, str]]
        """
        if field_name == "severityLevel":
            return [severity.__str__() for severity in IssueSeverity]
        if field_name == "status":
            return [status.__str__() for status in IssueStatus]
        if field_name == "identification":
            return [identification.__str__() for identification in IssueIdentification]
        return cls.get_bool_enums(field_name)

    @classmethod
    def get_lookup_field(cls, field_name: str) -> str:
        """
        Overrides the base method.

        :param str field_name: The property name to provide enum values for
        :return: The field name to look up
        :rtype: str
        """
        lookup_fields = {"issueOwnerId": "user", "facilityId": "facilities", "orgId": "organizations"}
        if field_name in lookup_fields.keys():
            return lookup_fields[field_name]
        return ""

    @classmethod
    def is_date_field(cls, field_name: str) -> bool:
        """
        Overrides the base method.

        :param str field_name: The property name to provide enum values for
        :return: If the field should be formatted as a date
        :rtype: bool
        """
        return field_name in ["dueDate", "dateCreated", "dateCompleted", "dateFirstDetected"]

    # pylint: disable=C0301
    @classmethod
    def get_export_query(cls, app: Application, parent_id: int, parent_module: str) -> List[Dict[str, Any]]:
        """
        Overrides the base method.

        :param Application app: RegScale Application object
        :param int parent_id: RegScale ID of parent
        :param str parent_module: Module of parent
        :return: GraphQL response from RegScale
        :rtype: List[Dict[str, Any]]
        """
        body = """
                query {
                        issues (skip: 0, take: 50, where: {parentId: {eq: parent_id} parentModule: {eq: "parent_module"}}) {
                          items {
                           id
                           issueOwnerId
                           issueOwner {
                             firstName
                             lastName
                             userName
                           }
                           title
                           dateCreated
                           description
                           severityLevel
                           costEstimate
                           levelOfEffort
                           dueDate
                           identification
                           status
                           dateCompleted
                           activitiesObserved
                           failuresObserved
                           requirementsViolated
                           safetyImpact
                           securityImpact
                           qualityImpact
                           securityChecks
                           recommendedActions
                           isPoam
                           parentId
                           parentModule
                          }
                          totalCount
                          pageInfo {
                            hasNextPage
                          }
                        }
                     }
                    """.replace(
            "parent_module", parent_module
        ).replace(
            "parent_id", str(parent_id)
        )

        api = Api()
        existing_issue_data = api.graph(query=body)

        if existing_issue_data["issues"]["totalCount"] > 0:
            raw_data = existing_issue_data["issues"]["items"]
            moded_data = []
            for a in raw_data:
                moded_data.append(build_issue_dict_from_query(a))
            return moded_data
        return []

    # pylint: enable=C0301

    @classmethod
    def find_by_service_now_id(cls, snow_id: str) -> List["Issue"]:
        """
        Find issues by its serviceNowId

        :param str snow_id: The serviceNowId to search for
        :return: The found Issues
        :rtype: List[Issue]
        """
        api_handler = cls._get_api_handler()
        endpoint = cls.get_endpoint("find_by_service_now_id").format(id=snow_id)

        response = api_handler.get(endpoint)
        issues: List["Issue"] = cls._handle_list_response(response)
        return issues

    @classmethod
    def use_query(cls) -> bool:
        """
        Overrides the base method.

        :return: Whether to use query
        :rtype: bool
        """
        return True

    @classmethod
    def get_extra_fields(cls) -> List[str]:
        """
        Overrides the base method.

        :return: List of extra field names
        :rtype: List[str]
        """
        return []

    @classmethod
    def get_include_fields(cls) -> List[str]:
        """
        Overrides the base method.

        :return: List of field names to include
        :rtype: List[str]
        """
        return []

    @field_validator("riskAdjustment")
    def validate_risk_adjustment(cls, v: str) -> str:
        """
        Validates the riskAdjustment field.

        :param str v: The value to validate
        :raise ValueError: If the value is not valid

        :return: The validated values
        :rtype: str

        """
        allowed_values = ["No", "Yes", "Pending", None]
        if v not in allowed_values:
            raise ValueError(f"riskAdjustment must be one of {allowed_values}")
        return v

    @field_validator("issueOwner", "createdBy", "lastUpdatedBy", mode="before")
    @classmethod
    def convert_user_object_to_string(cls, v: Any) -> Optional[str]:
        """
        Convert user objects returned by API to string representation.

        The API sometimes returns nested user objects for these fields instead of strings.
        This validator handles both formats gracefully.

        :param Any v: The value to validate (string, dict, or None)
        :return: String representation or None
        :rtype: Optional[str]
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            # Try to extract a meaningful string from the user object
            # Common fields: userName, email, firstName + lastName, or id
            if "userName" in v:
                return str(v["userName"])
            if "email" in v:
                return str(v["email"])
            if "firstName" in v and "lastName" in v:
                return f"{v['firstName']} {v['lastName']}".strip()
            if "id" in v:
                return str(v["id"])
            # Fallback to string representation of the dict
            return str(v)
        # For any other type, convert to string
        return str(v)

    def _get_default_config(self, standard: str) -> Dict[str, Any]:
        """
        Get default configuration thresholds based on standard.

        Args:
            standard: 'fedramp' or 'nist'

        Returns:
            Dictionary with default thresholds
        """
        if standard == "fedramp":
            return {"critical": 30, "high": 30, "medium": 90, "low": 180, "status": "Open"}
        return {"critical": 30, "high": 90, "medium": 90, "low": 180, "status": "Open"}

    def _parse_detection_date(self, detection_date_str: str) -> Optional[datetime.datetime]:
        """
        Parse detection date from string.

        Args:
            detection_date_str: Date string to parse

        Returns:
            Parsed datetime or None if parsing fails
        """
        try:
            return datetime.datetime.strptime(detection_date_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                return datetime.datetime.strptime(detection_date_str, "%Y-%m-%d")
            except ValueError:
                return None

    def _calculate_threshold_days(self, config: Dict[str, Any]) -> int:
        """
        Calculate threshold days based on severity and config.

        Args:
            config: Configuration dictionary with severity thresholds

        Returns:
            Number of threshold days for this issue
        """
        severity_map = {
            IssueSeverity.Critical: config.get("critical", 30),
            IssueSeverity.High: config.get("high", 90),
            IssueSeverity.Moderate: config.get("medium", 90),
            IssueSeverity.Low: config.get("low", 365),
            IssueSeverity.NotAssigned: config.get("low", 365),
        }
        severity = (
            IssueSeverity(self.severityLevel)
            if self.severityLevel in {s.value for s in IssueSeverity}
            else IssueSeverity.NotAssigned
        )
        return severity_map[severity]

    def _apply_fedramp_logic(
        self, severity: IssueSeverity, is_scan: bool, days_since_detection: int, threshold_days: int, open_statuses: set
    ) -> bool:
        """
        Apply FedRAMP-specific POAM logic.

        Args:
            severity: Issue severity level
            is_scan: Whether this is a scan-based issue
            days_since_detection: Days since issue was detected
            threshold_days: Threshold for overdue status
            open_statuses: Set of statuses considered open

        Returns:
            Whether this should be marked as a POAM
        """
        if severity in {IssueSeverity.High, IssueSeverity.Critical}:
            return self.status in open_statuses
        if is_scan:
            return days_since_detection > threshold_days
        return self.status in open_statuses

    def _check_vendor_dependency(self, current_date: datetime.datetime, threshold_days: int) -> Optional[bool]:
        """
        Check if vendor dependency affects POAM status.

        Args:
            current_date: Current date for calculation
            threshold_days: Threshold for overdue status

        Returns:
            POAM status if vendor dependency applies, None otherwise
        """
        if self.vendorDependency and self.vendorLastUpdate:
            try:
                vendor_date = datetime.datetime.strptime(self.vendorLastUpdate, "%Y-%m-%dT%H:%M:%S")
                days_since_vendor = (current_date - vendor_date).days
                return days_since_vendor > threshold_days
            except ValueError:
                pass
        return None

    def _get_open_statuses(self) -> set:
        """
        Get the set of statuses considered open.

        Returns:
            Set of open status values
        """
        return {
            IssueStatus.Open,
            IssueStatus.Delayed,
            IssueStatus.PendingVerification,
            IssueStatus.VendorDependency,
            IssueStatus.PendingApproval,
        }

    def _is_accepted_risk(self) -> bool:
        """
        Check if issue is accepted as residual risk.

        Returns:
            True if accepted as residual risk
        """
        return bool(self.falsePositive or self.operationalRequirement or self.deviationRationale)

    def _get_detection_context(self, current_date: datetime.datetime) -> Optional[tuple]:
        """
        Get detection date context for POAM calculation.

        Args:
            current_date: Current date for calculation

        Returns:
            Tuple of (days_since_detection, is_scan, severity) or None if invalid
        """
        detection_date_str = self.dateFirstDetected or self.dateCreated
        if not detection_date_str:
            return None

        detection_date = self._parse_detection_date(detection_date_str)
        if not detection_date:
            return None

        days_since_detection = (current_date - detection_date).days
        scan_sources = {"Vulnerability Assessment", "FDCC/USGCB", "Penetration Test"}
        is_scan = self.identification in scan_sources

        severity = (
            IssueSeverity(self.severityLevel)
            if self.severityLevel in {s.value for s in IssueSeverity}
            else IssueSeverity.NotAssigned
        )

        return (days_since_detection, is_scan, severity)

    def _apply_standard_logic(
        self,
        standard: str,
        severity: IssueSeverity,
        is_scan: bool,
        days_since_detection: int,
        threshold_days: int,
        open_statuses: set,
        current_date: datetime.datetime,
    ) -> bool:
        """
        Apply standard-specific POAM logic.

        Args:
            standard: 'fedramp' or 'nist'
            severity: Issue severity level
            is_scan: Whether this is a scan-based issue
            days_since_detection: Days since detection
            threshold_days: Threshold for overdue status
            open_statuses: Set of open statuses
            current_date: Current date for calculation

        Returns:
            POAM status
        """
        if standard == "fedramp":
            is_poam = self._apply_fedramp_logic(severity, is_scan, days_since_detection, threshold_days, open_statuses)
            vendor_status = self._check_vendor_dependency(current_date, threshold_days)
            return vendor_status if vendor_status is not None else is_poam
        return self.status in open_statuses

    # New method to determine and set isPoam based on NIST/FedRAMP criteria
    def set_is_poam(
        self,
        config: Optional[Dict[str, Any]] = None,
        standard: str = "fedramp",
        current_date: Optional[datetime.datetime] = None,
    ) -> None:
        """
        Sets the isPoam field based on NIST 800-53 or FedRAMP criteria, preserving historical POAM status.

        Criteria:
        - Preserves isPoam=True for imported data, even if closed, for reporting purposes.
        - For new issues:
          - Skips if false positive, operational requirement, or deviation rationale exists.
          - FedRAMP: High/Critical issues are POAMs if open; scan-based issues are POAMs if overdue; non-scan issues are POAMs if open.
          - NIST: POAM for any open deficiency unless accepted as residual risk.
          - Uses config thresholds (e.g., {'critical': 30, 'high': 90, 'medium': 90, 'low': 365, 'status': 'Open'}).

        Args:
            config: Optional dictionary with severity thresholds and status from init.yaml.
                    Defaults to FedRAMP: {'critical': 30, 'high': 30, 'medium': 90, 'low': 180, 'status': 'Open'}.
                    For NIST, uses {'critical': 30, 'high': 90, 'medium': 90, 'low': 180, 'status': 'Open'}.
            standard: 'fedramp' (default) or 'nist'.
            current_date: Optional datetime for calculation (defaults to current time).

        Returns:
            None: Sets the isPoam attribute directly.
        """
        current_date = current_date or datetime.datetime.now()

        if self.isPoam or self._is_accepted_risk():
            self.isPoam = False if self._is_accepted_risk() else True
            return

        config = config or self._get_default_config(standard)
        threshold_days = self._calculate_threshold_days(config)

        detection_context = self._get_detection_context(current_date)
        if not detection_context:
            self.isPoam = False
            return

        days_since_detection, is_scan, severity = detection_context
        open_statuses = self._get_open_statuses()

        self.isPoam = self._apply_standard_logic(
            standard, severity, is_scan, days_since_detection, threshold_days, open_statuses, current_date
        )

        if "status" in config:
            self.isPoam = self.isPoam and self.status == config["status"]


def build_issue_dict_from_query(a: Dict[str, Any]) -> Dict[str, Any]:
    """
    This method takes in a single record from the graphQL query and reformat
    it into an issue dict.

    :param Dict[str, Any] a: A single record returned from the query
    :return: Reformatted dict for the data needs
    :rtype: Dict[str, Any]
    """
    modeled_item = {}
    modeled_item["id"] = a["id"]
    modeled_item["issueOwnerId"] = (
        (
            str(a["issueOwner"]["lastName"]).strip()
            + ", "
            + str(a["issueOwner"]["firstName"]).strip()
            + " ("
            + str(a["issueOwner"]["userName"]).strip()
            + ")"
        )
        if a["issueOwner"]
        else "None"
    )
    modeled_item["title"] = a["title"]
    modeled_item["dateCreated"] = reformat_str_date(a["dateCreated"])
    modeled_item["isPoam"] = a["isPoam"]
    modeled_item["description"] = a["description"] if a["description"] else "None"
    modeled_item["severityLevel"] = a["severityLevel"]
    modeled_item["costEstimate"] = a["costEstimate"] if a["costEstimate"] and a["costEstimate"] != "None" else 0.00
    modeled_item["levelOfEffort"] = a["levelOfEffort"] if a["levelOfEffort"] and a["levelOfEffort"] != "None" else 0
    modeled_item["dueDate"] = reformat_str_date(a["dueDate"])
    modeled_item["identification"] = a["identification"] if a["identification"] else "None"
    modeled_item["status"] = a["status"] if a["status"] else "None"
    modeled_item["dateCompleted"] = reformat_str_date(a["dateCompleted"]) if a["dateCompleted"] else ""
    modeled_item["activitiesObserved"] = blank_if_empty(a, "activitiesObserved")
    modeled_item["failuresObserved"] = blank_if_empty(a, "failuresObserved")
    modeled_item["requirementsViolated"] = blank_if_empty(a, "requirementsViolated")
    modeled_item["safetyImpact"] = blank_if_empty(a, "safetyImpact")
    modeled_item["securityImpact"] = blank_if_empty(a, "securityImpact")
    modeled_item["qualityImpact"] = blank_if_empty(a, "qualityImpact")
    modeled_item["securityChecks"] = blank_if_empty(a, "securityChecks")
    modeled_item["recommendedActions"] = blank_if_empty(a, "recommendedActions")
    return modeled_item


def blank_if_empty(data: dict, field: str) -> str:
    """
    This method will return the value of the specified field from the passed dict if it exists. If
    it doesn't, an empty string will be returned.

    :param dict data: the data to be queried for the field
    :param str field: the field to return if it exists in the dict
    :return: str the field value or an empty string
    :rtype: str
    """
    return data.get(field, "")
