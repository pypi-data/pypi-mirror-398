#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RegScale SonarCloud Integration"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import click
import requests  # type: ignore[import-untyped]

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import (
    create_progress_object,
    days_between,
    error_and_exit,
    get_current_datetime,
)
from regscale.models import regscale_id, regscale_module
from regscale.models.regscale_models.assessment import Assessment
from regscale.models.regscale_models.issue import Issue

logger = logging.getLogger("regscale")

# Constants
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def get_sonarcloud_results(
    config: dict, organization: Optional[str] = None, branch: Optional[str] = None, project_key: Optional[str] = None
) -> list[list[dict]]:
    """
    Retrieve Sonarcloud Results from the Sonarcloud.io API

    :param dict config: RegScale CLI configuration
    :param Optional[str] organization: Organization name to filter results, defaults to None
    :param Optional[str] branch: Branch name to filter results, defaults to None
    :param Optional[str] project_key: SonarCloud Project Key, defaults to None
    :return: json response data from API GET request
    :rtype: list[list[dict]]
    """
    # create an empty list to hold multiple pages of data
    complete = []
    # api endpoint
    url = urljoin(config["sonarUrl"], "/api/issues/search")
    # SONAR_TOKEN from Sonarcloud
    token = config["sonarToken"]
    # arguments to pass to the API call
    params = {
        "statuses": "OPEN, CONFIRMED, REOPENED",
        "ps": 500,
    }
    if organization and project_key:
        params["componentKeys"] = project_key
    if organization:
        params["organization"] = organization
    if branch:
        params["branch"] = branch
    if project_key:
        params["projectKeys"] = project_key
    # GET request pulls in data to check results size
    logger.info("Fetching issues from SonarCloud/Qube...")
    r = requests.get(url, auth=(str(token), ""), params=params)
    if r.status_code != 200:
        error_and_exit(f"Sonarcloud API call failed with status code {r.status_code}: {r.reason}\n{r.text}")
    # if the status code does not equal 200
    if r and not r.ok:
        # exit the script gracefully
        error_and_exit(f"Sonarcloud API call failed please check the configuration\n{r.status_code}: {r.text}")
    # pull in response data to a dictionary
    data = r.json()
    # find the total results number
    total = data["paging"]["total"]
    complete.extend(data.get("issues", []))
    # find the number of results in each result page
    size = data["paging"]["pageSize"]
    # calculate the number of pages to iterate through sequentially
    pages = math.ceil(total / size)
    # loop through each page number
    for i in range(2, pages + 1, 1):
        # parameters to pass to the API call
        params["p"] = str(i)
        # for each page make a GET request to pull in the data
        r = requests.get(url, auth=(str(token), ""), params=params)
        # pull in response data to a dictionary
        data = r.json()
        # extract only the issues from the data
        issues = data["issues"]
        # add each page to the total results page
        complete.extend(issues)
    # return the list of json response objects for use
    logger.info(f"Retrieved {len(complete)}/{total} issue(s) from SonarCloud/Qube.")
    return complete


def build_data(
    api: Api, organization: Optional[str] = None, branch: Optional[str] = None, project_key: Optional[str] = None
) -> list[dict]:
    """
    Build vulnerability alert data list

    :param Api api: API object
    :param Optional[str] organization: Organization name to filter results, defaults to None
    :param Optional[str] branch: Branch name to filter results, defaults to None
    :param Optional[str] project_key: SonarCloud Project Key, defaults to None
    :return: vulnerability data list
    :rtype: list[dict]
    """
    # execute GET request
    data = get_sonarcloud_results(config=api.config, organization=organization, branch=branch, project_key=project_key)
    # create empty list to hold json response dicts
    vulnerability_data_list = []
    # loop through the lists in API response data
    for issue in data:
        # loop through the list of dicts in the API response data
        # format datetime stamp to use with days_between function
        create_date = issue["creationDate"][0:19] + "Z"
        # build vulnerability list
        vulnerability_data_list.append(
            {
                "key": issue["key"],
                "severity": issue["severity"],
                "component": issue["component"],
                "status": issue["status"],
                "message": issue["message"],
                "creationDate": issue["creationDate"][0:19],
                "updateDate": issue["updateDate"][0:19],
                "type": issue["type"],
                "days_elapsed": days_between(vuln_time=create_date),
            }
        )
    return vulnerability_data_list


