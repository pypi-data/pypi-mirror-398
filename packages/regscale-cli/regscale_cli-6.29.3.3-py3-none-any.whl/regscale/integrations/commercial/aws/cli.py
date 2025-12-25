"""AWS CLI integration module."""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List

import click

from regscale.models.integration_models.flat_file_importer import FlatFileImporter

logger = logging.getLogger("regscale")


@dataclass
class ComplianceSyncConfig:
    """Configuration for AWS Audit Manager compliance sync."""

    region: str
    regscale_id: int
    framework: str = "NIST800-53R5"
    custom_framework_name: Optional[str] = None
    assessment_id: Optional[str] = None
    create_issues: bool = True
    update_control_status: bool = True
    create_poams: bool = False
    collect_evidence: bool = False
    evidence_control_ids: Optional[List[str]] = None
    evidence_frequency: int = 30
    max_evidence_per_control: int = 100
    use_assessment_evidence_folders: bool = True
    force_refresh: bool = False
    use_enhanced_analyzer: bool = False


# Evidence collection constants
EVIDENCE_MODE_SSP_ATTACHMENTS = "Evidence collection mode: SSP file attachments (default)"
EVIDENCE_MODE_INDIVIDUAL_RECORDS = "Evidence collection mode: Individual Evidence records"
DEFAULT_EVIDENCE_FREQUENCY_DAYS = 30  # Default evidence update frequency in days


@dataclass
class AWSCredentialConfig:
    """AWS credential configuration."""

    session_name: Optional[str] = None
    profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class FindingsSyncConfig:
    """Configuration for AWS findings sync."""

    region: str
    regscale_id: int
    credentials: AWSCredentialConfig
    generate_evidence: bool = False
    control_ids: Optional[str] = None
    format: str = "native"
    import_all_findings: bool = False
    evidence_frequency: int = DEFAULT_EVIDENCE_FREQUENCY_DAYS


@dataclass
class ConfigComplianceConfig:
    """Configuration for AWS Config compliance sync."""

    region: str
    regscale_id: int
    framework: str = "NIST800-53R5"
    conformance_pack_name: Optional[str] = None
    create_issues: bool = True
    update_control_status: bool = True
    create_poams: bool = False
    collect_evidence: bool = False
    evidence_as_attachments: bool = True
    evidence_as_records: bool = False
    evidence_control_ids: Optional[List[str]] = None
    evidence_frequency: int = 30
    use_security_hub: bool = False
    force_refresh: bool = False


@dataclass
class KMSConfig:
    """Configuration for AWS KMS evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_kms_evidence: bool = True
    kms_evidence_control_ids: Optional[List[str]] = None
    kms_evidence_frequency: int = 30
    kms_evidence_mode: str = "attachments"


@dataclass
class OrganizationConfig:
    """Configuration for AWS Organizations evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_org_evidence: bool = True
    org_evidence_control_ids: Optional[List[str]] = None
    org_evidence_frequency: int = 30
    org_evidence_mode: str = "attachments"


@dataclass
class IAMConfig:
    """Configuration for AWS IAM evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_iam_evidence: bool = True
    iam_evidence_control_ids: Optional[List[str]] = None
    iam_evidence_frequency: int = 30
    iam_evidence_mode: str = "attachments"


@dataclass
class GuardDutyConfig:
    """Configuration for AWS GuardDuty evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_guardduty_evidence: bool = True
    guardduty_evidence_control_ids: Optional[List[str]] = None
    guardduty_evidence_frequency: int = 30
    guardduty_evidence_mode: str = "attachments"


@dataclass
class S3Config:
    """Configuration for AWS S3 evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_s3_evidence: bool = True
    s3_evidence_control_ids: Optional[List[str]] = None
    s3_evidence_frequency: int = 30
    s3_evidence_mode: str = "attachments"


@dataclass
class CloudTrailConfig:
    """Configuration for AWS CloudTrail evidence collection."""

    region: str
    regscale_ssp_id: int
    collect_cloudtrail_evidence: bool = True
    cloudtrail_evidence_control_ids: Optional[List[str]] = None
    cloudtrail_evidence_frequency: int = 30
    cloudtrail_evidence_mode: str = "attachments"


def parse_tags(tags_string: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Parse tag string into dictionary.

    Format: key1=value1,key2=value2

    :param Optional[str] tags_string: Comma-separated key=value pairs
    :return: Dictionary of tag key-value pairs or None if input is empty
    :rtype: Optional[Dict[str, str]]
    """
    if not tags_string:
        return None

    tag_dict = {}
    try:
        for tag_pair in tags_string.split(","):
            if "=" not in tag_pair:
                logger.warning(f"Invalid tag format (missing '='): {tag_pair}")
                continue
            key, value = tag_pair.split("=", 1)
            tag_dict[key.strip()] = value.strip()
        return tag_dict if tag_dict else None
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing tags: {e}")
        raise click.ClickException("Invalid tag format. Expected format: key1=value1,key2=value2")


