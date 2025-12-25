#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP CLI integration module.

This module provides Click commands for GCP Security Command Center integration:
- authenticate: Test GCP credentials and connection
- inventory: Export GCP inventory to JSON file
- sync_assets: Sync GCP assets to RegScale
- sync_findings: Sync SCC findings to RegScale
- sync_compliance: Sync compliance posture to RegScale
- collect_evidence: Collect evidence for controls
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from regscale.integrations.commercial.gcp.variables import (
    GcpVariables,
    GCP_SUPPORTED_FRAMEWORKS,
    GCP_DEFAULT_FINDING_SOURCES,
    GCP_VALID_EVIDENCE_MODES,
    GCP_VALID_SCAN_TYPES,
)

logger = logging.getLogger("regscale")

# Constants for log messages
LOG_MSG_USING_ENV_CREDENTIALS = "Using credentials from environment configuration"


@dataclass
class GCPCredentialConfig:
    """GCP credential configuration."""

    credentials_file: Optional[str] = None
    session_name: Optional[str] = None
    project_id: Optional[str] = None
    organization_id: Optional[str] = None
    folder_id: Optional[str] = None


@dataclass
class ComplianceSyncConfig:
    """Configuration for GCP SCC compliance sync."""

    regscale_id: int
    framework: str = "NIST800-53R5"
    create_issues: bool = True
    update_control_status: bool = True
    create_poams: bool = False


@dataclass
class EvidenceCollectionConfig:
    """Configuration for evidence collection."""

    regscale_ssp_id: int
    control_ids: Optional[List[str]] = None
    mode: str = "attachments"
    frequency_days: int = 30


