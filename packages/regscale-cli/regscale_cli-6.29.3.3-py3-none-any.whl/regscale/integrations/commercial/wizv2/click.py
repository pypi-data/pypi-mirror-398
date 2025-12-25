#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates Wiz.io into RegScale"""

# standard python imports
import logging
from typing import Optional

import click

from regscale.integrations.commercial.wizv2.variables import WizVariables
from regscale.models import regscale_id
from regscale.models.app_models.click import regscale_ssp_id, regscale_module

logger = logging.getLogger("regscale")


@click.group()  # type: ignore
def wiz():
    """Integrates continuous monitoring data from Wiz.io."""


@wiz.command()
@click.option("--client_id", default=None, hide_input=False, required=False)  # type: ignore
@click.option("--client_secret", default=None, hide_input=True, required=False)  # type: ignore
def authenticate(client_id, client_secret):
    """Authenticate to Wiz."""
    from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate

    wiz_authenticate(client_id, client_secret)


@wiz.command()
@click.option(
    "--wiz_project_id",
    "-p",
    required=False,
    type=str,
    help="Comma Seperated list of one or more Wiz project ids to pull inventory for.",
)
@regscale_ssp_id(
    help="RegScale SSP ID to push inventory to in RegScale.",
)
@click.option(
    "--client_id",
    "-ci",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(
    "--client_secret",
    "-cs",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(
    "--filter_by_override",
    "-f",
    default=None,
    type=str,
    required=False,
    help="""Filter by override to use for pulling inventory you can use one or more of the following.
    IE: --filter_by='{projectId: ["1234"], type: ["VIRTUAL_MACHINE"], subscriptionExternalId: ["1234"],
         providerUniqueId: ["1234"], updatedAt: {after: "2023-06-14T14:07:06Z"}, search: "test-7"}' """,
)
def inventory(
    wiz_project_id: str,
    regscale_ssp_id: int,
    client_id: str,
    client_secret: str,
    filter_by_override: Optional[str] = None,
) -> None:
    """Process inventory from Wiz and create assets in RegScale."""
    from regscale.integrations.commercial.wizv2.scanner import WizVulnerabilityIntegration

    if client_secret is None:
        client_secret = WizVariables.wizClientSecret
    if client_id is None:
        client_id = WizVariables.wizClientId

    scanner = WizVulnerabilityIntegration(plan_id=regscale_ssp_id)
    scanner.sync_assets(
        plan_id=regscale_ssp_id,
        filter_by_override=filter_by_override or WizVariables.wizInventoryFilterBy,  # type: ignore
        client_id=client_id,  # type: ignore
        client_secret=client_secret,  # type: ignore
        wiz_project_id=wiz_project_id,
    )


@wiz.command()
@click.option(
    "--wiz_project_id",
    "-p",
    prompt="Enter the project ID for Wiz",
    default=None,
    required=False,
)
@regscale_ssp_id(help="RegScale will create and update issues as children of this record.")
@click.option(
    "--client_id",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(
    "--client_secret",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@click.option(
    "--filter_by_override",
    "-f",
    default=None,
    type=str,
    required=False,
    help="""Filter by override to use for pulling inventory you can use one or more of the following.
    IE: --filter_by='{projectId: ["1234"], type: ["VIRTUAL_MACHINE"], subscriptionExternalId: ["1234"],
         providerUniqueId: ["1234"], updatedAt: {after: "2023-06-14T14:07:06Z"}, search: "test-7"}' """,
)
def issues(
    wiz_project_id: str,
    regscale_ssp_id: int,
    client_id: str,
    client_secret: str,
    filter_by_override: Optional[str] = None,
) -> None:
    """
    Process Issues from Wiz into RegScale
    """
    from regscale.core.app.utils.app_utils import check_license
    from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate
    from regscale.integrations.commercial.wizv2.issue import WizIssue
    import json

    if client_secret is None:
        client_secret = WizVariables.wizClientSecret
    if client_id is None:
        client_id = WizVariables.wizClientId

    check_license()
    wiz_authenticate(client_id, client_secret)
    filter_by = json.loads(filter_by_override or WizVariables.wizIssueFilterBy.replace("\n", ""))

    filter_by["project"] = wiz_project_id

    scanner = WizIssue(plan_id=regscale_ssp_id)
    scanner.sync_findings(
        plan_id=regscale_ssp_id,
        filter_by_override=filter_by,  # Pass the processed dict with project ID
        client_id=client_id,  # type: ignore
        client_secret=client_secret,  # type: ignore
        wiz_project_id=wiz_project_id,
    )


@wiz.command(name="attach_sbom")
@click.option(  # type: ignore
    "--client_id",
    "-ci",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(  # type: ignore
    "--client_secret",
    "-cs",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@regscale_ssp_id(help="RegScale will create and update issues as children of this record.")
@click.option("--report_id", "-r", help="Wiz Report ID", required=True)  # type: ignore
@click.option(  # type: ignore
    "--standard", "-s", help="SBOM standard CycloneDX or SPDX default is CycloneDX", default="CycloneDX", required=False
)
def attach_sbom(
    client_id,
    client_secret,
    regscale_ssp_id: str,
    report_id: str,
    standard="CycloneDX",
):
    """Download SBOMs from a Wiz report by ID and add them to the corresponding RegScale assets."""
    from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate
    from regscale.integrations.commercial.wizv2.utils import fetch_sbom_report

    if client_secret is None:
        client_secret = WizVariables.wizClientSecret
    if client_id is None:
        client_id = WizVariables.wizClientId

    wiz_authenticate(
        client_id=client_id,
        client_secret=client_secret,
    )
    fetch_sbom_report(
        report_id,
        parent_id=regscale_ssp_id,
        report_file_name="sbom_report",
        report_file_extension="zip",
        standard=standard,
    )


@wiz.command()
@click.option(  # type: ignore
    "--wiz_project_id",
    "-p",
    prompt="Enter the project ID for Wiz",
    default=None,
    required=False,
)
@regscale_ssp_id(help="RegScale will create and update issues as children of this record.")
@click.option(  # type: ignore
    "--client_id",
    "-ci",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(  # type: ignore
    "--client_secret",
    "-cs",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@click.option(  # type: ignore
    "--filter_by_override",
    "-f",
    default=None,
    type=str,
    required=False,
    help="""Filter by override to use for pulling inventory you can use one or more of the following.
    IE: --filter_by='{projectId: ["1234"], type: ["VIRTUAL_MACHINE"], subscriptionExternalId: ["1234"],
         providerUniqueId: ["1234"], updatedAt: {after: "2023-06-14T14:07:06Z"}, search: "test-7"}' """,
)
def vulnerabilities(
    wiz_project_id: str,
    regscale_ssp_id: int,
    client_id: str,
    client_secret: str,
    filter_by_override: Optional[str] = None,
):
    """Process vulnerabilities from Wiz"""
    from regscale.integrations.commercial.wizv2.scanner import WizVulnerabilityIntegration

    if client_secret is None:
        client_secret = WizVariables.wizClientSecret
    if client_id is None:
        client_id = WizVariables.wizClientId

    scanner = WizVulnerabilityIntegration(plan_id=regscale_ssp_id)
    scanner.sync_findings(
        plan_id=regscale_ssp_id,
        filter_by_override=filter_by_override,  # type: ignore
        client_id=client_id,  # type: ignore
        client_secret=client_secret,  # type: ignore
        wiz_project_id=wiz_project_id,
    )


@wiz.command(name="add_report_evidence")
@click.option(  # type: ignore
    "--client_id",
    "-ci",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(  # type: ignore
    "--client_secret",
    "-cs",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@click.option("--evidence_id", "-e", help="Wiz Evidence ID", required=True, type=int)  # type: ignore
@click.option("--report_id", "-r", help="Wiz Report ID", required=True)  # type: ignore
@click.option(
    "--report_file_name", "-n", help="Report file name", default="evidence_report", required=False
)  # type: ignore
@click.option(
    "--report_file_extension", "-e", help="Report file extension", default="csv", required=False
)  # type: ignore
def add_report_evidence(
    client_id,
    client_secret,
    evidence_id: int,
    report_id: str,
    report_file_name: str = "evidence_report",
    report_file_extension: str = "csv",
):
    """Download a Wiz report by ID and Attach to Evidence locker"""
    from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate
    from regscale.integrations.commercial.wizv2.utils import fetch_report_by_id

    if client_secret is None:
        client_secret = WizVariables.wizClientSecret
    if client_id is None:
        client_id = WizVariables.wizClientId

    wiz_authenticate(
        client_id=client_id,
        client_secret=client_secret,
    )
    fetch_report_by_id(
        report_id,
        parent_id=evidence_id,
        report_file_name=report_file_name,
        report_file_extension=report_file_extension,
    )


@wiz.command(
    "sync_compliance",
    deprecated=True,
    help="[BETA] This command shows an experimental feature. Use with caution. Use compliance report instead for Compliance sync from Wiz.",
)
@click.option(  # type: ignore
    "--wiz_project_id",
    "-p",
    prompt="Enter the Wiz project ID",
    help="Enter the Wiz Project ID for policy compliance sync.",
    required=True,
)
@regscale_id(help="RegScale will create and update control assessments as children of this record.")
@regscale_module(required=True, default="securityplans", prompt=False)
@click.option(  # type: ignore
    "--client_id",
    "-i",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(  # type: ignore
    "--client_secret",
    "-s",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@click.option(  # type: ignore
    "--framework_id",
    "-f",
    help=(
        "Wiz framework ID or shorthand (e.g., 'nist', 'aws', 'wf-id-4'). "
        "Use --list-frameworks to see options. Default: wf-id-4 (NIST SP 800-53 Rev 5)"
    ),
    default="wf-id-4",
    required=False,
)
@click.option(  # type: ignore
    "--list-frameworks",
    "-lf",
    is_flag=True,
    help="List all available framework options and shortcuts",
    default=False,
)
@click.option(  # type: ignore
    "--create-issues/--no-create-issues",
    "-ci/-ni",
    default=True,
    help="Create issues for failed policy assessments (default: enabled)",
)
@click.option(  # type: ignore
    "--update-control-status/--no-update-control-status",
    "-ucs/-nucs",
    default=True,
    help="Update control implementation status based on assessment results (default: enabled)",
)
@click.option(  # type: ignore
    "--create-poams/--no-create-poams",
    "-cp/-ncp",
    default=False,
    help="Mark created issues as POAMs (default: disabled)",
)
@click.option(  # type: ignore
    "--refresh/--no-refresh",
    "-r/-nr",
    default=False,
    help="Force refresh and ignore cached data (default: use cache if available)",
)
@click.option(  # type: ignore
    "--cache-duration",
    "-cd",
    type=click.INT,
    default=1440,
    help="Cache duration in minutes - reuse cached data if newer than this (default: 1440 minutes / 1 day)",
)
def sync_compliance(
    wiz_project_id,
    regscale_id,
    regscale_module,
    client_id,
    client_secret,
    framework_id,
    list_frameworks,
    create_issues,
    update_control_status,
    create_poams,
    refresh,
    cache_duration,
):
    """
    Sync policy compliance assessments from Wiz to RegScale.

    This command now uses CSV compliance reports from Wiz instead of GraphQL API.
    It creates:
    - Control assessments based on policy compliance results
    - Issues for failed policy assessments (if --create-issues enabled)
    - Updates to control implementation status (if --update-control-status enabled)

    NOTE: This command is deprecated. Use 'compliance_report' command instead.
    """
    click.echo("⚠️  sync_compliance is deprecated and now uses compliance_report implementation.")
    click.echo("    Consider using 'regscale wiz compliance_report' directly for future use.\n")

    # Handle --list-frameworks flag (no longer supported, inform user)
    if list_frameworks:
        click.echo("❌  --list-frameworks is no longer supported in the deprecated sync_compliance command.")
        click.echo("    Please use 'regscale wiz compliance_report' instead.\n")
        return

    # Use environment variables if not provided
    if client_secret is None or client_secret == "":
        client_secret = WizVariables.wizClientSecret
    if client_id is None or client_id == "":
        client_id = WizVariables.wizClientId

    # Import compliance_report processor instead of GraphQL-based integration
    from regscale.integrations.commercial.wizv2.compliance_report import WizComplianceReportProcessor

    # Create processor with similar options to compliance_report command
    processor = WizComplianceReportProcessor(
        plan_id=regscale_id,
        wiz_project_id=wiz_project_id,
        client_id=client_id,
        client_secret=client_secret,
        regscale_module=regscale_module,
        create_poams=create_poams,
        create_issues=create_issues,
        update_control_status=update_control_status,
        report_file_path=None,  # Will create new report
        force_fresh_report=refresh,  # Map --refresh to force_fresh_report
        reuse_existing_reports=not refresh,  # Inverse of refresh
        bypass_control_filtering=True,  # Enable for performance
    )

    # Process the compliance report using new ComplianceIntegration pattern
    processor.process_compliance_sync()


@wiz.command(name="compliance_report")
@click.option(
    "--wiz_project_id",
    "-p",
    prompt="Enter the Wiz project ID",
    help="Enter the Wiz Project ID for compliance report processing.",
    required=True,
)
@regscale_id(help="RegScale will create and update control assessments as children of this record.")
@regscale_module(required=True, default="securityplans", prompt=False)
@click.option(
    "--client_id",
    "-i",
    help="Wiz Client ID, or can be set as environment variable wizClientId",
    default=None,
    hide_input=False,
    required=False,
)
@click.option(
    "--client_secret",
    "-s",
    help="Wiz Client Secret, or can be set as environment variable wizClientSecret",
    default=None,
    hide_input=True,
    required=False,
)
@click.option(
    "--report_file_path",
    "-f",
    help="Path to existing CSV compliance report file (optional - will create new report if not provided)",
    default=None,
    required=False,
)
@click.option(
    "--create-issues/--no-create-issues",
    "-ci/-ni",
    default=True,
    help="Create issues for failed compliance assessments (default: enabled)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    "-ucs/-nucs",
    default=True,
    help="Update control implementation status based on assessment results (default: enabled)",
)
@click.option(
    "--create-poams/--no-create-poams",
    "-cp/-ncp",
    default=False,
    help="Mark created issues as POAMs (default: disabled)",
)
@click.option(
    "--reuse-existing-reports/--no-reuse-existing-reports",
    "-rer/-nrer",
    default=True,
    help="Reuse existing Wiz compliance reports instead of creating new ones (default: enabled)",
)
@click.option(
    "--force-fresh-report/--no-force-fresh-report",
    "-ffr/-nffr",
    default=False,
    help="Force creation of a fresh compliance report, ignoring existing reports (default: disabled)",
)
def compliance_report(
    wiz_project_id,
    regscale_id,
    regscale_module,
    client_id,
    client_secret,
    report_file_path,
    create_issues,
    update_control_status,
    create_poams,
    reuse_existing_reports,
    force_fresh_report,
):
    """
    Process Wiz compliance reports and create assessments in RegScale.

    This command can either:
    1. Create a new compliance report from Wiz and process it
    2. Process an existing compliance report CSV file

    The command will:
    - Parse compliance assessment data from CSV format
    - Create control assessments based on compliance results
    - Create issues for failed compliance assessments (if --create-issues enabled)
    - Update control implementation status (if --update-control-status enabled)
    - Support POAM creation for compliance issues

    REPORT MANAGEMENT:
    By default, the command will look for existing compliance reports in Wiz for the
    specified project and rerun them instead of creating new ones. This prevents the
    accumulation of duplicate reports in Wiz. Use --no-reuse-existing-reports to
    always create new reports, or --force-fresh-report to force a new report even
    when reuse is enabled.
    """
    from regscale.integrations.commercial.wizv2.compliance_report import WizComplianceReportProcessor

    # Use environment variables if not provided or empty
    if not client_secret:
        client_secret = WizVariables.wizClientSecret
    if not client_id:
        client_id = WizVariables.wizClientId

    # Create and run the compliance report processor
    # Enable bypass_control_filtering by default for performance with large control sets
    processor = WizComplianceReportProcessor(
        plan_id=regscale_id,
        wiz_project_id=wiz_project_id,
        client_id=client_id,
        client_secret=client_secret,
        regscale_module=regscale_module,
        create_poams=create_poams,
        create_issues=create_issues,
        update_control_status=update_control_status,
        report_file_path=report_file_path,
        bypass_control_filtering=True,  # Bypass filtering for performance with large control sets
        reuse_existing_reports=reuse_existing_reports,
        force_fresh_report=force_fresh_report,
    )

    # Process the compliance report using new ComplianceIntegration pattern
    processor.process_compliance_sync()