def resolve_aws_credentials(
    session_name: Optional[str],
    profile: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    aws_session_token: Optional[str],
    region: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Resolve AWS credentials from session cache, profile, or explicit credentials.

    Priority order:
    1. Cached session (if session_name provided)
    2. Explicit credentials (if provided)
    3. Profile (if provided)
    4. Environment variables / default credential chain

    :param Optional[str] session_name: Name of cached session to use
    :param Optional[str] profile: AWS profile name
    :param Optional[str] aws_access_key_id: Explicit access key ID
    :param Optional[str] aws_secret_access_key: Explicit secret access key
    :param Optional[str] aws_session_token: Explicit session token
    :param Optional[str] region: AWS region
    :return: Tuple of (profile, access_key_id, secret_access_key, session_token, region)
    :rtype: Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]
    """
    # If session-name is provided, try to get credentials from cache
    if session_name:
        from .session_manager import AWSSessionManager

        manager = AWSSessionManager()
        cached_creds = manager.get_credentials_for_session(session_name)

        if cached_creds:
            cached_access_key, cached_secret_key, cached_session_token, cached_region = cached_creds
            logger.info(f"Using cached AWS session: {session_name}")
            return (
                None,  # Don't use profile when using cached session
                cached_access_key,
                cached_secret_key,
                cached_session_token,
                region or cached_region,
            )
        else:
            logger.warning(f"Cached session '{session_name}' not found or expired. Falling back to other methods.")

    # Otherwise, use provided credentials or profile
    return (profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region)


@click.group(name="aws")
def awsv2():
    """AWS Integrations."""
    pass


@awsv2.command(name="sync_assets")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect inventory from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale will create and update assets as children of this record.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter resources by AWS account ID",
    envvar="AWS_ACCOUNT_ID",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter resources by tags (format: key1=value1,key2=value2). All tags must match.",
)
@click.option(
    "--force-refresh",
    is_flag=True,
    default=False,
    help="Force refresh AWS inventory data, ignoring cached data even if it's still valid.",
)
def sync_assets(
    region: str,
    regscale_id: int,
    session_name: Optional[str] = None,
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    account_id: Optional[str] = None,
    tags: Optional[str] = None,
    force_refresh: bool = False,
) -> None:
    """
    Sync AWS resources to RegScale assets.

    This command collects AWS resources and creates/updates corresponding assets in RegScale:
    - EC2 instances
    - S3 buckets
    - RDS instances
    - Lambda functions
    - DynamoDB tables
    - VPCs and networking resources
    - Container resources
    - And more...

    Caching Behavior:
    AWS inventory data is cached for 8 hours in artifacts/aws/inventory.json to improve performance.
    The cache is shared across all SSPs for the same AWS account/region.
    Use --force-refresh to bypass the cache and fetch fresh data from AWS.

    Note: "Updated" assets in the output are resources that already exist in the target SSP
    (from a previous sync). This is normal behavior when syncing to an SSP multiple times.

    Filtering Options:
    Use --account-id to filter resources by AWS account ID.
    Use --tags to filter resources by tags (format: Environment=prod,Team=security).
    Both filters use AND logic - all criteria must match.

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain
    """
    try:
        logger.info("Starting AWS asset sync to RegScale...")
        from .scanner import AWSInventoryIntegration

        # Parse tags
        tag_dict = parse_tags(tags)
        if tag_dict:
            logger.info(f"Filtering resources by tags: {tag_dict}")
        if account_id:
            logger.info(f"Filtering resources by account ID: {account_id}")

        # Resolve credentials from session cache or other methods
        profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        if force_refresh:
            logger.info("Force refresh enabled - clearing cached inventory data")

        AWSInventoryIntegration.sync_assets(
            plan_id=regscale_id,
            region=region,
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            account_id=account_id,
            tags=tag_dict,
            force_refresh=force_refresh,
        )
        logger.info("AWS asset sync completed successfully.")
    except (
        Exception
    ) as e:  # Broad catch appropriate for CLI command - may raise AWS SDK, network, or RegScale API errors
        logger.error(f"Error syncing AWS assets: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.group()
def inventory():
    """AWS resource inventory commands."""
    pass


@inventory.command(name="collect")
@click.option(
    "--region",
    type=str,
    default=os.getenv("AWS_REGION", "us-east-1"),
    help="AWS region to collect inventory from. Default is us-east-1.",
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    envvar="AWS_SECRET_ACCESS_KEY",
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter resources by AWS account ID",
    envvar="AWS_ACCOUNT_ID",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter resources by tags (format: key1=value1,key2=value2). All tags must match.",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (JSON format)",
    required=False,
)
def collect_inventory(
    region: str,
    session_name: Optional[str],
    profile: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    aws_session_token: Optional[str],
    account_id: Optional[str],
    tags: Optional[str],
    output: Optional[str],
) -> None:
    """
    Collect AWS resource inventory.

    This command collects information about various AWS resources including:
    - EC2 instances
    - S3 buckets
    - RDS instances
    - Lambda functions
    - And more...

    The inventory can be displayed to stdout or saved to a JSON file.

    Filtering Options:
    Use --account-id to filter resources by AWS account ID.
    Use --tags to filter resources by tags (format: Environment=prod,Team=security).
    Both filters use AND logic - all criteria must match.

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain
    """
    try:
        from .inventory import collect_all_inventory
        from regscale.models import DateTimeEncoder

        logger.info("Collecting AWS inventory...")

        # Parse tags
        tag_dict = parse_tags(tags)
        if tag_dict:
            logger.info(f"Filtering resources by tags: {tag_dict}")
        if account_id:
            logger.info(f"Filtering resources by account ID: {account_id}")

        # Resolve credentials from session cache or other methods
        profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        aws_inventory = collect_all_inventory(
            region=region,
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            account_id=account_id,
            tags=tag_dict,
        )
        logger.info(
            "AWS inventory collected successfully. Received %s resource(s).",
            sum(len(resources) for resources in aws_inventory.values()),
        )

        if output:
            with open(output, "w") as f:
                json.dump(aws_inventory, f, indent=2, cls=DateTimeEncoder)
            logger.info(f"Inventory saved to {output}")
        else:
            click.echo(json.dumps(aws_inventory, indent=2, cls=DateTimeEncoder))

    except Exception as e:
        logger.error(f"Error collecting AWS inventory: {e}")
        raise click.ClickException(str(e))


@awsv2.group(help="Sync AWS Inspector Scans to RegScale.")
def inspector():
    """Sync AWS Inspector scans."""


@inspector.command(name="import_scans")
@FlatFileImporter.common_scanner_options(
    message="File path to the folder containing AWS Inspector files to process to RegScale.",
    prompt="File path for AWS Inspector files (CSV or JSON)",
    import_name="aws_inspector",
)
def import_scans(
    folder_path: os.PathLike[str],
    regscale_ssp_id: int,
    scan_date: datetime,
    mappings_path: click.Path,
    disable_mapping: bool,
    s3_bucket: str,
    s3_prefix: str,
    aws_profile: str,
    upload_file: Optional[bool] = True,
) -> None:
    """
    Import AWS Inspector scans to a System Security Plan in RegScale as assets and vulnerabilities.
    """
    import_aws_scans(
        folder_path=folder_path,
        regscale_ssp_id=regscale_ssp_id,
        scan_date=scan_date,
        mappings_path=mappings_path,
        disable_mapping=disable_mapping,
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        aws_profile=aws_profile,
        upload_file=upload_file,
    )


def import_aws_scans(
    folder_path: os.PathLike[str],
    regscale_ssp_id: int,
    mappings_path: click.Path,
    scan_date: datetime,
    s3_bucket: str,
    s3_prefix: str,
    aws_profile: str,
    disable_mapping: Optional[bool] = False,
    upload_file: Optional[bool] = True,
) -> None:
    """
    Function to import AWS Inspector scans to RegScale as assets and vulnerabilities

    :param os.PathLike[str] folder_path: Path to the folder containing AWS Inspector files
    :param int regscale_ssp_id: RegScale System Security Plan ID
    :param datetime.date scan_date: Date of the scan
    :param click.Path mappings_path: Path to the header mapping file
    :param str s3_bucket: The S3 bucket to download the files from
    :param str s3_prefix: The S3 prefix to download the files from
    :param str aws_profile: The AWS profile to use for S3 access
    :param bool disable_mapping: Disable header mapping
    :param bool upload_file: Upload the file to RegScale after processing, defaults to True
    :rtype: None
    """
    from regscale.models.integration_models.aws_models.inspector_scan import InspectorScan

    FlatFileImporter.import_files(
        import_type=InspectorScan,
        import_name="AWS Inspector",
        file_types=[".csv", ".json"],
        folder_path=folder_path,
        object_id=regscale_ssp_id,
        scan_date=scan_date,
        mappings_path=mappings_path,
        disable_mapping=disable_mapping,
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        aws_profile=aws_profile,
        upload_file=upload_file,
    )


@awsv2.command(name="sync_findings")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect findings from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale will create and update findings as children of this record.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--generate-evidence",
    is_flag=True,
    default=False,
    help="Generate evidence record for collected findings and link to SSP (uses --regscale_id)",
)
@click.option(
    "--control-ids",
    type=str,
    default=None,
    help="Comma-separated list of control IDs to link evidence (e.g., '123,456,789')",
)
@click.option(
    "--format",
    type=click.Choice(["native", "ocsf", "both"], case_sensitive=False),
    default="native",
    help="Output format for findings (native, ocsf, or both)",
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter findings by AWS account ID",
    envvar="AWS_ACCOUNT_ID",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter findings by resource tags (format: key1=value1,key2=value2). All tags must match (AND logic).",
)
@click.option(
    "--import-all-findings",
    is_flag=True,
    default=False,
    help="Import all findings even if they are not associated with an asset in RegScale. By default, findings without matching assets are skipped.",
)
def sync_findings(
    region: str,
    regscale_id: int,
    session_name: Optional[str] = None,
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    generate_evidence: bool = False,
    control_ids: Optional[str] = None,
    format: str = "native",
    account_id: Optional[str] = None,
    tags: Optional[str] = None,
    import_all_findings: bool = False,
) -> None:
    """
    Sync AWS Security Hub findings to RegScale with optional filtering.

    This command fetches findings from AWS Security Hub and creates/updates
    corresponding issues in RegScale. Optionally generates evidence records
    and supports OCSF (Open Cybersecurity Schema Framework) format export.

    Filtering Options:
    Use --account-id to filter findings by AWS account.
    Use --tags to filter findings by resource tags (format: key1=value1,key2=value2).
    Both filters use AND logic - all criteria must match.

    Evidence Generation:
    Use --generate-evidence to create evidence records for compliance documentation.
    Evidence will be automatically linked to the SSP specified by --regscale_id.
    Optionally link to specific controls with --control-ids.

    OCSF Format:
    Use --format ocsf to export findings in OCSF normalized format for cross-platform
    security data sharing. Use --format both for dual-format export.

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain
    """
    # Parse tags into dictionary
    tag_dict = parse_tags(tags) if tags else None

    # Create credential config
    credentials = AWSCredentialConfig(
        session_name=session_name,
        profile=profile,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        account_id=account_id,
        tags=tag_dict,
    )

    # Create config object
    config = FindingsSyncConfig(
        region=region,
        regscale_id=regscale_id,
        credentials=credentials,
        generate_evidence=generate_evidence,
        control_ids=control_ids,
        format=format,
        import_all_findings=import_all_findings,
    )
    _sync_findings_with_config(config)


def _sync_findings_with_config(config: FindingsSyncConfig) -> None:
    """
    Internal function to sync findings using configuration object.

    :param FindingsSyncConfig config: Configuration for findings sync
    """
    try:
        logger.info("Starting AWS Security Hub findings sync to RegScale...")
        from .scanner import AWSInventoryIntegration
        import boto3
        from regscale.integrations.commercial.aws.common import fetch_aws_findings

        # Resolve credentials from session cache or other methods
        profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region = resolve_aws_credentials(
            config.credentials.session_name,
            config.credentials.profile,
            config.credentials.aws_access_key_id,
            config.credentials.aws_secret_access_key,
            config.credentials.aws_session_token,
            config.region,
        )

        # Debug logging
        logger.debug(
            f"Resolved credentials - profile: {profile}, region: {region}, has_keys: {bool(aws_access_key_id)}"
        )

        # Get tag dictionary and account ID from credentials
        tag_dict = config.credentials.tags
        if tag_dict:
            logger.info(f"Filtering findings by tags: {tag_dict}")
        if config.credentials.account_id:
            logger.info(f"Filtering findings by account ID: {config.credentials.account_id}")

        # Parse control IDs
        control_id_list = None
        if config.control_ids:
            control_id_list = [int(cid.strip()) for cid in config.control_ids.split(",")]

        # If evidence generation or OCSF format requested, use enhanced processing
        if config.generate_evidence or config.format != "native":
            # Create AWS session
            if aws_access_key_id or aws_secret_access_key:
                session = boto3.Session(
                    region_name=region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    aws_session_token=aws_session_token,
                )
            else:
                session = boto3.Session(
                    profile_name=profile,
                    region_name=region,
                )
            client = session.client("securityhub")

            logger.info("Fetching findings from AWS Security Hub...")
            # Fetch raw findings with minimum severity from config
            from regscale.core.app.application import Application

            app = Application()
            minimum_severity = app.config.get("issues", {}).get("amazon", {}).get("minimumSeverity")
            raw_findings = fetch_aws_findings(aws_client=client, minimum_severity=minimum_severity)
            logger.info(f"Fetched {len(raw_findings)} findings from AWS Security Hub")

            # Process with evidence/OCSF support
            scanner = AWSInventoryIntegration(
                plan_id=config.regscale_id, import_all_findings=config.import_all_findings
            )
            scanner.authenticate(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region=region,
                aws_session_token=aws_session_token,
                profile=profile,
                account_id=config.credentials.account_id,
                tags=tag_dict,
            )

            # Don't set num_findings_to_process since many findings get filtered during parse_finding()
            # Progress bar will show processed count without a misleading total

            # Get asset map for linking findings to assets
            logger.info("Loading asset map from RegScale...")
            scanner.asset_map_by_identifier.update(scanner.get_asset_map())

            logger.info("Processing findings with evidence/OCSF support...")
            integration_findings, evidence = scanner.process_findings_with_evidence(
                findings=raw_findings,
                service_name="SecurityHub",
                generate_evidence=config.generate_evidence,
                ssp_id=config.regscale_id,  # Use regscale_id as the SSP ID for evidence linking
                control_ids=control_id_list,
                ocsf_format=(config.format in ["ocsf", "both"]),
            )

            # Consolidate findings by plugin_id in consolidated mode
            logger.info("Consolidating findings by plugin_id...")
            consolidated_findings = scanner.consolidate_findings_by_plugin_id(integration_findings)

            # Sync findings to RegScale with progress bar
            logger.info("Syncing findings to RegScale...")
            findings_processed = scanner.update_regscale_findings(consolidated_findings)

            logger.info(
                f"AWS Security Hub findings sync completed successfully. Processed {findings_processed} findings."
            )
            if evidence:
                logger.info(f"Created evidence record: {evidence.id} - {evidence.title}")
        else:
            # Standard sync without evidence generation
            findings_processed = AWSInventoryIntegration.sync_findings(
                plan_id=config.regscale_id,
                region=region,
                profile=profile,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                account_id=config.credentials.account_id,
                tags=tag_dict,
                import_all_findings=config.import_all_findings,
            )
            logger.info(
                f"AWS Security Hub findings sync completed successfully. Processed {findings_processed} findings."
            )

    except Exception as e:
        logger.error(f"Error syncing AWS Security Hub findings: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_findings_and_assets")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect findings and assets from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale will create and update findings and assets as children of this record.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter resources by AWS account ID (from ARN)",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter resources by tags (format: key1=value1,key2=value2). All specified tags must match (AND logic).",
)
@click.option(
    "--import-all-findings",
    is_flag=True,
    default=False,
    help="Import all findings even if they are not associated with an asset in RegScale. By default, findings without matching assets are skipped.",
)
def sync_findings_and_assets(
    region: str,
    regscale_id: int,
    session_name: Optional[str] = None,
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    account_id: Optional[str] = None,
    tags: Optional[str] = None,
    import_all_findings: bool = False,
) -> None:
    """
    Sync AWS Security Hub findings and automatically discovered assets to RegScale.

    This command fetches findings from AWS Security Hub, creates/updates corresponding
    issues in RegScale, and also creates assets for the resources referenced in the findings.
    This provides a comprehensive view by creating both the security findings and the
    underlying AWS resources they reference.

    Filtering support:
    - Account ID: Filter resources by AWS account ID (extracted from ARNs)
    - Tags: Filter resources by tag key-value pairs (AND logic - all must match)

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain
    """
    try:
        logger.info("Starting AWS Security Hub findings and assets sync to RegScale...")
        from .scanner import AWSInventoryIntegration

        # Parse tags if provided
        tag_dict = parse_tags(tags)
        if account_id:
            logger.info(f"Filtering resources by account ID: {account_id}")
        if tag_dict:
            logger.info(f"Filtering resources by tags: {tag_dict}")

        # Resolve credentials from session cache or other methods
        profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        scanner = AWSInventoryIntegration(plan_id=regscale_id, import_all_findings=import_all_findings)
        findings_processed, assets_processed = scanner.sync_findings_and_assets(
            plan_id=regscale_id,
            region=region,
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            account_id=account_id,
            tags=tag_dict,
        )
        logger.info(
            f"AWS Security Hub sync completed successfully. "
            f"Processed {findings_processed} findings and {assets_processed} assets."
        )
    except Exception as e:
        logger.error(f"Error syncing AWS Security Hub findings and assets: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.group()
def findings():
    """AWS Security Hub findings commands."""
    pass


def _create_aws_session(
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    aws_session_token: Optional[str],
    profile: Optional[str],
    region: str,
) -> "boto3.Session":
    """
    Create boto3 session with provided credentials.

    :param Optional[str] aws_access_key_id: AWS access key ID
    :param Optional[str] aws_secret_access_key: AWS secret access key
    :param Optional[str] aws_session_token: AWS session token
    :param Optional[str] profile: AWS profile name
    :param str region: AWS region
    :return: Configured boto3 session
    :rtype: boto3.Session
    """
    import boto3

    if aws_access_key_id or aws_secret_access_key:
        return boto3.Session(
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
        )
    return boto3.Session(profile_name=profile, region_name=region)


def _finding_matches_account(finding: Dict[str, Any], account_id: str) -> bool:
    """
    Check if finding's resources match the account ID.

    :param Dict[str, Any] finding: AWS Security Hub finding
    :param str account_id: AWS account ID to match
    :return: True if any resource matches the account ID
    :rtype: bool
    """
    resources = finding.get("Resources", [])
    for resource in resources:
        resource_id = resource.get("Id", "")
        if resource_id.startswith("arn:"):
            arn_parts = resource_id.split(":")
            if len(arn_parts) >= 5 and arn_parts[4] == account_id:
                return True
    return False


def _finding_matches_tags(finding: Dict[str, Any], tag_dict: Dict[str, str]) -> bool:
    """
    Check if finding's resources match all specified tags.

    :param Dict[str, Any] finding: AWS Security Hub finding
    :param Dict[str, str] tag_dict: Tags to match (all must match - AND logic)
    :return: True if any resource matches all tags
    :rtype: bool
    """
    resources = finding.get("Resources", [])
    for resource in resources:
        resource_tags = resource.get("Tags", {})
        if all(resource_tags.get(k) == v for k, v in tag_dict.items()):
            return True
    return False


def _filter_findings(
    findings: List[Dict[str, Any]], account_id: Optional[str], tag_dict: Optional[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Apply account and tag filters to findings.

    :param List[Dict[str, Any]] findings: List of findings to filter
    :param Optional[str] account_id: Account ID filter (if specified)
    :param Optional[Dict[str, str]] tag_dict: Tag filters (if specified)
    :return: Filtered list of findings
    :rtype: List[Dict[str, Any]]
    """
    if not account_id and not tag_dict:
        return findings

    filtered = []
    for finding in findings:
        if account_id and not _finding_matches_account(finding, account_id):
            continue
        if tag_dict and not _finding_matches_tags(finding, tag_dict):
            continue
        filtered.append(finding)

    return filtered