def build_dataframes(sonar_data: list[dict]) -> str:
    """
    Build pandas dataframes from vulnerability alert data list

    :param list[dict] sonar_data: SonarCloud alerts and issues data
    :return: dataframe as an HTML table
    :rtype: str
    """
    import pandas as pd  # Optimize import performance

    df = pd.DataFrame(sonar_data)
    # sort dataframe by severity
    df.sort_values(by=["severity"], inplace=True)
    # reset and drop the index
    df.reset_index(drop=True, inplace=True)
    # convert the dataframe to an html table
    output = df.to_html(header=True, index=False, justify="center", border=1)
    return output


def create_alert_assessment(
    sonar_data: list[dict], api: Api, parent_id: Optional[int] = None, parent_module: Optional[str] = None
) -> Optional[int]:
    """
    Create Assessment containing SonarCloud alerts

    :param list[dict] sonar_data: SonarCloud alerts and issues data
    :param Api api: API object
    :param Optional[int] parent_id: Parent ID of the assessment, defaults to None
    :param Optional[str] parent_module: Parent module of the assessment, defaults to None
    :return: New Assessment ID, if created
    :rtype: Optional[int]
    """
    # create the assessment report HTML table
    df_output = build_dataframes(sonar_data)
    # build assessment model data
    assessment_data = Assessment(
        leadAssessorId=api.config["userId"],
        title="SonarCloud Code Scan Assessment",
        assessmentType="Control Testing",
        plannedStart=get_current_datetime(),
        plannedFinish=get_current_datetime(),
        assessmentReport=df_output,
        assessmentPlan="Complete the child issues created by the SonarCloud code scan results that were retrieved by the API. The assessment will fail if any high severity vulnerabilities has a days_elapsed value greater than or equal to 10 days.",
        createdById=api.config["userId"],
        dateCreated=get_current_datetime(),
        lastUpdatedById=api.config["userId"],
        dateLastUpdated=get_current_datetime(),
        status="In Progress",
    )
    if parent_id and parent_module:
        assessment_data.parentId = parent_id
        assessment_data.parentModule = parent_module
    # if assessmentResult is changed to Pass / Fail then status has to be
    # changed to complete and a completion date has to be passed
    for vulnerability in sonar_data:
        if vulnerability["severity"] == "CRITICAL" and vulnerability["days_elapsed"] >= 10:
            assessment_data.status = "Complete"
            assessment_data.actualFinish = get_current_datetime()
            assessment_data.assessmentResult = "Fail"

    # create a new assessment in RegScale
    if new_assessment := assessment_data.create():
        # log assessment creation result
        api.logger.debug("Assessment was created successfully")
        return new_assessment.id
    else:
        api.logger.debug("Assessment was not created")
        return None


def create_alert_issues(
    parent_id: Optional[int] = None,
    parent_module: Optional[str] = None,
    organization: Optional[str] = None,
    branch: Optional[str] = None,
    project_key: Optional[str] = None,
) -> None:
    """
    Create child issues from the alert assessment

    :param Optional[int] parent_id: Parent ID record to associate the assessment to, defaults to None
    :param Optional[str] parent_module: Parent module to associate the assessment to, defaults to None
    :param Optional[str] organization: Organization name to filter results, defaults to None
    :param Optional[str] branch: Branch name to filter results, defaults to None
    :param Optional[str] project_key: SonarCloud Project Key, defaults to None
    :rtype: None
    """
    # set environment and application configuration
    app = Application()
    api = Api()
    sonar_data = build_data(api=api, organization=organization, branch=branch, project_key=project_key)
    # execute POST request and return new assessment ID
    assessment_id = create_alert_assessment(
        sonar_data=sonar_data, api=api, parent_id=parent_id, parent_module=parent_module
    )

    # create vulnerability data list
    # loop through each vulnerability alert in the list
    with create_progress_object() as progress:
        task = progress.add_task("Creating/updating issue(s) in RegScale...", total=len(sonar_data))
        for vulnerability in sonar_data:
            # create issue model
            issue_data = Issue(
                title="Sonarcloud Code Scan",  # Required
                dateCreated=get_current_datetime(DATETIME_FORMAT),
                description=vulnerability["message"],
                severityLevel=Issue.assign_severity(vulnerability["severity"]),  # Required
                dueDate=Issue.get_due_date(
                    severity=vulnerability["severity"].lower(), config=app.config, key="sonarcloud"
                ),
                identification="Code scan assessment",
                status="Open",
                assessmentId=assessment_id,
                parentId=parent_id or assessment_id,
                parentModule=parent_module or "assessments",
                sourceReport="SonarCloud/Qube",
                otherIdentifier=vulnerability["key"],
            )
            # log issue creation result
            if issue_data.create_or_update(bulk_create=True, bulk_update=True):
                logger.debug("Issue was created/updated successfully")
            else:
                logger.debug("Issue was not created.")
            progress.advance(task)
        Issue.bulk_save(progress)