def parse_labels(labels_string: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Parse label string into dictionary.

    Format: key1=value1,key2=value2

    :param Optional[str] labels_string: Comma-separated key=value pairs
    :return: Dictionary of label key-value pairs or None if input is empty
    :rtype: Optional[Dict[str, str]]
    """
    if not labels_string:
        return None

    label_dict = {}
    try:
        for label_pair in labels_string.split(","):
            if "=" not in label_pair:
                logger.warning("Invalid label format (missing '='): %s", label_pair)
                continue
            key, value = label_pair.split("=", 1)
            label_dict[key.strip()] = value.strip()
        return label_dict if label_dict else None
    except (ValueError, AttributeError) as e:
        logger.error("Error parsing labels: %s", e)
        raise click.ClickException("Invalid label format. Expected format: key1=value1,key2=value2")


def get_gcp_parent(scope: str, project_id: str, organization_id: str, folder_id: str) -> str:
    """
    Build GCP parent resource path based on scope.

    :param str scope: Scope type (project, organization, folder)
    :param str project_id: GCP project ID
    :param str organization_id: GCP organization ID
    :param str folder_id: GCP folder ID
    :return: GCP parent resource path
    :rtype: str
    """
    if scope == "organization":
        return f"organizations/{organization_id}"
    elif scope == "folder":
        return f"folders/{folder_id}"
    else:
        return f"projects/{project_id}"


@click.group(name="gcp")
def gcpv2():
    """GCP Security Command Center Integrations."""
    pass


# =============================================================================
# Authentication Commands
# =============================================================================


@gcpv2.command(name="authenticate")
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file. Defaults to gcpCredentials from init.yaml.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file for "
    "environments where file paths are not available (e.g., Airflow DAGs).",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
def authenticate(
    credentials_file: Optional[str] = None,
    credentials_json: Optional[str] = None,
    credentials_json_base64: Optional[str] = None,
) -> None:
    """
    Test GCP credentials and connection.

    This command verifies that GCP credentials are valid and can connect to GCP APIs.
    Credentials can be provided via (in order of precedence):
    - --credentials-json-base64: Base64-encoded JSON (recommended for Airflow)
    - --credentials-json: Raw JSON string
    - --credentials-file: Path to service account JSON key file
    - gcpCredentialsJsonBase64 in init.yaml
    - gcpCredentials in init.yaml (default)

    Examples:
        # Use default credentials from init.yaml
        regscale gcp authenticate

        # Use specific credentials file
        regscale gcp authenticate --credentials-file /path/to/service-account.json

        # Use base64-encoded credentials (recommended for Airflow DAGs)
        regscale gcp authenticate --credentials-json-base64 "eyJ0eXBlIjoi..."
    """
    try:
        from regscale.integrations.commercial.gcp.auth import (
            authenticate as gcp_authenticate,
            setup_credentials_from_json,
            ensure_gcp_credentials,
        )

        # Determine credentials source (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            creds_path = setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            logger.info("Using credentials from JSON content")
            creds_path = setup_credentials_from_json(credentials_json)
        elif credentials_file:
            creds_path = credentials_file
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
            logger.info("Using credentials file: %s", credentials_file)
        else:
            # Let ensure_gcp_credentials handle the fallback logic
            ensure_gcp_credentials()
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            if not creds_path:
                raise click.ClickException(
                    "No credentials provided. Use --credentials-json-base64, --credentials-json, "
                    "--credentials-file, or set gcpCredentialsJsonBase64/gcpCredentials in init.yaml"
                )

        success, message = gcp_authenticate(credentials_path=creds_path)

        if success:
            click.echo(click.style("\n[OK] GCP Authentication Successful!", fg="green", bold=True))
            click.echo(message)
            click.echo("\nYou can now use GCP integration commands.")
        else:
            click.echo(click.style("\n[FAILED] GCP Authentication Failed!", fg="red", bold=True))
            click.echo(message)
            raise click.ClickException("Authentication failed. Check your credentials.")

    except Exception as e:
        logger.error("Error during GCP authentication: %s", e, exc_info=True)
        raise click.ClickException(str(e))


# =============================================================================
# Inventory Commands
# =============================================================================


@gcpv2.group()
def inventory():
    """GCP resource inventory commands."""
    pass


@inventory.command(name="collect")
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, writable=True),
    default="artifacts/gcp/inventory.json",
    help="Output file path for inventory JSON. Default: artifacts/gcp/inventory.json",
)
@click.option(
    "--scope",
    type=click.Choice(GCP_VALID_SCAN_TYPES, case_sensitive=False),
    default="project",
    help="Scope for inventory collection: organization, folder, or project. Default: project",
)
@click.option(
    "--project-id",
    type=str,
    required=False,
    help="GCP project ID. Defaults to gcpProjectId from init.yaml.",
    envvar="GCP_PROJECT_ID",
)
@click.option(
    "--organization-id",
    type=str,
    required=False,
    help="GCP organization ID (for organization scope). Defaults to gcpOrganizationId from init.yaml.",
    envvar="GCP_ORGANIZATION_ID",
)
@click.option(
    "--folder-id",
    type=str,
    required=False,
    help="GCP folder ID (for folder scope). Defaults to gcpFolderId from init.yaml.",
    envvar="GCP_FOLDER_ID",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file.",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
@click.option(
    "--labels",
    type=str,
    required=False,
    help="Filter resources by labels (format: key1=value1,key2=value2). All labels must match.",
)
def collect_inventory(
    output_file: str,
    scope: str,
    project_id: Optional[str],
    organization_id: Optional[str],
    folder_id: Optional[str],
    credentials_file: Optional[str],
    credentials_json: Optional[str],
    credentials_json_base64: Optional[str],
    labels: Optional[str],
) -> None:
    """
    Collect GCP resource inventory.

    This command collects information about various GCP resources including:
    - Compute Engine instances and disks
    - Cloud Storage buckets
    - Cloud SQL instances
    - GKE clusters
    - VPCs and networking resources
    - IAM policies and service accounts
    - And more...

    The inventory is saved to a JSON file for later analysis or syncing to RegScale.

    Examples:
        # Collect project-level inventory
        regscale gcp inventory collect --project-id my-project

        # Collect organization-level inventory
        regscale gcp inventory collect --scope organization --organization-id 123456789

        # Collect with label filtering
        regscale gcp inventory collect --labels environment=prod,team=security

        # Specify output file
        regscale gcp inventory collect --output-file /tmp/gcp-inventory.json
    """
    try:
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials, setup_credentials_from_json

        logger.info("Collecting GCP inventory...")

        # Set credentials (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            setup_credentials_from_json(credentials_json)
        elif credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        ensure_gcp_credentials()

        # Resolve scope parameters from config if not provided
        project_id = project_id or str(GcpVariables.gcpProjectId)
        organization_id = organization_id or str(GcpVariables.gcpOrganizationId)
        folder_id = folder_id or str(GcpVariables.gcpFolderId)

        # Parse labels
        label_dict = parse_labels(labels)
        if label_dict:
            logger.info("Filtering resources by labels: %s", label_dict)

        # Get parent resource path
        parent = get_gcp_parent(scope, project_id, organization_id, folder_id)
        logger.info("Collecting inventory for scope: %s (%s)", scope, parent)

        # Collect inventory from all resource collectors
        inventory_data = _collect_all_inventory(
            parent=parent,
            credentials_path=credentials_file,
            project_id=project_id if scope == "project" else None,
            labels=label_dict,
        )

        # Calculate totals
        total_resources = sum(len(resources) for resources in inventory_data.values())
        logger.info("GCP inventory collected successfully. Found %d resource(s).", total_resources)

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write inventory to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(inventory_data, f, indent=2, default=str)

        logger.info("Inventory saved to %s", output_file)
        click.echo(f"\nInventory saved to {output_file}")
        click.echo(f"Total resources collected: {total_resources}")

    except Exception as e:
        logger.error("Error collecting GCP inventory: %s", e, exc_info=True)
        raise click.ClickException(str(e))


def _collect_all_inventory(
    parent: str,
    credentials_path: Optional[str] = None,
    project_id: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect inventory from all GCP resource collectors.

    :param str parent: GCP parent resource path
    :param Optional[str] credentials_path: Path to credentials file
    :param Optional[str] project_id: Project ID for filtering
    :param Optional[Dict[str, str]] labels: Labels for filtering
    :return: Dictionary of collected inventory by resource type
    :rtype: Dict[str, Any]
    """
    from regscale.integrations.commercial.gcp.inventory.resources import (
        ComputeCollector,
        StorageCollector,
        IAMCollector,
        NetworkingCollector,
        SecurityCollector,
    )

    inventory: Dict[str, Any] = {
        "metadata": {
            "parent": parent,
            "project_id": project_id,
            "labels_filter": labels,
        },
    }

    # List of collectors to use
    collectors = [
        ("compute", ComputeCollector),
        ("storage", StorageCollector),
        ("iam", IAMCollector),
        ("networking", NetworkingCollector),
        ("security", SecurityCollector),
    ]

    for name, collector_class in collectors:
        try:
            logger.info("Collecting %s resources...", name)
            collector = collector_class(
                parent=parent,
                credentials_path=credentials_path,
                project_id=project_id,
                labels=labels,
            )
            inventory[name] = collector.collect()
        except Exception as e:
            logger.warning("Error collecting %s resources: %s", name, e)
            inventory[name] = {"error": str(e)}

    return inventory


# =============================================================================
# Asset Sync Commands
# =============================================================================


@gcpv2.command(name="sync_assets")
@click.option(
    "--regscale_ssp_id",
    type=click.INT,
    help="The ID number from RegScale of the System Security Plan",
    prompt="Enter RegScale System Security Plan ID",
    required=True,
)
@click.option(
    "--scope",
    type=click.Choice(GCP_VALID_SCAN_TYPES, case_sensitive=False),
    default=None,
    help="Scope for asset collection. Defaults to gcpScanType from init.yaml.",
)
@click.option(
    "--project-id",
    type=str,
    required=False,
    help="GCP project ID. Defaults to gcpProjectId from init.yaml.",
    envvar="GCP_PROJECT_ID",
)
@click.option(
    "--organization-id",
    type=str,
    required=False,
    help="GCP organization ID. Defaults to gcpOrganizationId from init.yaml.",
    envvar="GCP_ORGANIZATION_ID",
)
@click.option(
    "--asset-types",
    type=str,
    required=False,
    help="Comma-separated list of asset types to sync (e.g., 'compute.googleapis.com/Instance,storage.googleapis.com/Bucket'). "
    "If not specified, all asset types are synced.",
)
@click.option(
    "--labels",
    type=str,
    required=False,
    help="Filter resources by labels (format: key1=value1,key2=value2). All labels must match.",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file.",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
@click.option(
    "--force-refresh",
    is_flag=True,
    default=False,
    help="Force refresh GCP inventory data, ignoring cached data even if still valid.",
)
def sync_assets(
    regscale_ssp_id: int,
    scope: Optional[str],
    project_id: Optional[str],
    organization_id: Optional[str],
    asset_types: Optional[str],
    labels: Optional[str],
    credentials_file: Optional[str],
    credentials_json: Optional[str],
    credentials_json_base64: Optional[str],
    force_refresh: bool,
) -> None:
    """
    Sync GCP assets to RegScale.

    This command collects GCP resources and creates/updates corresponding assets in RegScale:
    - Compute Engine instances
    - Cloud Storage buckets
    - Cloud SQL instances
    - GKE clusters
    - VPCs and networking resources
    - And more...

    Caching Behavior:
    GCP inventory data is cached for 8 hours in artifacts/gcp/inventory.json to improve performance.
    Use --force-refresh to bypass the cache and fetch fresh data from GCP.

    Filtering Options:
    Use --asset-types to filter specific GCP asset types.
    Use --labels to filter resources by GCP labels (format: env=prod,team=security).

    Examples:
        # Sync all assets from default project
        regscale gcp sync_assets --regscale_ssp_id 123

        # Sync specific asset types
        regscale gcp sync_assets --regscale_ssp_id 123 \\
            --asset-types compute.googleapis.com/Instance,storage.googleapis.com/Bucket

        # Sync with label filtering
        regscale gcp sync_assets --regscale_ssp_id 123 --labels environment=production
    """
    try:
        from regscale.integrations.commercial.gcp import GCPScannerIntegration
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials, setup_credentials_from_json

        logger.info("Starting GCP asset sync to RegScale...")

        # Set credentials (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            setup_credentials_from_json(credentials_json)
        elif credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        ensure_gcp_credentials()

        # Parse asset types filter
        asset_type_list = None
        if asset_types:
            asset_type_list = [t.strip() for t in asset_types.split(",")]
            logger.info("Filtering asset types: %s", asset_type_list)

        # Parse labels
        label_dict = parse_labels(labels)
        if label_dict:
            logger.info("Filtering resources by labels: %s", label_dict)

        if force_refresh:
            logger.info("Force refresh enabled - clearing cached inventory data")

        # Use the existing GCPScannerIntegration
        GCPScannerIntegration.sync_assets(plan_id=regscale_ssp_id)

        logger.info("GCP asset sync completed successfully.")

    except Exception as e:
        logger.error("Error syncing GCP assets: %s", e, exc_info=True)
        raise click.ClickException(str(e))


# =============================================================================
# Findings Sync Commands
# =============================================================================


@gcpv2.command(name="sync_findings")
@click.option(
    "--regscale_ssp_id",
    type=click.INT,
    help="The ID number from RegScale of the System Security Plan",
    prompt="Enter RegScale System Security Plan ID",
    required=True,
)
@click.option(
    "--severity-filter",
    type=str,
    default=None,
    help="Comma-separated list of severities to include (e.g., 'CRITICAL,HIGH,MEDIUM'). "
    "Defaults to gcpSeverityFilter from init.yaml.",
)
@click.option(
    "--sources",
    type=str,
    default=None,
    help="Comma-separated list of SCC finding sources to include "
    f"(e.g., '{','.join(GCP_DEFAULT_FINDING_SOURCES[:2])}'). "
    "Defaults to gcpFindingSources from init.yaml.",
)
@click.option(
    "--scope",
    type=click.Choice(GCP_VALID_SCAN_TYPES, case_sensitive=False),
    default=None,
    help="Scope for findings collection. Defaults to gcpScanType from init.yaml.",
)
@click.option(
    "--project-id",
    type=str,
    required=False,
    help="GCP project ID. Defaults to gcpProjectId from init.yaml.",
    envvar="GCP_PROJECT_ID",
)
@click.option(
    "--organization-id",
    type=str,
    required=False,
    help="GCP organization ID. Defaults to gcpOrganizationId from init.yaml.",
    envvar="GCP_ORGANIZATION_ID",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file.",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
@click.option(
    "--generate-evidence",
    is_flag=True,
    default=False,
    help="Generate evidence record for collected findings and link to SSP.",
)
@click.option(
    "--control-ids",
    type=str,
    default=None,
    help="Comma-separated list of control IDs to link evidence (e.g., '123,456,789').",
)
def sync_findings(
    regscale_ssp_id: int,
    severity_filter: Optional[str],
    sources: Optional[str],
    scope: Optional[str],
    project_id: Optional[str],
    organization_id: Optional[str],
    credentials_file: Optional[str],
    credentials_json: Optional[str],
    credentials_json_base64: Optional[str],
    generate_evidence: bool,
    control_ids: Optional[str],
) -> None:
    """
    Sync GCP Security Command Center findings to RegScale.

    This command fetches findings from GCP Security Command Center and creates/updates
    corresponding issues in RegScale. Findings include security misconfigurations,
    vulnerabilities, and threats detected by SCC.

    Finding Sources:
    - SECURITY_HEALTH_ANALYTICS: Misconfigurations and best practices
    - EVENT_THREAT_DETECTION: Detected threats and anomalies
    - CONTAINER_THREAT_DETECTION: Container security findings
    - WEB_SECURITY_SCANNER: Web application vulnerabilities

    Severity Filtering:
    Use --severity-filter to include only findings with specific severity levels.
    Valid values: CRITICAL, HIGH, MEDIUM, LOW

    Examples:
        # Sync all findings to a plan
        regscale gcp sync_findings --regscale_ssp_id 123

        # Sync only critical and high severity findings
        regscale gcp sync_findings --regscale_ssp_id 123 --severity-filter CRITICAL,HIGH

        # Sync findings from specific sources
        regscale gcp sync_findings --regscale_ssp_id 123 \\
            --sources SECURITY_HEALTH_ANALYTICS,EVENT_THREAT_DETECTION

        # Generate evidence records
        regscale gcp sync_findings --regscale_ssp_id 123 --generate-evidence
    """
    try:
        from regscale.integrations.commercial.gcp import GCPScannerIntegration
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials, setup_credentials_from_json

        logger.info("Starting GCP Security Command Center findings sync to RegScale...")

        # Set credentials (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            setup_credentials_from_json(credentials_json)
        elif credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        ensure_gcp_credentials()

        # Log filtering options
        if severity_filter:
            logger.info("Filtering by severity: %s", severity_filter)
        if sources:
            logger.info("Filtering by sources: %s", sources)

        # Parse control IDs if provided (will be used when evidence generation is enhanced)
        if control_ids:
            parsed_control_ids = [int(cid.strip()) for cid in control_ids.split(",")]
            logger.info("Control IDs for evidence linking: %s", parsed_control_ids)

        # Use the existing GCPScannerIntegration
        GCPScannerIntegration.sync_findings(plan_id=regscale_ssp_id)

        logger.info("GCP Security Command Center findings sync completed successfully.")

    except Exception as e:
        logger.error("Error syncing GCP SCC findings: %s", e, exc_info=True)
        raise click.ClickException(str(e))


# =============================================================================
# Compliance Sync Commands
# =============================================================================


@gcpv2.command(name="sync_compliance")
@click.option(
    "--regscale_ssp_id",
    type=click.INT,
    help="The ID number from RegScale of the System Security Plan",
    prompt="Enter RegScale System Security Plan ID",
    required=True,
)
@click.option(
    "--framework",
    type=click.Choice(GCP_SUPPORTED_FRAMEWORKS, case_sensitive=False),
    default="NIST800-53R5",
    help="Compliance framework to sync. Default: NIST800-53R5",
)
@click.option(
    "--scope",
    type=click.Choice(GCP_VALID_SCAN_TYPES, case_sensitive=False),
    default=None,
    help="Scope for compliance assessment. Defaults to gcpScanType from init.yaml.",
)
@click.option(
    "--project-id",
    type=str,
    required=False,
    help="GCP project ID. Defaults to gcpProjectId from init.yaml.",
    envvar="GCP_PROJECT_ID",
)
@click.option(
    "--organization-id",
    type=str,
    required=False,
    help="GCP organization ID. Defaults to gcpOrganizationId from init.yaml.",
    envvar="GCP_ORGANIZATION_ID",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file.",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for failed compliance controls. Default: True",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on compliance results. Default: True",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs. Default: False",
)
def sync_compliance(
    regscale_ssp_id: int,
    framework: str,
    scope: Optional[str],
    project_id: Optional[str],
    organization_id: Optional[str],
    credentials_file: Optional[str],
    credentials_json: Optional[str],
    credentials_json_base64: Optional[str],
    create_issues: bool,
    update_control_status: bool,
    create_poams: bool,
) -> None:
    """
    Sync GCP Security Command Center compliance posture to RegScale.

    This command fetches compliance assessment results from GCP SCC and:
    - Creates control assessments in RegScale based on SCC compliance findings
    - Creates issues for failed compliance controls (optional)
    - Updates control implementation status (optional)

    Supported Frameworks:
    - NIST800-53R5: NIST 800-53 Rev 5
    - CIS_GCP: CIS Google Cloud Platform Benchmark
    - FedRAMP: Federal Risk and Authorization Management Program
    - PCI-DSS: Payment Card Industry Data Security Standard
    - SOC2: Service Organization Control 2

    The integration maps GCP SCC findings to control IDs in the specified framework,
    allowing for automated compliance assessment updates in RegScale.

    Examples:
        # Sync NIST 800-53 compliance
        regscale gcp sync_compliance --regscale_ssp_id 123

        # Sync CIS GCP benchmark compliance
        regscale gcp sync_compliance --regscale_ssp_id 123 --framework CIS_GCP

        # Sync without creating issues
        regscale gcp sync_compliance --regscale_ssp_id 123 --no-create-issues

        # Sync and mark issues as POAMs
        regscale gcp sync_compliance --regscale_ssp_id 123 --create-poams
    """
    try:
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials, setup_credentials_from_json
        from regscale.integrations.commercial.gcp.compliance_integration import GCPComplianceIntegration

        logger.info("Starting GCP SCC compliance sync to RegScale...")

        # Set credentials (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            setup_credentials_from_json(credentials_json)
        elif credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        ensure_gcp_credentials()

        # Resolve scope from config if not provided
        scope = scope or str(GcpVariables.gcpScanType)
        project_id = project_id or str(GcpVariables.gcpProjectId)
        organization_id = organization_id or str(GcpVariables.gcpOrganizationId)

        # Log configuration
        logger.info("Framework: %s", framework)
        logger.info("Scope: %s", scope)
        logger.info("Create issues: %s", create_issues)
        logger.info("Update control status: %s", update_control_status)
        logger.info("Create POAMs: %s", create_poams)

        # Create and run GCPComplianceIntegration
        from regscale.integrations.commercial.gcp.compliance_integration import GCPScopeOptions

        scope_options = GCPScopeOptions(scope=scope, project_id=project_id, organization_id=organization_id)
        integration = GCPComplianceIntegration(
            plan_id=regscale_ssp_id,
            scope_options=scope_options,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
        )

        integration.sync_compliance()

        logger.info("GCP SCC compliance sync completed successfully.")

    except Exception as e:
        logger.error("Error syncing GCP SCC compliance: %s", e, exc_info=True)
        raise click.ClickException(str(e))


# =============================================================================
# Evidence Collection Commands
# =============================================================================


@gcpv2.command(name="collect_evidence")
@click.option(
    "--regscale_ssp_id",
    type=click.INT,
    help="The ID number from RegScale of the System Security Plan",
    prompt="Enter RegScale System Security Plan ID",
    required=True,
)
@click.option(
    "--control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'AU-2,AU-3,AU-6'). "
    "If not specified, evidence is collected for all controls in the assessment.",
)
@click.option(
    "--mode",
    type=click.Choice(GCP_VALID_EVIDENCE_MODES, case_sensitive=False),
    default="attachments",
    help="Evidence collection mode: 'attachments' saves as SSP file attachments, "
    "'records' creates individual Evidence records. Default: attachments",
)
@click.option(
    "--scope",
    type=click.Choice(GCP_VALID_SCAN_TYPES, case_sensitive=False),
    default=None,
    help="Scope for evidence collection. Defaults to gcpScanType from init.yaml.",
)
@click.option(
    "--project-id",
    type=str,
    required=False,
    help="GCP project ID. Defaults to gcpProjectId from init.yaml.",
    envvar="GCP_PROJECT_ID",
)
@click.option(
    "--organization-id",
    type=str,
    required=False,
    help="GCP organization ID. Defaults to gcpOrganizationId from init.yaml.",
    envvar="GCP_ORGANIZATION_ID",
)
@click.option(
    "--credentials-file",
    type=click.Path(exists=True, readable=True),
    required=False,
    help="Path to GCP service account JSON key file.",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
)
@click.option(
    "--credentials-json",
    type=str,
    required=False,
    help="GCP service account credentials as JSON string. Alternative to --credentials-file.",
    envvar="GCP_CREDENTIALS_JSON",
)
@click.option(
    "--credentials-json-base64",
    type=str,
    required=False,
    help="Base64-encoded GCP service account credentials JSON. Recommended for Airflow DAGs. "
    "Generate with: cat service-account.json | base64",
    envvar="GCP_CREDENTIALS_JSON_BASE64",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days. Default: 30",
)
def collect_evidence(
    regscale_ssp_id: int,
    control_ids: Optional[str],
    mode: str,
    scope: Optional[str],
    project_id: Optional[str],
    organization_id: Optional[str],
    credentials_file: Optional[str],
    credentials_json: Optional[str],
    credentials_json_base64: Optional[str],
    evidence_frequency: int,
) -> None:
    """
    Collect evidence for controls from GCP Security Command Center.

    This command collects evidence artifacts from GCP and stores them in RegScale.
    Evidence can be collected as SSP file attachments or individual Evidence records.

    Evidence Types:
    - Security Health Analytics findings
    - Asset inventory snapshots
    - Compliance assessment results
    - Cloud Audit Logs summaries

    Collection Modes:
    - attachments: Saves evidence as file attachments to the SSP (faster, less granular)
    - records: Creates individual Evidence records linked to controls (more detailed)

    Examples:
        # Collect evidence for all controls
        regscale gcp collect_evidence --regscale_ssp_id 123

        # Collect evidence for specific controls
        regscale gcp collect_evidence --regscale_ssp_id 123 --control-ids AU-2,AU-3,AU-6

        # Collect evidence as individual records
        regscale gcp collect_evidence --regscale_ssp_id 123 --mode records

        # Set custom evidence frequency
        regscale gcp collect_evidence --regscale_ssp_id 123 --evidence-frequency 7
    """
    try:
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials, setup_credentials_from_json

        logger.info("Starting GCP evidence collection...")

        # Set credentials (base64 > JSON > file > config)
        if credentials_json_base64:
            logger.info(LOG_MSG_USING_ENV_CREDENTIALS)
            setup_credentials_from_json(credentials_json_base64, is_base64=True)
        elif credentials_json:
            setup_credentials_from_json(credentials_json)
        elif credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file

        ensure_gcp_credentials()

        # Parse control IDs
        control_id_list = None
        if control_ids:
            control_id_list = [cid.strip() for cid in control_ids.split(",")]
            logger.info("Collecting evidence for controls: %s", control_id_list)
        else:
            logger.info("Collecting evidence for all controls")

        # Log configuration
        logger.info("Evidence mode: %s", mode)
        logger.info("Evidence frequency: %d days", evidence_frequency)

        # Build configuration
        config = EvidenceCollectionConfig(
            regscale_ssp_id=regscale_ssp_id,
            control_ids=control_id_list,
            mode=mode,
            frequency_days=evidence_frequency,
        )

        # Execute evidence collection
        _collect_gcp_evidence(config, scope, project_id, organization_id)

        logger.info("GCP evidence collection completed successfully.")

    except Exception as e:
        logger.error("Error collecting GCP evidence: %s", e, exc_info=True)
        raise click.ClickException(str(e))


def _collect_gcp_evidence(
    config: EvidenceCollectionConfig,
    scope: Optional[str],
    project_id: Optional[str],
    organization_id: Optional[str],
) -> None:
    """
    Internal function to collect GCP evidence using GCPComplianceIntegration.

    :param EvidenceCollectionConfig config: Evidence collection configuration
    :param Optional[str] scope: GCP scope (project, organization, folder)
    :param Optional[str] project_id: GCP project ID
    :param Optional[str] organization_id: GCP organization ID
    """
    from regscale.integrations.commercial.gcp.compliance_integration import (
        GCPComplianceIntegration,
        GCPEvidenceOptions,
        GCPScopeOptions,
    )

    # Resolve scope from config if not provided
    scope = scope or str(GcpVariables.gcpScanType)
    project_id = project_id or str(GcpVariables.gcpProjectId)
    organization_id = organization_id or str(GcpVariables.gcpOrganizationId)

    logger.info("Collecting evidence using GCPComplianceIntegration...")

    # Create compliance integration with evidence collection enabled
    scope_options = GCPScopeOptions(scope=scope, project_id=project_id, organization_id=organization_id)
    evidence_options = GCPEvidenceOptions(
        collect=True,
        as_attachments=(config.mode == "attachments"),
        as_records=(config.mode == "records"),
        control_ids=config.control_ids,
        frequency=config.frequency_days,
    )
    integration = GCPComplianceIntegration(
        plan_id=config.regscale_ssp_id,
        scope_options=scope_options,
        evidence_options=evidence_options,
        # Don't create issues or update control status - just collect evidence
        create_issues=False,
        update_control_status=False,
    )

    # Run the compliance sync which will also collect evidence
    integration.sync_compliance()

    click.echo(f"\nEvidence collection completed for SSP ID: {config.regscale_ssp_id}")
    click.echo(f"Mode: {config.mode}")
    if config.control_ids:
        click.echo(f"Controls: {', '.join(config.control_ids)}")