def _write_findings_output(findings: List[Dict[str, Any]], output: Optional[str]) -> None:
    """
    Write findings to stdout or file.

    :param List[Dict[str, Any]] findings: Findings to write
    :param Optional[str] output: Output path (None for default, '-' for stdout)
    :rtype: None
    """
    from regscale.models import DateTimeEncoder

    # Default output path
    if output is None:
        output = os.path.join("artifacts", "aws", "findings.json")

    if output == "-":
        click.echo(json.dumps(findings, indent=2, cls=DateTimeEncoder))
    else:
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2, cls=DateTimeEncoder)
        logger.info(f"Findings saved to {output}")


@findings.command(name="collect")
@click.option(
    "--region",
    type=str,
    default=os.getenv("AWS_REGION", "us-east-1"),
    help="AWS region to collect findings from. Default is us-east-1.",
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    envvar="AWS_SECRET_ACCESS_KEY",
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter findings by AWS account ID (from ARN)",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter findings by tags (format: key1=value1,key2=value2). All specified tags must match (AND logic).",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (JSON format). Default: artifacts/aws/findings.json",
    required=False,
)
def collect_findings(
    region: str,
    session_name: Optional[str],
    profile: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    aws_session_token: Optional[str],
    account_id: Optional[str],
    tags: Optional[str],
    output: Optional[str],
) -> None:
    """
    Collect AWS Security Hub findings.

    This command fetches findings from AWS Security Hub and displays them to stdout
    or saves them to a JSON file. The findings include security issues, compliance
    violations, and other security-related information from AWS Security Hub.

    If no output file is specified, findings will be saved to artifacts/aws/findings.json
    by default. Use --output - to display to stdout instead.

    Filtering support:
    - Account ID: Filter findings by AWS account ID (extracted from ARNs)
    - Tags: Filter findings by tag key-value pairs (AND logic - all must match)

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain
    """
    try:
        from regscale.integrations.commercial.aws.common import fetch_aws_findings

        logger.info("Collecting AWS Security Hub findings...")

        # Parse tags and log filters
        tag_dict = parse_tags(tags)
        if account_id:
            logger.info(f"Filtering findings by account ID: {account_id}")
        if tag_dict:
            logger.info(f"Filtering findings by tags: {tag_dict}")

        # Resolve credentials
        profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        # Create session and fetch findings
        session = _create_aws_session(aws_access_key_id, aws_secret_access_key, aws_session_token, profile, region)
        client = session.client("securityhub")
        findings = fetch_aws_findings(aws_client=client)

        # Apply filtering
        original_count = len(findings)
        findings = _filter_findings(findings, account_id, tag_dict)

        if account_id or tag_dict:
            logger.info(f"Filtered from {original_count} to {len(findings)} findings based on criteria")

        logger.info(f"AWS Security Hub findings collected successfully. Found {len(findings)} finding(s).")

        # Write output
        _write_findings_output(findings, output)

    except Exception as e:
        logger.error(f"Error collecting AWS Security Hub findings: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.group()
def auth():
    """AWS session token management commands."""
    pass


@auth.command(name="login")
@click.option(
    "--session-name",
    type=str,
    required=True,
    help="Name for this session (used to cache credentials)",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key",
    envvar="AWS_SECRET_ACCESS_KEY",
)
@click.option(
    "--mfa-serial",
    type=str,
    required=False,
    help="ARN of MFA device (e.g., arn:aws:iam::123456789012:mfa/username)",
)
@click.option(
    "--mfa-code",
    type=str,
    required=False,
    help="6-digit MFA code from authenticator app",
)
@click.option(
    "--role-arn",
    type=str,
    required=False,
    help="ARN of role to assume (e.g., arn:aws:iam::123456789012:role/MyRole)",
)
@click.option(
    "--role-session-name",
    type=str,
    required=False,
    help="Name for the assumed role session",
)
@click.option(
    "--duration",
    type=int,
    default=3600,
    help="Duration for session token in seconds (900-43200, default: 3600)",
)
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to associate with this session",
)
def login(
    session_name: str,
    profile: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    mfa_serial: Optional[str],
    mfa_code: Optional[str],
    role_arn: Optional[str],
    role_session_name: Optional[str],
    duration: int,
    region: str,
) -> None:
    """
    Generate and cache AWS session tokens.

    This command generates temporary AWS credentials (session tokens) and caches them
    locally for use with subsequent AWS commands. Session tokens provide better security
    than long-term access keys and support MFA authentication.

    Examples:

        # Simple session from profile
        regscale aws auth login --session-name my-session --profile default

        # Session with MFA
        regscale aws auth login --session-name my-session --profile default \\
            --mfa-serial arn:aws:iam::123456789012:mfa/username --mfa-code 123456

        # Assume role with MFA
        regscale aws auth login --session-name cross-account --profile default \\
            --role-arn arn:aws:iam::987654321098:role/CrossAccountRole \\
            --mfa-serial arn:aws:iam::123456789012:mfa/username --mfa-code 123456

        # Session with explicit credentials
        regscale aws auth login --session-name my-session \\
            --aws_access_key_id AKIAIOSFODNN7EXAMPLE \\
            --aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    """
    try:
        from .session_manager import AWSSessionManager

        logger.info(f"Generating AWS session token: {session_name}")

        manager = AWSSessionManager()

        # Generate session token
        credentials = manager.get_session_token(
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            mfa_serial=mfa_serial,
            mfa_code=mfa_code,
            role_arn=role_arn,
            role_session_name=role_session_name,
            duration_seconds=duration,
        )

        # Cache the session
        manager.cache_session(session_name, credentials, region)

        click.echo(click.style(f"\n✓ Session '{session_name}' created successfully!", fg="green", bold=True))
        click.echo(f"Region: {region}")
        click.echo(f"Expires: {credentials['expiration']}")
        click.echo(f"\nUse --session-name {session_name} with AWS commands to use these credentials.")

    except Exception as e:
        logger.error(f"Failed to generate session token: {e}", exc_info=True)
        raise click.ClickException(str(e))