# ============================================================================
# GitLab SAST Report Import Functions
# ============================================================================


def parse_gitlab_sast_file(file_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Parse a GitLab SAST report JSON file.

    :param Path file_path: Path to the GitLab SAST JSON file
    :return: Tuple of (vulnerabilities list, scan metadata dict)
    :rtype: tuple[list[dict[str, Any]], dict[str, Any]]
    :raises SystemExit: If file format is invalid or unsupported
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        error_and_exit(f"File not found: {file_path}")
    except json.JSONDecodeError as err:
        error_and_exit(f"Invalid JSON in file {file_path}: {err}")

    # Validate required fields for GitLab SAST format
    if "vulnerabilities" not in data:
        error_and_exit(f"Invalid GitLab SAST format: missing 'vulnerabilities' field in {file_path}")

    if "scan" not in data:
        error_and_exit(f"Invalid GitLab SAST format: missing 'scan' field in {file_path}")

    scan_info = data.get("scan", {})
    vulnerabilities = data.get("vulnerabilities", [])

    logger.info("Parsed GitLab SAST file: %d vulnerabilities found", len(vulnerabilities))

    return vulnerabilities, scan_info


def build_gitlab_sast_description(vulnerability: dict[str, Any]) -> str:
    """
    Build a comprehensive description from GitLab SAST vulnerability data.

    :param dict[str, Any] vulnerability: Single vulnerability from GitLab SAST file
    :return: Formatted description string
    :rtype: str
    """
    parts = []

    # Add message (brief summary)
    if message := vulnerability.get("message"):
        parts.append(message)

    # Add description (detailed explanation)
    if description := vulnerability.get("description"):
        parts.append("")
        parts.append(description)

    # Add location information
    location = vulnerability.get("location", {})
    if location:
        file_path = location.get("file", "")
        start_line = location.get("start_line")
        end_line = location.get("end_line")

        if file_path:
            location_str = f"Location: {file_path}"
            if start_line:
                if end_line and end_line != start_line:
                    location_str += f":{start_line}-{end_line}"
                else:
                    location_str += f":{start_line}"
            parts.append("")
            parts.append(location_str)

    # Add solution if available
    if solution := vulnerability.get("solution"):
        parts.append("")
        parts.append(f"Solution: {solution}")

    return "\n".join(parts)


def transform_gitlab_sast_to_internal(
    vulnerabilities: list[dict[str, Any]],
    scan_info: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Transform GitLab SAST vulnerabilities to internal format compatible
    with existing processing functions.

    :param list[dict[str, Any]] vulnerabilities: Raw vulnerabilities from GitLab SAST file
    :param dict[str, Any] scan_info: Scan metadata from file
    :return: List of vulnerabilities in internal format
    :rtype: list[dict[str, Any]]
    """
    # Extract scan timestamp - use end_time, falling back to start_time
    scan_time = scan_info.get("end_time") or scan_info.get("start_time") or get_current_datetime(DATETIME_FORMAT)

    # Normalize scan time format for days_between calculation
    # GitLab SAST format: "2025-10-08T14:44:26" (no Z suffix)
    if not scan_time.endswith("Z"):
        scan_time_for_days = scan_time + "Z"
    else:
        scan_time_for_days = scan_time

    # Extract scanner name for source report
    scanner_name = scan_info.get("scanner", {}).get("name") or scan_info.get("analyzer", {}).get("name") or "Unknown"

    internal_data = []
    for vuln in vulnerabilities:
        # Normalize severity to uppercase (GitLab uses mixed case: Critical, Medium, Low)
        severity = (vuln.get("severity") or "UNKNOWN").upper()

        # Build the internal format matching what build_data() produces
        internal_data.append(
            {
                "key": vuln.get("id", ""),
                "severity": severity,
                "component": vuln.get("location", {}).get("file", ""),
                "status": "OPEN",  # GitLab SAST files don't have status, assume open
                "message": vuln.get("message", ""),
                "creationDate": scan_time[:19],  # Truncate to match format
                "updateDate": scan_time[:19],
                "type": "VULNERABILITY",
                "days_elapsed": days_between(vuln_time=scan_time_for_days),
                # Additional fields for GitLab SAST
                "name": vuln.get("name", ""),
                "description": build_gitlab_sast_description(vuln),
                "scanner_name": scanner_name,
            }
        )

    return internal_data


def create_gitlab_sast_issues(
    file_path: Path,
    parent_id: Optional[int] = None,
    parent_module: Optional[str] = None,
) -> None:
    """
    Create assessment and child issues from a GitLab SAST report file.

    :param Path file_path: Path to the GitLab SAST JSON file
    :param Optional[int] parent_id: Parent ID record to associate the assessment to, defaults to None
    :param Optional[str] parent_module: Parent module to associate the assessment to, defaults to None
    :rtype: None
    """
    app = Application()

    # Parse and transform the GitLab SAST file
    vulnerabilities, scan_info = parse_gitlab_sast_file(file_path)
    sast_data = transform_gitlab_sast_to_internal(vulnerabilities, scan_info)

    if not sast_data:
        logger.warning("No vulnerabilities found in GitLab SAST file: %s", file_path)
        return

    # Extract scanner name for source report attribution
    source_report = f"{sast_data[0].get('scanner_name', 'Unknown')} (GitLab SAST)"

    # Create assessment using existing function
    assessment_id = create_alert_assessment(
        sonar_data=sast_data, api=Api(), parent_id=parent_id, parent_module=parent_module
    )

    # Create issues for each vulnerability
    with create_progress_object() as progress:
        task = progress.add_task("Creating/updating issue(s) in RegScale...", total=len(sast_data))
        for vuln in sast_data:
            Issue(
                title=vuln.get("name") or "GitLab SAST Finding",
                dateCreated=get_current_datetime(DATETIME_FORMAT),
                description=vuln.get("description") or vuln.get("message", ""),
                severityLevel=Issue.assign_severity(vuln["severity"]),
                dueDate=Issue.get_due_date(severity=vuln["severity"].lower(), config=app.config, key="sonarcloud"),
                identification="GitLab SAST Import",
                status="Open",
                assessmentId=assessment_id,
                parentId=parent_id or assessment_id,
                parentModule=parent_module or "assessments",
                sourceReport=source_report,
                otherIdentifier=vuln["key"],
            ).create_or_update(bulk_create=True, bulk_update=True)
            progress.advance(task)

        Issue.bulk_save(progress)

    logger.info("GitLab SAST import complete: %d issues processed from %s", len(sast_data), file_path)


@click.group()
def sonarcloud() -> None:
    """
    Sync alerts from SonarCloud API or import from GitLab SAST report files.
    """
    pass


@sonarcloud.command(name="sync_alerts")
@regscale_id(required=False, default=None)
@regscale_module(required=False, default=None)
@click.option(
    "--organization",
    "-o",
    type=click.STRING,
    help="Organization name to filter results, defaults to None",
    default=None,
)
@click.option("--branch", "-b", type=click.STRING, help="Branch name to filter results, defaults to None", default=None)
@click.option("--project_key", "-p", type=click.STRING, help="SonarCloud Project Key, defaults to None", default=None)
def create_alerts(
    regscale_id: Optional[int] = None,
    regscale_module: Optional[str] = None,
    organization: Optional[str] = None,
    branch: Optional[str] = None,
    project_key: Optional[str] = None,
) -> None:
    """
    Create a child assessment and child issues in RegScale from SonarCloud alerts.
    """
    create_alert_issues(
        parent_id=regscale_id,
        parent_module=regscale_module,
        organization=organization,
        branch=branch,
        project_key=project_key,
    )


@sonarcloud.command(name="import_gitlab_sast")
@click.option(
    "--file",
    "-f",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to GitLab SAST report JSON file",
)
@regscale_id(required=False, default=None)
@regscale_module(required=False, default=None)
def import_gitlab_sast(
    file_path: Path,
    regscale_id: Optional[int] = None,
    regscale_module: Optional[str] = None,
) -> None:
    """
    Import vulnerabilities from a GitLab SAST report JSON file.

    Creates an assessment and child issues in RegScale from the scan results.
    Supports GitLab SAST report format v15.0.0 from any compatible scanner
    (Checkmarx, Semgrep, SonarQube, etc.).

    Example:
        regscale sonarcloud import_gitlab_sast -f ./gl-sast-report.json --regscale_id 123
    """
    create_gitlab_sast_issues(
        file_path=file_path,
        parent_id=regscale_id,
        parent_module=regscale_module,
    )
