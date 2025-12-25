# flake8: noqa E501
# pylint: disable=line-too-long

"""Vulnerabilities connector commands for the RegScale CLI"""

import click
from datetime import datetime
from regscale.models import regscale_ssp_id


@click.group()
def vulnerabilities() -> None:
    """Vulnerabilities connector commands for the RegScale CLI"""
    pass


@vulnerabilities.command(name="build-query")
@click.option(
    "--provider",
    required=False,
    help="Provider ID (e.g., vulnerabilities_armis_centrix). If not specified, starts interactive mode.",
)
@click.option("--validate", help="Validate a filter string against provider capabilities")
@click.option("--list-fields", is_flag=True, default=False, help="List all available fields for the provider")
def build_query(provider, validate, list_fields):
    """
    Build and validate filter queries for Vulnerabilities connectors.

    Examples:
        # Build a filter query
        regscale vulnerabilities build-query

        # List all fields for a specific provider
        regscale vulnerabilities build-query --provider vulnerabilities_armis_centrix --list-fields

        # Validate a filter string
        regscale vulnerabilities build-query --provider vulnerabilities_armis_centrix --validate "device.ip[eq]192.168.1.1"
    """
    from regscale.integrations.commercial.synqly.query_builder import handle_build_query

    handle_build_query("vulnerabilities", provider, validate, list_fields)


@vulnerabilities.command(name="sync_crowdstrike")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Crowdstrike",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Crowdstrike",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
@click.option(
    "--url",
    type=click.STRING,
    help="Base URL for the CrowdStrike Falcon® Spotlight API.",
    required=False,
)
def sync_crowdstrike(
    regscale_ssp_id: int,
    minimum_severity_filter: str,
    scan_date: datetime,
    all_scans: bool,
    asset_filter: str,
    url: str,
) -> None:
    """Sync Vulnerabilities from Crowdstrike to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_crowdstrike = Vulnerabilities("crowdstrike")
    vulnerabilities_crowdstrike.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
        url=url,
    )


@vulnerabilities.command(name="sync_nucleus")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Nucleus",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans", help="Whether to sync all vulnerabilities from Nucleus", required=False, is_flag=True, default=False
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_nucleus(
    regscale_ssp_id: int, minimum_severity_filter: str, scan_date: datetime, all_scans: bool, asset_filter: str
) -> None:
    """Sync Vulnerabilities from Nucleus to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_nucleus = Vulnerabilities("nucleus")
    vulnerabilities_nucleus.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
    )


@vulnerabilities.command(name="sync_qualys_cloud")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Qualys Cloud",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Qualys Cloud",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_qualys_cloud(
    regscale_ssp_id: int, minimum_severity_filter: str, scan_date: datetime, all_scans: bool, asset_filter: str
) -> None:
    """Sync Vulnerabilities from Qualys Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_qualys_cloud = Vulnerabilities("qualys_cloud")
    vulnerabilities_qualys_cloud.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
    )


@vulnerabilities.command(name="sync_rapid7_insight_cloud")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Rapid7 Insight Cloud",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Rapid7 Insight Cloud",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_rapid7_insight_cloud(
    regscale_ssp_id: int, minimum_severity_filter: str, scan_date: datetime, all_scans: bool, asset_filter: str
) -> None:
    """Sync Vulnerabilities from Rapid7 Insight Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_rapid7_insight_cloud = Vulnerabilities("rapid7_insight_cloud")
    vulnerabilities_rapid7_insight_cloud.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
    )


@vulnerabilities.command(name="sync_servicenow_vr")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Servicenow Vr",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Servicenow Vr",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_servicenow_vr(
    regscale_ssp_id: int, minimum_severity_filter: str, scan_date: datetime, all_scans: bool, asset_filter: str
) -> None:
    """Sync Vulnerabilities from Servicenow Vr to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_servicenow_vr = Vulnerabilities("servicenow_vr")
    vulnerabilities_servicenow_vr.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
    )


@vulnerabilities.command(name="sync_tanium_cloud")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Tanium Cloud",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Tanium Cloud",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_tanium_cloud(
    regscale_ssp_id: int, minimum_severity_filter: str, scan_date: datetime, all_scans: bool, asset_filter: str
) -> None:
    """Sync Vulnerabilities from Tanium Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_tanium_cloud = Vulnerabilities("tanium_cloud")
    vulnerabilities_tanium_cloud.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
    )


@vulnerabilities.command(name="sync_tenable_cloud")
@regscale_ssp_id()
@click.option(
    "--minimum_severity_filter",
    "-s",
    help="Minimum severity of the vulnerabilities to sync. (Options: critical, high, medium, low, info), e.g. providing high will sync all vulnerabilities with a severity of high and critical.",
    required=False,
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default=None,
)
@click.option(
    "--scan_date",
    help="The date of the scan to sync vulnerabilities from Tenable Cloud",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
)
@click.option(
    "--all_scans",
    help="Whether to sync all vulnerabilities from Tenable Cloud",
    required=False,
    is_flag=True,
    default=False,
)
@click.option(
    "--asset_filter",
    help='STRING: Apply filters to asset queries. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
@click.option(
    "--url",
    type=click.STRING,
    help="Base URL for the Tenable Cloud API.",
    required=False,
)
def sync_tenable_cloud(
    regscale_ssp_id: int,
    minimum_severity_filter: str,
    scan_date: datetime,
    all_scans: bool,
    asset_filter: str,
    url: str,
) -> None:
    """Sync Vulnerabilities from Tenable Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Vulnerabilities

    vulnerabilities_tenable_cloud = Vulnerabilities("tenable_cloud")
    vulnerabilities_tenable_cloud.run_sync(
        regscale_ssp_id=regscale_ssp_id,
        minimum_severity_filter=minimum_severity_filter,
        scan_date=scan_date,
        all_scans=all_scans,
        filter=asset_filter.split(";") if asset_filter else [],
        url=url,
    )


# pylint: enable=line-too-long