@auth.command(name="logout")
@click.option(
    "--session-name",
    type=str,
    required=True,
    help="Name of session to clear",
)
def logout(session_name: str) -> None:
    """
    Clear a cached AWS session.

    This removes the cached session tokens for the specified session name.

    Example:
        regscale aws auth logout --session-name my-session
    """
    try:
        from .session_manager import AWSSessionManager

        manager = AWSSessionManager()

        if manager.clear_session(session_name):
            click.echo(click.style(f"✓ Session '{session_name}' cleared successfully!", fg="green"))
        else:
            click.echo(click.style(f"Session '{session_name}' not found.", fg="yellow"))

    except Exception as e:
        logger.error(f"Failed to clear session: {e}", exc_info=True)
        raise click.ClickException(str(e))


@auth.command(name="logout-all")
@click.confirmation_option(prompt="Are you sure you want to clear all cached sessions?")
def logout_all() -> None:
    """
    Clear all cached AWS sessions.

    This removes all cached session tokens.

    Example:
        regscale aws auth logout-all
    """
    try:
        from .session_manager import AWSSessionManager

        manager = AWSSessionManager()
        count = manager.clear_all_sessions()

        click.echo(click.style(f"✓ Cleared {count} session(s) successfully!", fg="green"))

    except Exception as e:
        logger.error(f"Failed to clear sessions: {e}", exc_info=True)
        raise click.ClickException(str(e))


@auth.command(name="list")
def list_sessions() -> None:
    """
    List all cached AWS sessions.

    This shows all cached session tokens with their expiration status.

    Example:
        regscale aws auth list
    """
    try:
        from .session_manager import AWSSessionManager

        manager = AWSSessionManager()
        sessions = manager.list_sessions()

        if not sessions:
            click.echo("No cached sessions found.")
            return

        click.echo("\nCached AWS Sessions:")
        click.echo("=" * 80)

        for session in sessions:
            status = click.style("EXPIRED", fg="red") if session["expired"] else click.style("ACTIVE", fg="green")
            click.echo(f"\nSession: {click.style(session['name'], bold=True)}")
            click.echo(f"  Status:     {status}")
            click.echo(f"  Region:     {session['region']}")
            click.echo(f"  Expires:    {session['expiration']}")
            click.echo(f"  Cached At:  {session['cached_at']}")

        click.echo("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_compliance")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect compliance data from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale will create and update compliance assessments as children of this record.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter resources by AWS account ID (from ARN)",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter resources by tags (format: key1=value1,key2=value2). All specified tags must match (AND logic).",
)
@click.option(
    "--framework",
    type=click.Choice(
        ["NIST800-53R5", "SOC2", "PCI DSS", "HIPAA", "GDPR", "ISO27001", "CIS", "CUSTOM"],
        case_sensitive=False,
    ),
    default="NIST800-53R5",
    help="Compliance framework to sync. Only assessments matching this framework will be processed. "
    "Use CUSTOM for custom frameworks and provide --custom-framework-name. "
    "NOTE: Framework filtering is bypassed when --assessment-id is specified.",
)
@click.option(
    "--custom-framework-name",
    type=str,
    required=False,
    help="Custom framework name for CUSTOM framework types. Required when --framework=CUSTOM.",
)
@click.option(
    "--assessment-id",
    type=str,
    required=False,
    help="Specific AWS Audit Manager assessment ID to sync. When provided, framework filtering is bypassed "
    "and the specified assessment is used directly regardless of its framework type.",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for failed compliance controls (default: True)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on compliance results (default: True)",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=False,
    help="Collect and store evidence artifacts from AWS Audit Manager (default: False)",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'AU-2,AU-3,AU-6'). "
    "If not specified, evidence is collected for all controls in the assessment.",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--max-evidence-per-control",
    type=int,
    default=100,
    help="Maximum number of evidence items to collect per control (default: 100). "
    "For accounts with large numbers of resources, you may need to increase this significantly (e.g., 5000 or higher). "
    "Set to 0 for unlimited evidence collection (not recommended for very large environments).",
)
@click.option(
    "--use-assessment-evidence-folders/--no-use-assessment-evidence-folders",
    default=True,
    help="Use assessment-level evidence collection (faster, automatic) vs control-level (slower, requires manual report). "
    "Assessment-level collects evidence from assessment folders directly. Control-level requires assessment report generation. "
    "(default: True - use assessment folders)",
)
@click.option(
    "--force-refresh",
    is_flag=True,
    default=False,
    help="Force refresh of compliance data by bypassing cache (default: False)",
)
@click.option(
    "--use-enhanced-analyzer/--no-enhanced-analyzer",
    default=True,
    help="Use enhanced ControlComplianceAnalyzer for evidence-based compliance determination (default: True)",
)
@click.pass_context
def sync_compliance(ctx, **kwargs) -> None:
    """
    Sync AWS Audit Manager compliance assessments to RegScale.

    This command fetches compliance assessment results from AWS Audit Manager and:
    - Creates control assessments in RegScale based on AWS assessment results
    - Creates issues for failed compliance controls (optional)
    - Updates control implementation status (optional)
    - Collects and stores evidence artifacts from AWS Audit Manager (optional)
    - Supports multiple compliance frameworks (NIST 800-53, SOC2, PCI DSS, etc.)

    AWS Audit Manager provides automated evidence collection and compliance
    assessments against standard and custom frameworks. This integration brings
    those assessments into RegScale for unified compliance management.

    Filtering support:
    - Account ID: Filter resources by AWS account ID (extracted from ARNs)
    - Tags: Filter resources by tag key-value pairs (AND logic - all must match)

    Evidence Collection:
    Use --collect-evidence to retrieve and store evidence artifacts from AWS Audit Manager.
    Evidence is collected from evidence folders for each control and stored as JSONL
    attachments in RegScale Evidence records. Evidence includes CloudTrail events,
    AWS Config snapshots, and other automated evidence sources.

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain

    Examples:
        # Sync all assessments for a plan
        regscale aws sync_compliance --regscale_id 123

        # Sync specific assessment (bypasses framework filtering)
        regscale aws sync_compliance --regscale_id 123 --assessment-id abc-123

        # Sync custom framework assessment by ID
        regscale aws sync_compliance --regscale_id 123 --assessment-id abc-123 \\
            --framework CUSTOM --custom-framework-name "DOC Moderate Baseline"
        # NOTE: When --assessment-id is provided, the framework parameters are optional

        # Sync without creating issues
        regscale aws sync_compliance --regscale_id 123 --no-create-issues

        # Sync with evidence collection
        regscale aws sync_compliance --regscale_id 123 --collect-evidence

        # Collect evidence only for specific controls
        regscale aws sync_compliance --regscale_id 123 --collect-evidence \\
            --evidence-control-ids AU-2,AU-3,AU-6,AC-2
    """
    try:
        # Extract parameters from kwargs
        region = kwargs.get("region", "us-east-1")
        regscale_id = kwargs.get("regscale_id")
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        framework = kwargs.get("framework", "NIST800-53R5")
        custom_framework_name = kwargs.get("custom_framework_name")
        assessment_id = kwargs.get("assessment_id")
        create_issues = kwargs.get("create_issues", True)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", False)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        max_evidence_per_control = kwargs.get("max_evidence_per_control", 100)
        use_assessment_evidence_folders = kwargs.get("use_assessment_evidence_folders", True)
        force_refresh = kwargs.get("force_refresh", False)
        use_enhanced_analyzer = kwargs.get("use_enhanced_analyzer", True)

        # Parse evidence control IDs into list
        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]

        # Build configuration objects
        sync_config = ComplianceSyncConfig(
            region=region,
            regscale_id=regscale_id,
            framework=framework,
            custom_framework_name=custom_framework_name,
            assessment_id=assessment_id,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            max_evidence_per_control=max_evidence_per_control,
            use_assessment_evidence_folders=use_assessment_evidence_folders,
            force_refresh=force_refresh,
            use_enhanced_analyzer=use_enhanced_analyzer,
        )

        credential_config = AWSCredentialConfig(
            session_name=session_name,
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            account_id=account_id,
            tags=parse_tags(tags),
        )

        # Delegate to helper function
        _execute_compliance_sync(sync_config, credential_config)

    except Exception as e:
        logger.error(f"Error syncing AWS Audit Manager compliance: {e}", exc_info=True)
        raise click.ClickException(str(e))


def _execute_compliance_sync(sync_config: ComplianceSyncConfig, credential_config: AWSCredentialConfig) -> None:
    """
    Execute the compliance sync with provided configurations.

    :param ComplianceSyncConfig sync_config: Sync configuration
    :param AWSCredentialConfig credential_config: AWS credential configuration
    :return: None
    :rtype: None
    """
    from .audit_manager_compliance import AWSAuditManagerCompliance

    logger.info("Starting AWS Audit Manager compliance sync to RegScale...")

    # Log filtering information
    if credential_config.account_id:
        logger.info(f"Filtering resources by account ID: {credential_config.account_id}")
    if credential_config.tags:
        logger.info(f"Filtering resources by tags: {credential_config.tags}")

    # Resolve AWS credentials
    profile, access_key, secret_key, session_token, region = resolve_aws_credentials(
        credential_config.session_name,
        credential_config.profile,
        credential_config.aws_access_key_id,
        credential_config.aws_secret_access_key,
        credential_config.aws_session_token,
        sync_config.region,
    )

    # Log credential resolution results
    logger.info(
        f"Using AWS credentials - profile: {profile if profile else 'not set'}, "
        f"explicit credentials: {'yes' if access_key else 'no'}, region: {region}"
    )

    # Log evidence collection request
    if sync_config.evidence_control_ids:
        logger.info(f"Evidence collection requested for controls: {sync_config.evidence_control_ids}")

    # Create scanner and execute sync
    scanner = AWSAuditManagerCompliance(
        plan_id=sync_config.regscale_id,
        region=region,
        profile=profile,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        framework=sync_config.framework,
        custom_framework_name=sync_config.custom_framework_name,
        assessment_id=sync_config.assessment_id,
        create_issues=sync_config.create_issues,
        update_control_status=sync_config.update_control_status,
        create_poams=sync_config.create_poams,
        collect_evidence=sync_config.collect_evidence,
        evidence_control_ids=sync_config.evidence_control_ids,
        evidence_frequency=sync_config.evidence_frequency,
        max_evidence_per_control=sync_config.max_evidence_per_control,
        use_assessment_evidence_folders=sync_config.use_assessment_evidence_folders,
        account_id=credential_config.account_id,
        tags=credential_config.tags,
        force_refresh=sync_config.force_refresh,
        use_enhanced_analyzer=sync_config.use_enhanced_analyzer,
    )

    scanner.sync_compliance()

    logger.info("AWS Audit Manager compliance sync completed successfully")


@awsv2.command(name="sync_config_compliance")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect compliance data from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale will create and update compliance assessments as children of this record.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter Config rules by AWS account ID (from ARN)",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter Config rules by tags (format: key1=value1,key2=value2). All specified tags must match (AND logic).",
)
@click.option(
    "--framework",
    type=click.Choice(
        ["NIST800-53R5", "SOC2", "PCI DSS", "HIPAA", "GDPR", "ISO27001", "CIS"],
        case_sensitive=False,
    ),
    default="NIST800-53R5",
    help="Compliance framework to sync. Only rules matching this framework will be processed.",
)
@click.option(
    "--conformance-pack-name",
    type=str,
    required=False,
    help="Specific AWS Config conformance pack to sync (optional)",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for failed compliance controls (default: True)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on compliance results (default: True)",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=False,
    help="Collect and store evidence artifacts from AWS Config (default: False)",
)
@click.option(
    "--evidence-as-attachments/--no-evidence-as-attachments",
    default=True,
    help="Store evidence as SSP-level file attachments (default: True)",
)
@click.option(
    "--evidence-as-records",
    is_flag=True,
    default=False,
    help="Create individual Evidence records per control (like Audit Manager)",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'AU-2,AU-3,AU-6'). "
    "If not specified, evidence is collected for all controls.",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--use-security-hub/--no-use-security-hub",
    default=False,
    help="Include AWS Security Hub control findings (default: False)",
)
@click.option(
    "--force-refresh",
    is_flag=True,
    default=False,
    help="Force refresh of compliance data by bypassing cache (default: False)",
)
@click.pass_context
def sync_config_compliance(ctx, **kwargs) -> None:
    """
    Sync AWS Config compliance assessments to RegScale (alternative to Audit Manager).

    This command provides equivalent functionality to AWS Audit Manager using AWS Config
    and optionally Security Hub. Use this when Audit Manager is not available.

    This command fetches compliance assessment results from AWS Config rules and:
    - Creates control assessments in RegScale based on Config rule evaluation results
    - Creates issues for failed compliance controls (optional)
    - Updates control implementation status (optional)
    - Collects evidence artifacts from Config evaluations (optional)

    Evidence Collection Modes:
    - Default (--evidence-as-attachments): Creates consolidated evidence file attached to SSP
    - Optional (--evidence-as-records): Creates individual Evidence records per control

    Examples:
        # Basic compliance sync (no evidence)
        regscale aws sync_config_compliance --regscale_id 123 --framework NIST800-53R5

        # Filter by account ID
        regscale aws sync_config_compliance --regscale_id 123 --account-id 123456789012

        # Filter by tags
        regscale aws sync_config_compliance --regscale_id 123 --tags Environment=Production,Owner=Security

        # Combine account and tag filtering
        regscale aws sync_config_compliance --regscale_id 123 --account-id 123456789012 \\
            --tags Environment=Production

        # With evidence as SSP attachments (default)
        regscale aws sync_config_compliance --regscale_id 123 --collect-evidence

        # With evidence as individual records (Audit Manager style)
        regscale aws sync_config_compliance --regscale_id 123 --collect-evidence --evidence-as-records

        # Evidence for specific controls only
        regscale aws sync_config_compliance --regscale_id 123 --collect-evidence \\
            --evidence-control-ids AC-2,AU-3,SI-2

        # With Security Hub integration
        regscale aws sync_config_compliance --regscale_id 123 --use-security-hub
    """
    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        framework = kwargs["framework"]
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        conformance_pack_name = kwargs.get("conformance_pack_name")
        create_issues = kwargs.get("create_issues", True)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", False)
        evidence_as_attachments = kwargs.get("evidence_as_attachments", True)
        evidence_as_records = kwargs.get("evidence_as_records", False)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        use_security_hub = kwargs.get("use_security_hub", False)
        force_refresh = kwargs.get("force_refresh", False)

        # Parse evidence control IDs
        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]

        # Parse tags
        parsed_tags = parse_tags(tags) if tags else None

        # Resolve AWS credentials
        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name,
            profile,
            aws_access_key_id,
            aws_secret_access_key,
            aws_session_token,
            region,
        )

        # Log credential resolution results
        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        # Log filtering information
        if account_id:
            logger.info(f"Filtering Config rules by account ID: {account_id}")
        if parsed_tags:
            logger.info(f"Filtering Config rules by tags: {parsed_tags}")

        # Log evidence collection request
        if collect_evidence:
            if evidence_as_records:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)
            else:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)

            if evidence_control_list:
                logger.info(f"Evidence collection requested for controls: {evidence_control_list}")

        # Import and create scanner
        from .config_compliance import AWSConfigCompliance

        logger.info("Starting AWS Config compliance sync to RegScale...")

        scanner = AWSConfigCompliance(
            plan_id=regscale_id,
            region=resolved_region,
            profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            account_id=account_id,
            tags=parsed_tags,
            framework=framework,
            conformance_pack_name=conformance_pack_name,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_as_attachments=evidence_as_attachments,
            evidence_as_records=evidence_as_records,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            use_security_hub=use_security_hub,
            force_refresh=force_refresh,
        )

        scanner.sync_compliance()

        logger.info("AWS Config compliance sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS Config compliance: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_kms")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region to collect KMS key data from",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale SSP ID to create evidence and compliance assessments under.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter KMS keys by AWS account ID (extracted from key ARN)",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter KMS keys by tags (format: key1=value1,key2=value2). All specified tags must match (AND logic).",
)
@click.option(
    "--framework",
    type=click.Choice(["NIST800-53R5", "ISO27001"], case_sensitive=False),
    default="NIST800-53R5",
    help="Compliance framework for KMS key assessments (default: NIST800-53R5)",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for non-compliant KMS keys (default: True)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on KMS compliance results (default: True)",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=False,
    help="Collect and store KMS key evidence artifacts (default: False)",
)
@click.option(
    "--evidence-as-attachments/--evidence-as-records",
    "evidence_as_attachments",
    default=True,
    help="Attach evidence files to SSP (default) vs create individual Evidence records",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'SC-12,SC-13,SC-28')",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--force-refresh",
    "-f",
    is_flag=True,
    default=False,
    help="Force refresh KMS data by bypassing cache (cache TTL: 4 hours)",
)
@click.pass_context
def sync_kms(ctx, **kwargs) -> None:
    """
    Sync AWS KMS encryption key data to RegScale for compliance evidence and control assessments.

    This command collects AWS KMS key metadata, rotation status, and policies, then:
    - Assesses each key against NIST 800-53 controls (SC-12, SC-13, SC-28)
    - Creates control assessments in RegScale with PASS/FAIL status
    - Creates issues for non-compliant keys (e.g., rotation disabled)
    - Optionally collects evidence artifacts for compliance documentation

    KMS Compliance Checks:
    - SC-12 (Key Management): Key rotation enabled, proper lifecycle management
    - SC-13 (Cryptographic Protection): FIPS-validated algorithms, approved key specs
    - SC-28 (Data at Rest): Keys enabled and available for encryption

    Filtering Options:
    Use --account-id to filter keys by AWS account (extracted from key ARN).
    Use --tags to filter keys by tags (format: key1=value1,key2=value2).
    Both filters use AND logic - all criteria must match.

    Evidence Collection:
    Use --collect-evidence to create evidence artifacts for compliance documentation.
    By default, evidence is attached directly to the SSP as JSONL.GZ files.
    Use --evidence-as-records to create individual Evidence records instead.
    Optionally filter evidence by control IDs with --evidence-control-ids.

    Caching:
    KMS data is cached for 4 hours to reduce API calls. Use --force-refresh to bypass cache.

    Authentication methods (in priority order):
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain

    Examples:
    # Basic compliance sync with evidence collection
    regscale aws sync_kms --regscale_id 123 --collect-evidence

    # Filter by account and tags
    regscale aws sync_kms --regscale_id 123 --account-id 123456789012 \\
        --tags Environment=prod,Team=security

    # Create individual evidence records (not SSP attachments)
    regscale aws sync_kms --regscale_id 123 --collect-evidence \\
        --evidence-as-records

    # Force refresh to bypass cache
    regscale aws sync_kms --regscale_id 123 --force-refresh
    """
    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        framework = kwargs.get("framework", "NIST800-53R5")
        create_issues = kwargs.get("create_issues", True)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", False)
        evidence_as_attachments = kwargs.get("evidence_as_attachments", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        force_refresh = kwargs.get("force_refresh", False)

        logger.info("Starting AWS KMS compliance sync to RegScale...")

        # Resolve AWS credentials
        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name,
            profile,
            aws_access_key_id,
            aws_secret_access_key,
            aws_session_token,
            region,
        )

        # Log credential resolution results
        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        # Parse tags
        parsed_tags = parse_tags(tags)

        # Log filtering information
        if account_id:
            logger.info(f"Filtering KMS keys by account ID: {account_id}")
        if parsed_tags:
            logger.info(f"Filtering KMS keys by tags: {parsed_tags}")

        # Parse evidence control IDs
        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {evidence_control_list}")

        # Log evidence collection mode
        if collect_evidence:
            if evidence_as_attachments:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            else:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        # Import and create KMS evidence integration
        from .kms_evidence import AWSKMSEvidenceIntegration, KMSEvidenceConfig

        # Create configuration object
        config = KMSEvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_as_attachments=evidence_as_attachments,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            force_refresh=force_refresh,
            account_id=account_id,
            tags=parsed_tags,
            profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSKMSEvidenceIntegration(config)

        scanner.sync_compliance()

        logger.info("AWS KMS compliance sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS KMS compliance: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_org")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region for Organizations API access",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale SSP ID to create evidence and compliance assessments under.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--framework",
    type=click.Choice(["NIST800-53R5", "ISO27001"], case_sensitive=False),
    default="NIST800-53R5",
    help="Compliance framework for Organizations assessments (default: NIST800-53R5)",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for non-compliant organization (default: True)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on Organizations compliance (default: True)",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=False,
    help="Collect and store Organizations evidence artifacts (default: False)",
)
@click.option(
    "--evidence-as-attachments/--evidence-as-records",
    "evidence_as_attachments",
    default=True,
    help="Attach evidence files to SSP (default) vs create individual Evidence records",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'AC-1,PM-9,AC-2')",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--force-refresh",
    "-f",
    is_flag=True,
    default=False,
    help="Force refresh Organizations data by bypassing cache (cache TTL: 4 hours)",
)
@click.pass_context
def sync_org(ctx, **kwargs) -> None:
    """
    Sync AWS Organizations data to RegScale for governance and compliance evidence.

    This command collects AWS Organizations structure, accounts, OUs, and SCPs, then:
    - Assesses organization against NIST 800-53 controls (AC-1, PM-9, AC-2, AC-6)
    - Creates control assessments in RegScale with PASS/FAIL status
    - Creates issues for non-compliant configurations
    - Optionally collects evidence artifacts for compliance documentation

    Organizations Compliance Checks:
    - AC-1 (Access Control Policy): SCP enforcement, OU structure
    - PM-9 (Risk Management): Environment separation, restrictive SCPs
    - AC-2 (Account Management): Account status, contact information
    - AC-6 (Least Privilege): Restrictive SCPs, deny policies

    Evidence Collection:
    Use --collect-evidence to create evidence artifacts for compliance documentation.
    By default, evidence is attached directly to the SSP as JSONL.GZ files.
    Use --evidence-as-records to create individual Evidence records instead.

    Caching:
    Organizations data is cached for 4 hours. Use --force-refresh to bypass cache.

    Authentication:
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain

    Examples:
    # Basic compliance sync with evidence
    regscale aws sync_org --regscale_id 123 --collect-evidence

    # Create individual evidence records
    regscale aws sync_org --regscale_id 123 --collect-evidence --evidence-as-records

    # Force refresh with specific controls
    regscale aws sync_org --regscale_id 123 --collect-evidence \\
        --evidence-control-ids AC-1,PM-9 --force-refresh
    """
    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        framework = kwargs.get("framework", "NIST800-53R5")
        create_issues = kwargs.get("create_issues", True)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", False)
        evidence_as_attachments = kwargs.get("evidence_as_attachments", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        force_refresh = kwargs.get("force_refresh", False)

        logger.info("Starting AWS Organizations compliance sync to RegScale...")

        # Resolve credentials
        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        # Parse evidence control IDs
        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {evidence_control_list}")

        # Log evidence collection mode
        if collect_evidence:
            if evidence_as_attachments:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            else:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        # Import and create Organizations evidence integration
        from .org_evidence import AWSOrganizationsEvidenceIntegration

        scanner = AWSOrganizationsEvidenceIntegration(
            plan_id=regscale_id,
            region=resolved_region,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_as_attachments=evidence_as_attachments,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            force_refresh=force_refresh,
            profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner.sync_compliance()

        logger.info("AWS Organizations compliance sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS Organizations compliance: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_iam")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region for IAM API access",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale SSP ID to create evidence and compliance assessments under.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--framework",
    type=click.Choice(["NIST800-53R5", "ISO27001"], case_sensitive=False),
    default="NIST800-53R5",
    help="Compliance framework for IAM assessments (default: NIST800-53R5)",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=True,
    help="Create issues for non-compliant IAM configurations (default: True)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on IAM compliance (default: True)",
)
@click.option(
    "--create-poams",
    "-cp",
    is_flag=True,
    default=False,
    help="Mark created issues as POAMs (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=False,
    help="Collect and store IAM evidence artifacts (default: False)",
)
@click.option(
    "--evidence-as-attachments/--evidence-as-records",
    "evidence_as_attachments",
    default=True,
    help="Attach evidence files to SSP (default) vs create individual Evidence records",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'AC-2,IA-2,AC-6')",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--force-refresh",
    "-f",
    is_flag=True,
    default=False,
    help="Force refresh IAM data by bypassing cache (cache TTL: 4 hours)",
)
@click.pass_context
def sync_iam(ctx, **kwargs) -> None:
    """
    Sync AWS IAM data to RegScale for access control and authentication evidence.

    This command collects AWS IAM users, groups, roles, and policies, then:
    - Assesses IAM against NIST 800-53 controls (AC-2, AC-6, IA-2, IA-5, AC-3)
    - Creates control assessments in RegScale with PASS/FAIL status
    - Creates issues for non-compliant configurations
    - Optionally collects evidence artifacts for compliance documentation

    IAM Compliance Checks:
    - AC-2 (Account Management): MFA enforcement, root account security
    - AC-6 (Least Privilege): No users with AdministratorAccess
    - IA-2 (Authentication): Strong password policy, MFA required
    - IA-5 (Authenticator Management): Access key rotation, unused credentials
    - AC-3 (Access Enforcement): Restrictive role trust policies

    Evidence Collection:
    Use --collect-evidence to create evidence artifacts for compliance documentation.
    By default, evidence is attached directly to the SSP as JSONL.GZ files.
    Use --evidence-as-records to create individual Evidence records instead.

    Caching:
    IAM data is cached for 4 hours. Use --force-refresh to bypass cache.

    Authentication:
    1. Cached session: --session-name (from 'regscale aws auth login')
    2. Explicit credentials: --aws_access_key_id + --aws_secret_access_key
    3. AWS profile: --profile
    4. Environment variables or default AWS credential chain

    Examples:
    # Basic compliance sync with evidence
    regscale aws sync_iam --regscale_id 123 --collect-evidence

    # Create individual evidence records
    regscale aws sync_iam --regscale_id 123 --collect-evidence --evidence-as-records

    # Force refresh with specific controls
    regscale aws sync_iam --regscale_id 123 --collect-evidence \\
        --evidence-control-ids AC-2,IA-2,AC-6 --force-refresh
    """
    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        framework = kwargs.get("framework", "NIST800-53R5")
        create_issues = kwargs.get("create_issues", True)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", False)
        evidence_as_attachments = kwargs.get("evidence_as_attachments", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        force_refresh = kwargs.get("force_refresh", False)

        logger.info("Starting AWS IAM compliance sync to RegScale...")

        # Resolve credentials
        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        # Parse evidence control IDs
        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {evidence_control_list}")

        # Log evidence collection mode
        if collect_evidence:
            if evidence_as_attachments:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            else:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        # Import and create IAM evidence integration
        from .iam_evidence import AWSIAMEvidenceIntegration

        scanner = AWSIAMEvidenceIntegration(
            plan_id=regscale_id,
            region=resolved_region,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_as_attachments=evidence_as_attachments,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            force_refresh=force_refresh,
            profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner.sync_compliance()

        logger.info("AWS IAM compliance sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS IAM compliance: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_guardduty")
@click.option(
    "--region",
    type=str,
    default=os.environ.get("AWS_REGION", "us-east-1"),
    help="AWS region for GuardDuty API access",
)
@click.option(
    "--regscale_id",
    "--id",
    type=click.INT,
    help="RegScale SSP ID to create findings and evidence under.",
    required=True,
)
@click.option(
    "--session-name",
    type=str,
    required=False,
    help="Name of cached AWS session to use (from 'regscale aws auth login')",
)
@click.option(
    "--profile",
    type=str,
    required=False,
    help="AWS profile name from ~/.aws/credentials",
    envvar="AWS_PROFILE",
)
@click.option(
    "--aws_access_key_id",
    type=str,
    required=False,
    help="AWS access key ID (overrides profile)",
    envvar="AWS_ACCESS_KEY_ID",
)
@click.option(
    "--aws_secret_access_key",
    type=str,
    required=False,
    help="AWS secret access key (overrides profile)",
    default=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws_session_token",
    type=click.STRING,
    required=False,
    help="AWS session token (overrides profile)",
    default=os.environ.get("AWS_SESSION_TOKEN"),
)
@click.option(
    "--account-id",
    type=str,
    required=False,
    help="Filter GuardDuty findings by AWS account ID",
)
@click.option(
    "--tags",
    type=str,
    required=False,
    help="Filter GuardDuty detectors by tags (format: key1=value1,key2=value2)",
)
@click.option(
    "--framework",
    type=click.Choice(["NIST800-53R5"], case_sensitive=False),
    default="NIST800-53R5",
    help="Compliance framework for GuardDuty assessments (default: NIST800-53R5)",
)
@click.option(
    "--create-issues/--no-create-issues",
    default=False,
    help="Create issues for GuardDuty findings without CVEs (default: False)",
)
@click.option(
    "--create-vulnerabilities/--no-create-vulnerabilities",
    default=False,
    help="Create vulnerabilities for GuardDuty findings with CVEs (default: False)",
)
@click.option(
    "--update-control-status/--no-update-control-status",
    default=True,
    help="Update control implementation status based on findings (default: True)",
)
@click.option(
    "--create-poams/--no-create-poams",
    default=False,
    help="Create POA&Ms for failed controls (default: False)",
)
@click.option(
    "--collect-evidence/--no-collect-evidence",
    default=True,
    help="Collect and store GuardDuty evidence artifacts (default: True)",
)
@click.option(
    "--evidence-as-attachments/--evidence-as-records",
    "evidence_as_attachments",
    default=True,
    help="Attach evidence files to SSP (default) vs create individual Evidence records",
)
@click.option(
    "--evidence-control-ids",
    type=str,
    required=False,
    help="Comma-separated list of control IDs to collect evidence for (e.g., 'SI-4,IR-4,IR-5')",
)
@click.option(
    "--evidence-frequency",
    type=int,
    default=30,
    help="Evidence update frequency in days (default: 30)",
)
@click.option(
    "--force-refresh",
    "-f",
    is_flag=True,
    default=False,
    help="Force refresh GuardDuty data by bypassing cache (cache TTL: 4 hours)",
)
@click.pass_context
def sync_guardduty(ctx, **kwargs) -> None:
    """
    Sync AWS GuardDuty threat detection data to RegScale as compliance evidence.

    Collects GuardDuty detector configurations and findings for compliance assessment
    against NIST 800-53 R5 controls. By default, creates evidence attachments only
    (no issues or vulnerabilities).

    GuardDuty Compliance Checks:
    - SI-4 (System Monitoring): Detector enabled and configured
    - IR-4 (Incident Handling): Finding detection and alerting
    - IR-5 (Incident Monitoring): Continuous threat monitoring
    - SI-3 (Malicious Code Protection): Malware detection capabilities
    - RA-5 (Vulnerability Monitoring): Threat intelligence integration

    Examples:
    # Basic evidence collection (default)
    regscale aws sync_guardduty --regscale_id 123

    # Collect evidence for specific controls
    regscale aws sync_guardduty --regscale_id 123 --evidence-control-ids SI-4,IR-4,IR-5

    # Filter by AWS account
    regscale aws sync_guardduty --regscale_id 123 --account-id 123456789012

    # Create issues/vulnerabilities from findings (non-default)
    regscale aws sync_guardduty --regscale_id 123 --create-issues --create-vulnerabilities --no-collect-evidence
    """
    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        framework = kwargs.get("framework", "NIST800-53R5")
        create_issues = kwargs.get("create_issues", False)
        create_vulnerabilities = kwargs.get("create_vulnerabilities", False)
        update_control_status = kwargs.get("update_control_status", True)
        create_poams = kwargs.get("create_poams", False)
        collect_evidence = kwargs.get("collect_evidence", True)
        evidence_as_attachments = kwargs.get("evidence_as_attachments", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        evidence_frequency = kwargs.get("evidence_frequency", 30)
        force_refresh = kwargs.get("force_refresh", False)

        logger.info("Starting AWS GuardDuty findings sync to RegScale...")

        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        parsed_tags = parse_tags(tags)

        if account_id:
            logger.info(f"Filtering GuardDuty findings by account ID: {account_id}")
        if parsed_tags:
            logger.info(f"Filtering GuardDuty detectors by tags: {parsed_tags}")

        evidence_control_list = None
        if evidence_control_ids:
            evidence_control_list = [cid.strip() for cid in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {evidence_control_list}")

        if collect_evidence:
            if evidence_as_attachments:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            else:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        from .guardduty_evidence import AWSGuardDutyEvidenceIntegration, GuardDutyEvidenceConfig

        # Create configuration object
        config = GuardDutyEvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            framework=framework,
            create_issues=create_issues,
            create_vulnerabilities=create_vulnerabilities,
            update_control_status=update_control_status,
            create_poams=create_poams,
            collect_evidence=collect_evidence,
            evidence_as_attachments=evidence_as_attachments,
            evidence_control_ids=evidence_control_list,
            evidence_frequency=evidence_frequency,
            force_refresh=force_refresh,
            account_id=account_id,
            tags=parsed_tags,
            profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSGuardDutyEvidenceIntegration(config)

        scanner.sync_findings()

        logger.info("AWS GuardDuty findings sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS GuardDuty findings: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_s3")
@click.option("--region", default="us-east-1", help="AWS region to collect S3 buckets from")
@click.option("--regscale-id", type=int, required=True, help="RegScale SSP plan ID")
@click.option("--account-id", help="AWS account ID to filter resources")
@click.option("--tags", help="Resource tags for filtering (format: key1=value1,key2=value2)")
@click.option("--bucket-name-filter", help="Filter buckets by name prefix/pattern")
@click.option("--create-evidence", is_flag=True, default=False, help="Create evidence records in RegScale")
@click.option(
    "--create-ssp-attachment",
    is_flag=True,
    default=True,
    help="Create SSP attachment with evidence (default: True)",
)
@click.option(
    "--evidence-control-ids",
    help="Comma-separated control IDs to link evidence (e.g., SC-13,SC-28,AC-3)",
)
@click.option("--force-refresh", is_flag=True, default=False, help="Force refresh cached data")
@click.option("--session-name", help="Custom session name for this operation")
@click.option("--profile", help="AWS profile name to use for authentication")
@click.option("--aws-access-key-id", help="AWS access key ID")
@click.option("--aws-secret-access-key", help="AWS secret access key")
@click.option("--aws-session-token", help="AWS session token")
@click.pass_context
def sync_s3(ctx, **kwargs):
    """
    Sync AWS S3 storage configurations to RegScale as compliance evidence.

    Collects S3 bucket configurations including encryption, versioning, logging,
    access controls, and public access settings for compliance assessment against
    NIST 800-53 R5 controls (SC-13, SC-28, AC-3, AC-6, AU-2, AU-9, CP-9).

    Examples:

        # Sync all S3 buckets in us-east-1
        regscale aws sync_s3 --region us-east-1 --regscale-id 123

        # Filter by bucket name prefix
        regscale aws sync_s3 --region us-east-1 --regscale-id 123 --bucket-name-filter prod-

        # Filter by tags
        regscale aws sync_s3 --region us-east-1 --regscale-id 123 --tags Environment=Production,Compliance=Required

        # Create evidence and link to controls
        regscale aws sync_s3 --region us-east-1 --regscale-id 123 --create-evidence \\
            --evidence-control-ids SC-13,SC-28,AC-3

        # Use specific AWS profile
        regscale aws sync_s3 --region us-west-2 --regscale-id 456 --profile production

        # Force refresh cached data
        regscale aws sync_s3 --region us-east-1 --regscale-id 123 --force-refresh
    """
    from regscale.integrations.commercial.aws.s3_evidence import AWSS3EvidenceIntegration

    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        bucket_name_filter = kwargs.get("bucket_name_filter")
        create_evidence = kwargs.get("create_evidence", False)
        create_ssp_attachment = kwargs.get("create_ssp_attachment", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        force_refresh = kwargs.get("force_refresh", False)
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        logger.info("Starting AWS S3 storage configuration sync to RegScale...")

        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        parsed_tags = parse_tags(tags)

        if account_id:
            logger.info(f"Filtering S3 buckets by account ID: {account_id}")

        if parsed_tags:
            logger.info(f"Filtering S3 buckets by tags: {parsed_tags}")

        if bucket_name_filter:
            logger.info(f"Filtering S3 buckets by name pattern: {bucket_name_filter}")

        control_ids = None
        if evidence_control_ids:
            control_ids = [ctrl.strip() for ctrl in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {control_ids}")

        if create_evidence or create_ssp_attachment:
            if create_ssp_attachment:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            if create_evidence:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        from .s3_evidence import AWSS3EvidenceIntegration, S3EvidenceConfig

        # Create configuration object
        config = S3EvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            account_id=account_id,
            tags=parsed_tags,
            bucket_name_filter=bucket_name_filter,
            create_evidence=create_evidence,
            create_ssp_attachment=create_ssp_attachment,
            evidence_control_ids=control_ids,
            force_refresh=force_refresh,
            aws_profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSS3EvidenceIntegration(config)

        scanner.sync_compliance_data()

        logger.info("AWS S3 evidence sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS S3 evidence: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_cloudtrail")
@click.option("--region", default="us-east-1", help="AWS region to collect CloudTrail trails from")
@click.option("--regscale-id", type=int, required=True, help="RegScale SSP plan ID")
@click.option("--account-id", help="AWS account ID to filter resources")
@click.option("--tags", help="Resource tags for filtering (format: key1=value1,key2=value2)")
@click.option("--trail-name-filter", help="Filter trails by name prefix/pattern")
@click.option("--create-evidence", is_flag=True, default=False, help="Create evidence records in RegScale")
@click.option(
    "--create-ssp-attachment",
    is_flag=True,
    default=True,
    help="Create SSP attachment with evidence (default: True)",
)
@click.option(
    "--evidence-control-ids",
    help="Comma-separated control IDs to link evidence (e.g., AU-2,AU-3,AU-6)",
)
@click.option("--force-refresh", is_flag=True, default=False, help="Force refresh cached data")
@click.option("--session-name", help="Custom session name for this operation")
@click.option("--profile", help="AWS profile name to use for authentication")
@click.option("--aws-access-key-id", help="AWS access key ID")
@click.option("--aws-secret-access-key", help="AWS secret access key")
@click.option("--aws-session-token", help="AWS session token")
@click.pass_context
def sync_cloudtrail(ctx, **kwargs):
    """
    Sync AWS CloudTrail audit logging configurations to RegScale as compliance evidence.

    Collects CloudTrail trail configurations including logging status, multi-region settings,
    log file validation, encryption, CloudWatch Logs integration, and SNS notifications for
    compliance assessment against NIST 800-53 R5 controls (AU-2, AU-3, AU-6, AU-9, AU-11, AU-12, SI-4).

    Examples:

        # Sync all CloudTrail trails in us-east-1
        regscale aws sync_cloudtrail --region us-east-1 --regscale-id 123

        # Filter by trail name prefix
        regscale aws sync_cloudtrail --region us-east-1 --regscale-id 123 --trail-name-filter prod-

        # Filter by tags
        regscale aws sync_cloudtrail --region us-east-1 --regscale-id 123 --tags Environment=Production

        # Create evidence and link to controls
        regscale aws sync_cloudtrail --region us-east-1 --regscale-id 123 --create-evidence \\
            --evidence-control-ids AU-2,AU-3,AU-6,AU-9

        # Use specific AWS profile
        regscale aws sync_cloudtrail --region us-west-2 --regscale-id 456 --profile production

        # Force refresh cached data
        regscale aws sync_cloudtrail --region us-east-1 --regscale-id 123 --force-refresh
    """
    from regscale.integrations.commercial.aws.cloudtrail_evidence import AWSCloudTrailEvidenceIntegration

    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        trail_name_filter = kwargs.get("trail_name_filter")
        create_evidence = kwargs.get("create_evidence", False)
        create_ssp_attachment = kwargs.get("create_ssp_attachment", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        force_refresh = kwargs.get("force_refresh", False)
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        logger.info("Starting AWS CloudTrail audit logging sync to RegScale...")

        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        parsed_tags = parse_tags(tags)

        if account_id:
            logger.info(f"Filtering CloudTrail trails by account ID: {account_id}")

        if parsed_tags:
            logger.info(f"Filtering CloudTrail trails by tags: {parsed_tags}")

        if trail_name_filter:
            logger.info(f"Filtering CloudTrail trails by name pattern: {trail_name_filter}")

        control_ids = None
        if evidence_control_ids:
            control_ids = [ctrl.strip() for ctrl in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {control_ids}")

        if create_evidence or create_ssp_attachment:
            if create_ssp_attachment:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            if create_evidence:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        from .cloudtrail_evidence import AWSCloudTrailEvidenceIntegration, CloudTrailEvidenceConfig

        # Create configuration object
        config = CloudTrailEvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            account_id=account_id,
            tags=parsed_tags,
            trail_name_filter=trail_name_filter,
            create_evidence=create_evidence,
            create_ssp_attachment=create_ssp_attachment,
            evidence_control_ids=control_ids,
            force_refresh=force_refresh,
            aws_profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSCloudTrailEvidenceIntegration(config)

        scanner.sync_compliance_data()

        logger.info("AWS CloudTrail evidence sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS CloudTrail evidence: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_ssm")
@click.option("--region", default="us-east-1", help="AWS region to sync from")
@click.option("--regscale-id", type=int, required=True, help="RegScale SSP ID to attach evidence")
@click.option("--account-id", help="Optional AWS account ID to filter resources")
@click.option("--tags", help='Optional tags to filter resources (format: "Key1=Value1,Key2=Value2")')
@click.option("--create-evidence", is_flag=True, default=False, help="Create evidence records (default: False)")
@click.option("--create-ssp-attachment", is_flag=True, default=True, help="Create SSP attachments (default: True)")
@click.option("--evidence-control-ids", help='Control IDs for evidence (comma-separated, e.g., "CM-2,CM-6,SI-2")')
@click.option("--force-refresh", is_flag=True, default=False, help="Force cache refresh")
@click.option("--session-name", help="AWS session name for role assumption")
@click.option("--profile", help="AWS profile name to use")
@click.option("--aws-access-key-id", help="AWS access key ID")
@click.option("--aws-secret-access-key", help="AWS secret access key")
@click.option("--aws-session-token", help="AWS session token")
@click.pass_context
def sync_ssm(ctx, **kwargs):
    """Sync AWS Systems Manager configurations to RegScale as compliance evidence.

    This command collects SSM configuration data including managed instances, patch baselines,
    parameters, documents, maintenance windows, and compliance status for NIST 800-53 R5
    controls (CM-2, CM-6, SI-2, CM-3, CM-8).

    Examples:
        # Sync SSM evidence with default settings
        regscale commercial aws sync_ssm --regscale-id 123

        # Sync with specific AWS profile
        regscale commercial aws sync_ssm --regscale-id 123 --profile prod-account

        # Force refresh cache and filter by tags
        regscale commercial aws sync_ssm --regscale-id 123 --force-refresh --tags "Environment=Production"

        # Sync for specific account
        regscale commercial aws sync_ssm --regscale-id 123 --account-id 123456789012
    """
    from regscale.integrations.commercial.aws.ssm_evidence import AWSSSMEvidenceIntegration

    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        create_evidence = kwargs.get("create_evidence", False)
        create_ssp_attachment = kwargs.get("create_ssp_attachment", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        force_refresh = kwargs.get("force_refresh", False)
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        # Resolve AWS credentials
        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        # Parse tags if provided
        parsed_tags = parse_tags(tags)

        # Parse control IDs if provided
        control_ids = [ctrl.strip() for ctrl in evidence_control_ids.split(",")] if evidence_control_ids else None

        logger.info(f"Starting AWS Systems Manager evidence sync for region: {resolved_region}")

        from .ssm_evidence import AWSSSMEvidenceIntegration, SSMEvidenceConfig

        # Create configuration object
        config = SSMEvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            account_id=account_id,
            tags=parsed_tags,
            create_evidence=create_evidence,
            create_ssp_attachment=create_ssp_attachment,
            evidence_control_ids=control_ids,
            force_refresh=force_refresh,
            aws_profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSSSMEvidenceIntegration(config)

        scanner.sync_compliance_data()

        logger.info("AWS Systems Manager evidence sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS Systems Manager evidence: {e}", exc_info=True)
        raise click.ClickException(str(e))


@awsv2.command(name="sync_cloudwatch")
@click.option("--region", default="us-east-1", help="AWS region to collect CloudWatch Logs from")
@click.option("--regscale-id", type=int, required=True, help="RegScale SSP plan ID")
@click.option("--account-id", help="AWS account ID to filter resources")
@click.option("--tags", help="Resource tags for filtering (format: key1=value1,key2=value2)")
@click.option("--log-group-prefix", help="Filter log groups by name prefix")
@click.option("--create-evidence", is_flag=True, default=False, help="Create evidence records in RegScale")
@click.option(
    "--create-ssp-attachment",
    is_flag=True,
    default=True,
    help="Create SSP attachment with evidence (default: True)",
)
@click.option(
    "--evidence-control-ids",
    help="Comma-separated control IDs to link evidence (e.g., AU-2,AU-3,AU-6)",
)
@click.option("--force-refresh", is_flag=True, default=False, help="Force refresh cached data")
@click.option("--session-name", help="Custom session name for this operation")
@click.option("--profile", help="AWS profile name to use for authentication")
@click.option("--aws-access-key-id", help="AWS access key ID")
@click.option("--aws-secret-access-key", help="AWS secret access key")
@click.option("--aws-session-token", help="AWS session token")
@click.pass_context
def sync_cloudwatch(ctx, **kwargs):
    """
    Sync AWS CloudWatch Logs configurations to RegScale as compliance evidence.

    Collects CloudWatch log group configurations including retention policies, encryption status,
    metric filters, subscription filters, and storage metrics for compliance assessment against
    NIST 800-53 R5 controls (AU-2, AU-3, AU-6, AU-9, AU-11, AU-12, SI-4).

    Examples:

        # Sync all CloudWatch log groups in us-east-1
        regscale aws sync_cloudwatch --region us-east-1 --regscale-id 123

        # Filter by log group name prefix
        regscale aws sync_cloudwatch --region us-east-1 --regscale-id 123 --log-group-prefix /aws/lambda/

        # Filter by tags
        regscale aws sync_cloudwatch --region us-east-1 --regscale-id 123 --tags Environment=Production

        # Create evidence and link to controls
        regscale aws sync_cloudwatch --region us-east-1 --regscale-id 123 --create-evidence --evidence-control-ids AU-2,AU-3,AU-6,AU-9

        # Use specific AWS profile
        regscale aws sync_cloudwatch --region us-west-2 --regscale-id 456 --profile production

        # Force refresh cached data
        regscale aws sync_cloudwatch --region us-east-1 --regscale-id 123 --force-refresh
    """
    from regscale.integrations.commercial.aws.cloudwatch_evidence import AWSCloudWatchEvidenceIntegration

    try:
        # Extract parameters from kwargs
        region = kwargs["region"]
        regscale_id = kwargs["regscale_id"]
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        log_group_prefix = kwargs.get("log_group_prefix")
        create_evidence = kwargs.get("create_evidence", False)
        create_ssp_attachment = kwargs.get("create_ssp_attachment", True)
        evidence_control_ids = kwargs.get("evidence_control_ids")
        force_refresh = kwargs.get("force_refresh", False)
        session_name = kwargs.get("session_name")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        logger.info("Starting AWS CloudWatch Logs sync to RegScale...")

        resolved_profile, access_key, secret_key, session_token, resolved_region = resolve_aws_credentials(
            session_name, profile, aws_access_key_id, aws_secret_access_key, aws_session_token, region
        )

        logger.info(
            f"Using AWS credentials - profile: {resolved_profile if resolved_profile else 'not set'}, "
            f"explicit credentials: {'yes' if access_key else 'no'}, region: {resolved_region}"
        )

        parsed_tags = parse_tags(tags)

        if account_id:
            logger.info(f"Filtering CloudWatch log groups by account ID: {account_id}")

        if parsed_tags:
            logger.info(f"Filtering CloudWatch log groups by tags: {parsed_tags}")

        if log_group_prefix:
            logger.info(f"Filtering CloudWatch log groups by name prefix: {log_group_prefix}")

        control_ids = None
        if evidence_control_ids:
            control_ids = [ctrl.strip() for ctrl in evidence_control_ids.split(",")]
            logger.info(f"Evidence collection requested for controls: {control_ids}")

        if create_evidence or create_ssp_attachment:
            if create_ssp_attachment:
                logger.info(EVIDENCE_MODE_SSP_ATTACHMENTS)
            if create_evidence:
                logger.info(EVIDENCE_MODE_INDIVIDUAL_RECORDS)

        from .cloudwatch_evidence import AWSCloudWatchEvidenceIntegration, CloudWatchEvidenceConfig

        # Create configuration object
        config = CloudWatchEvidenceConfig(
            plan_id=regscale_id,
            region=resolved_region,
            account_id=account_id,
            tags=parsed_tags,
            log_group_prefix=log_group_prefix,
            create_evidence=create_evidence,
            create_ssp_attachment=create_ssp_attachment,
            evidence_control_ids=control_ids,
            force_refresh=force_refresh,
            aws_profile=resolved_profile,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
        )

        scanner = AWSCloudWatchEvidenceIntegration(config)

        scanner.sync_compliance_data()

        logger.info("AWS CloudWatch Logs evidence sync completed successfully")

    except Exception as e:
        logger.error(f"Error syncing AWS CloudWatch Logs evidence: {e}", exc_info=True)
        raise click.ClickException(str(e))
