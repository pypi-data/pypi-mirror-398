"""QRadar Events Connector Model for RegScale Integration"""

import logging
from datetime import datetime, timedelta
from typing import Iterator, Optional, Dict, Any, List

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.scanner_integration import (
    IntegrationAsset,
    IntegrationFinding,
    ScannerIntegration,
    ScannerIntegrationType,
)
from regscale.models.integration_models.qradar_models.event import QRadarEvent
from regscale.models.regscale_models import (
    IssueSeverity,
    AssetStatus,
    IssueStatus,
)

logger = logging.getLogger("regscale")


class QRadarIntegration(ScannerIntegration):
    """
    QRadar SIEM integration for RegScale.

    This integration syncs security events and findings from IBM QRadar SIEM
    into RegScale for compliance and risk management.

    Supports:
    - Asset synchronization from QRadar events
    - Finding/issue creation from security events
    - Control mapping for compliance frameworks
    - Event correlation and aggregation

    Example usage:
        >>> from regscale.integrations.commercial.qradar.qradar_api_client import QRadarAPIClient
        >>> client = QRadarAPIClient(
        ...     base_url="https://qradar.example.com",
        ...     api_key="your-api-key"
        ... )
        >>> integration = QRadarIntegration(
        ...     plan_id=123,
        ...     qradar_client=client,
        ...     time_window_hours=24
        ... )
        >>> integration.sync_assets(plan_id=123)
        >>> integration.sync_findings(plan_id=123)
    """

    # Required fields from ScannerIntegration
    title = "QRadar"
    asset_identifier_field = "ipAddress"  # Primary field for asset identification - can be overridden for AWS accounts

    # Map QRadar severity levels to RegScale IssueSeverity
    # NOTE: This map is kept for backwards compatibility but is no longer used
    # Severity mapping now uses bin ranges (see _create_finding_from_event method)
    # following the AWS GuardDuty pattern: QRadar 0-10 → IssueSeverity bins
    finding_severity_map = {
        "10": IssueSeverity.Critical,  # QRadar severity 10 (Critical)
        "9": IssueSeverity.Critical,  # QRadar severity 9 (Critical)
        "8": IssueSeverity.High,  # QRadar severity 8 (High)
        "7": IssueSeverity.High,  # QRadar severity 7 (High)
        "6": IssueSeverity.Moderate,  # QRadar severity 6 (Medium)
        "5": IssueSeverity.Moderate,  # QRadar severity 5 (Medium)
        "4": IssueSeverity.Low,  # QRadar severity 4 (Low)
        "3": IssueSeverity.Low,  # QRadar severity 3 (Low)
        "2": IssueSeverity.Low,  # QRadar severity 2 (Info)
        "1": IssueSeverity.Low,  # QRadar severity 1 (Info)
        "0": IssueSeverity.NotAssigned,  # QRadar severity 0 (Unknown)
    }

    # Integration type - QRadar events should be created as Vulnerabilities and Issues
    # VULNERABILITY type creates both vulnerability records and linked issues
    type = ScannerIntegrationType.VULNERABILITY

    app = Application()

    def __init__(self, plan_id: int, *args, **kwargs):
        """
        Initialize QRadar integration.

        Args:
            plan_id: RegScale security plan ID
            *args: Additional positional arguments for ScannerIntegration
            **kwargs: Additional keyword arguments for ScannerIntegration
                - time_window_hours: Time window for fetching events (default: 24 hours)
                - severity_threshold: Minimum severity level to sync (default: 5)
                - verify_ssl: Whether to verify SSL certificates (default: from config)
                - base_url: QRadar instance URL (default: from config)
                - api_key: QRadar API key (default: from config)
        """
        super().__init__(plan_id, *args, **kwargs)

        # Lazy initialization - client created on first use
        self._qradar_client: Optional[Any] = None

        # Track discovered assets for sync_findings_and_assets
        self.discovered_assets: List[IntegrationAsset] = []
        self.processed_asset_identifiers: set = set()

        # Get configuration from kwargs or config file
        qradar_config = self.app.config.get("qradar", {})

        # Override config with kwargs if provided
        self.base_url = kwargs.get("base_url") or qradar_config.get("base_url")
        self.api_key = kwargs.get("api_key") or qradar_config.get("api_key")
        self.time_window_hours = kwargs.get("time_window_hours") or qradar_config.get("time_window_hours", 24)
        self.severity_threshold = kwargs.get("severity_threshold") or qradar_config.get("severity_threshold", 5)
        self.account_id_filter = kwargs.get("account_id_filter") or qradar_config.get("account_id_filter")
        verify_ssl_value = kwargs.get("verify_ssl")
        if verify_ssl_value is None:
            verify_ssl_value = qradar_config.get("verify_ssl", True)
        self.verify_ssl: bool = bool(verify_ssl_value)

        # Additional client configuration
        self.api_version = kwargs.get("api_version") or qradar_config.get("api_version")
        self.timeout = qradar_config.get("timeout", 60)  # Increased from 30 to 60 seconds for initial request
        self.max_retries = qradar_config.get("max_retries", 3)
        self.query_timeout = qradar_config.get("query_timeout", 900)  # Increased from 300 to 900 seconds (15 min)
        self.max_events = qradar_config.get("max_events", 10000)

        # Calculate time range for queries
        from datetime import timezone

        self.end_time = datetime.now(timezone.utc)
        self.start_time = self.end_time - timedelta(hours=self.time_window_hours)

        logger.info(
            f"QRadar integration initialized for plan {plan_id} "
            f"(time window: {self.time_window_hours}h, severity >= {self.severity_threshold})"
        )

    @property
    def qradar_client(self) -> Any:
        """
        Lazy initialization of QRadar API client.

        Returns:
            QRadarAPIClient instance

        Raises:
            ValueError: If base_url or api_key not configured
        """
        if self._qradar_client is None:
            # Validate required configuration
            if not self.base_url:
                raise ValueError(
                    "QRadar base_url required. Add to init.yaml under 'qradar' section or pass as --base-url"
                )
            if not self.api_key:
                raise ValueError(
                    "QRadar api_key required. Add to init.yaml under 'qradar' section or pass as --api-key"
                )

            # Import here to avoid circular dependencies
            from regscale.integrations.commercial.qradar.qradar_api_client import QRadarAPIClient

            logger.info(f"Creating QRadar API client for {self.base_url}")
            self._qradar_client = QRadarAPIClient(
                base_url=self.base_url,
                api_key=self.api_key,
                verify_ssl=self.verify_ssl,
                timeout=self.timeout,
                max_retries=self.max_retries,
                api_version=self.api_version,
            )

        return self._qradar_client

    def _set_integration_asset_defaults(self, asset: IntegrationAsset) -> IntegrationAsset:
        """
        Set default values for integration assets.

        Override parent method to NOT set asset_owner_id, as it may reference
        non-existent users in RegScale and cause 400 errors.

        Args:
            asset: The integration asset

        Returns:
            The asset with defaults set
        """
        # Don't set asset_owner_id - let RegScale handle it
        if not asset.status:
            asset.status = AssetStatus.Active
        return asset

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """
        Fetch assets from QRadar events.

        Extracts unique assets from QRadar security events based on:
        - AWS Account IDs (for CloudTrail events)
        - Source IP addresses
        - Destination IP addresses
        - Hostnames/FQDNs
        - Log sources

        Yields:
            IntegrationAsset objects for each unique asset discovered
        """
        logger.info("Fetching assets from QRadar events...")
        seen_assets: Dict[str, IntegrationAsset] = {}

        try:
            events = self._fetch_qradar_events()
            for event in events:
                yield from self._process_event_for_assets(event, seen_assets)

            logger.info(f"Fetched {len(seen_assets)} unique assets from QRadar")
            logger.debug(f"Asset identifiers: {list(seen_assets.keys())}")

        except Exception as e:
            logger.error(f"Error fetching assets from QRadar: {str(e)}")
            raise

    def _process_event_for_assets(
        self, event: QRadarEvent, seen_assets: Dict[str, IntegrationAsset]
    ) -> Iterator[IntegrationAsset]:
        """
        Process a single event to extract assets.

        Args:
            event: QRadarEvent to process
            seen_assets: Dictionary tracking already seen assets

        Yields:
            IntegrationAsset objects discovered from the event
        """
        # Check for AWS account-based asset first
        if event.account_id and event.account_id != "":
            yield from self._process_aws_account_asset(event, seen_assets)
            return  # Skip IP-based asset creation for CloudTrail events

        # Extract assets from source and destination IPs
        yield from self._process_source_ip_asset(event, seen_assets)
        yield from self._process_dest_ip_asset(event, seen_assets)

    def _process_aws_account_asset(
        self, event: QRadarEvent, seen_assets: Dict[str, IntegrationAsset]
    ) -> Iterator[IntegrationAsset]:
        """Process AWS account-based asset from event."""
        account_id = event.account_id
        if account_id and account_id not in seen_assets:
            asset = self._create_asset_from_event(event, "")
            seen_assets[account_id] = asset
            logger.debug(
                f"Created AWS account asset: {asset.name} (Account ID: {account_id}, identifier: {asset.identifier})"
            )
            yield asset

    def _process_source_ip_asset(
        self, event: QRadarEvent, seen_assets: Dict[str, IntegrationAsset]
    ) -> Iterator[IntegrationAsset]:
        """Process source IP asset from event."""
        if event.is_valid_source_asset() and event.source_ip:
            source_ip = event.source_ip
            if source_ip not in seen_assets:
                asset = self._create_asset_from_event(event, source_ip)
                seen_assets[source_ip] = asset
                logger.debug(
                    f"Created source asset: {asset.name} (IP: {asset.ip_address}, identifier: {asset.identifier})"
                )
                yield asset

    def _process_dest_ip_asset(
        self, event: QRadarEvent, seen_assets: Dict[str, IntegrationAsset]
    ) -> Iterator[IntegrationAsset]:
        """Process destination IP asset from event."""
        if event.is_valid_dest_asset() and event.dest_ip:
            dest_ip = event.dest_ip
            if dest_ip not in seen_assets:
                asset = self._create_asset_from_event(event, dest_ip)
                seen_assets[dest_ip] = asset
                logger.debug(
                    f"Created dest asset: {asset.name} (IP: {asset.ip_address}, identifier: {asset.identifier})"
                )
                yield asset

    def _determine_ip_asset_name(self, event: QRadarEvent, ip_address: str) -> str:
        """
        Determine asset name for IP-based assets.

        Args:
            event: QRadarEvent object
            ip_address: IP address for the asset

        Returns:
            Asset name string
        """
        import re

        # For IP addresses, try to use username or log source as name
        if event.username and event.username not in ["", "N/A", "Unknown", "unknown"]:
            sanitized_username = re.sub(r"[@\s]+", "-", event.username)
            return f"{sanitized_username}-{ip_address}"
        elif event.log_source and event.log_source not in ["Unknown Source", "N/A"]:
            log_source_parts = event.log_source.split()
            if log_source_parts:
                return f"{log_source_parts[0]}-{ip_address}"
        return f"host-{ip_address}"

    def _determine_ip_asset_category(self, ip_address: str, log_source_lower: str) -> tuple[str, str]:
        """
        Determine asset category and type for IP-based assets.

        Args:
            ip_address: IP address or hostname
            log_source_lower: Lowercase log source string

        Returns:
            Tuple of (asset_category, asset_type)
        """
        if "amazonaws.com" in ip_address:
            return "Cloud Service", "Cloud Resource"
        elif "windows" in log_source_lower:
            return "Windows System", "Server"
        elif "linux" in log_source_lower:
            return "Linux System", "Server"
        elif "firewall" in log_source_lower:
            return "Network Device", "Firewall"
        elif "ids" in log_source_lower or "ips" in log_source_lower:
            return "Security Device", "IDS/IPS"
        else:
            return "Unknown", "Other"

    def _build_asset_notes(self, event: QRadarEvent, log_source: str, has_account_id: bool) -> str:
        """
        Build notes string for asset with event information.

        Args:
            event: QRadarEvent object
            log_source: Log source string
            has_account_id: Whether this is an AWS account asset

        Returns:
            Notes string
        """
        notes_parts = [f"Log Source: {log_source}"]
        if has_account_id:
            notes_parts.append(f"AWS Account ID: {event.account_id}")
            if event.account_name:
                notes_parts.append(f"AWS Account Name: {event.account_name}")
            if event.aws_access_key_id:
                notes_parts.append(f"AWS Access Key ID: {event.aws_access_key_id}")
        return " | ".join(notes_parts)

    def _create_asset_from_event(self, event: QRadarEvent, ip_address: str) -> IntegrationAsset:
        """
        Create an IntegrationAsset from a QRadar event.

        For AWS CloudTrail events with account_id, uses account_id as the primary identifier.
        For other events, uses IP address or hostname.

        Args:
            event: QRadarEvent object
            ip_address: IP address or hostname for the asset

        Returns:
            IntegrationAsset object
        """
        import re

        # Check if this is an AWS CloudTrail event with account_id
        has_account_id = bool(event.account_id and event.account_id != "")
        log_source = event.log_source or "Unknown"
        log_source_lower = log_source.lower()

        # Determine asset properties based on event type
        if has_account_id:
            # AWS CloudTrail event
            identifier = event.account_id or ""
            aws_identifier = event.account_id
            asset_name = f"AWS-{event.account_name}" if event.account_name else f"AWS-Account-{event.account_id}"
            asset_category = "Cloud Service"
            asset_type = "AWS Account"
            description = f"AWS Account discovered from QRadar CloudTrail event: {event.event_name or 'Unknown'}"
            ip_for_asset = identifier
            fqdn = None
        else:
            # Traditional IP-based asset
            identifier = ip_address
            aws_identifier = None
            is_hostname = bool(re.search(r"[a-zA-Z]", ip_address))

            if is_hostname:
                asset_name = re.sub(r"[@\s]+", "-", ip_address)
            else:
                asset_name = self._determine_ip_asset_name(event, ip_address)

            asset_category, asset_type = self._determine_ip_asset_category(ip_address, log_source_lower)
            description = f"Asset discovered from QRadar event: {event.event_name or 'Unknown'}"
            ip_for_asset = ip_address
            fqdn = ip_address if is_hostname else None

        notes = self._build_asset_notes(event, log_source, has_account_id)

        return IntegrationAsset(
            name=asset_name,
            identifier=identifier,
            ip_address=ip_for_asset,
            aws_identifier=aws_identifier,
            fqdn=fqdn,
            asset_type=asset_type,
            asset_category=asset_category,
            status=AssetStatus.Active,
            date_last_updated=get_current_datetime(),
            description=description,
            scanning_tool="QRadar SIEM",
            is_latest_scan=True,
            notes=notes,
        )

    def fetch_findings(self, plan_id: int, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetch findings from QRadar events.

        Transforms QRadar security events into RegScale findings/issues with:
        - Event classification and severity mapping
        - Asset correlation
        - Control mapping based on event categories
        - Evidence linking

        Also discovers assets during finding processing and stores them
        in self.discovered_assets for use by sync_findings_and_assets.

        Args:
            plan_id: RegScale security plan ID

        Yields:
            IntegrationFinding objects for each security event
        """
        logger.info(f"Fetching findings from QRadar events for plan {plan_id}...")
        discovered_asset_ips: Dict[str, IntegrationAsset] = {}

        try:
            events = self._fetch_qradar_events()
            if not events:
                logger.warning(f"No QRadar events found for plan {plan_id}")
                return

            finding_count = 0
            for event in events:
                self._log_event_details(event)
                self._discover_assets_from_event(event, discovered_asset_ips)
                finding = self._create_finding_from_event(event)
                logger.debug(f"  -> Created finding: {finding.title}")
                yield finding
                finding_count += 1

            self._store_discovered_assets(discovered_asset_ips)
            logger.info(
                f"Fetched {finding_count} findings and discovered {len(discovered_asset_ips)} unique assets from QRadar"
            )

        except Exception as e:
            logger.error(f"Error fetching findings from QRadar: {str(e)}")
            raise

    def _log_event_details(self, event: QRadarEvent) -> None:
        """Log event details for debugging."""
        logger.debug(
            f"Processing event: {event.event_name} | "
            f"Source: {event.source_ip or 'N/A'} | "
            f"Dest: {event.dest_ip or 'N/A'} | "
            f"Severity: {event.get_severity_value()}/10 | "
            f"Category: {event.category}"
        )

    def _discover_assets_from_event(
        self, event: QRadarEvent, discovered_asset_ips: Dict[str, IntegrationAsset]
    ) -> None:
        """Discover and validate assets from a QRadar event."""
        self._discover_source_asset(event, discovered_asset_ips)
        self._discover_dest_asset(event, discovered_asset_ips)

    def _discover_source_asset(self, event: QRadarEvent, discovered_asset_ips: Dict[str, IntegrationAsset]) -> None:
        """Discover source asset from event if valid."""
        if event.is_valid_source_asset() and event.source_ip:
            source_ip = event.source_ip
            if source_ip not in discovered_asset_ips:
                asset = self._create_asset_from_event(event, source_ip)
                if self._is_valid_asset(asset):
                    discovered_asset_ips[source_ip] = asset
                    logger.debug(f"  -> Discovered source asset: {source_ip} (name: {asset.name})")
                else:
                    logger.debug(f"  -> Skipping invalid source asset: {source_ip} (name: {asset.name})")

    def _discover_dest_asset(self, event: QRadarEvent, discovered_asset_ips: Dict[str, IntegrationAsset]) -> None:
        """Discover destination asset from event if valid."""
        if event.is_valid_dest_asset() and event.dest_ip:
            dest_ip = event.dest_ip
            if dest_ip not in discovered_asset_ips:
                asset = self._create_asset_from_event(event, dest_ip)
                if self._is_valid_asset(asset):
                    discovered_asset_ips[dest_ip] = asset
                    logger.debug(f"  -> Discovered destination asset: {dest_ip} (name: {asset.name})")
                else:
                    logger.debug(f"  -> Skipping invalid destination asset: {dest_ip} (name: {asset.name})")

    def _is_valid_asset(self, asset: IntegrationAsset) -> bool:
        """Check if an asset has a valid name."""
        return bool(asset.name and asset.name not in ["Unknown", ""])

    def _store_discovered_assets(self, discovered_asset_ips: Dict[str, IntegrationAsset]) -> None:
        """Store discovered assets for use by sync_findings_and_assets."""
        if hasattr(self, "discovered_assets"):
            self.discovered_assets.extend(discovered_asset_ips.values())

    def get_discovered_assets(self) -> Iterator[IntegrationAsset]:
        """
        Yield discovered assets that were found during finding processing.

        This is a helper method used by sync_findings_and_assets to iterate
        over assets discovered while processing findings.

        Yields:
            IntegrationAsset objects for each discovered asset
        """
        yield from self.discovered_assets

    def sync_findings_and_assets(self, **kwargs) -> tuple[int, int]:
        """
        Sync both findings and discovered assets from QRadar.

        This method first discovers assets from QRadar events, creates them in RegScale,
        then processes the findings and links them to the created assets.

        Also collects evidence from QRadar events and uploads as JSONL.GZ files
        to RegScale as SSP attachments or Evidence records.

        This follows the AWS Security Hub pattern where assets are automatically
        discovered and synced as part of the findings sync process.

        Args:
            **kwargs: Additional keyword arguments passed to underlying methods
                - create_evidence: Create evidence files (default: True)
                - evidence_as_attachment: Upload as SSP attachment vs Evidence record (default: True)
                - evidence_control_ids: List of control IDs to link evidence to (default: None)

        Returns:
            tuple[int, int]: Tuple of (findings_processed, assets_processed)
        """
        from regscale.core.app.utils.app_utils import create_progress_object

        logger.info("Starting QRadar findings and assets sync...")

        # Create progress bar context for the entire operation
        with create_progress_object() as progress:
            # Store progress object for use by nested methods
            self.finding_progress = progress

            # First, fetch findings to discover assets (but don't sync findings yet)
            logger.info("Discovering assets from QRadar events...")

            # Reset discovered assets for this run
            self.discovered_assets.clear()
            self.processed_asset_identifiers.clear()

            # Fetch findings to discover assets - store them to avoid re-fetching
            findings_list = list(self.fetch_findings(self.plan_id, **kwargs))

            # Sync the discovered assets first
            if self.discovered_assets:
                logger.info(f"Creating {len(self.discovered_assets)} assets discovered from findings...")
                logger.debug(f"Assets to create: {[asset.identifier for asset in self.discovered_assets]}")
                self.num_assets_to_process = len(self.discovered_assets)
                assets_processed = self.update_regscale_assets(self.get_discovered_assets())
                logger.info(f"Successfully created {assets_processed} assets in RegScale")
            else:
                logger.info("No assets discovered from findings")
                assets_processed = 0

            # Now process the findings we already fetched (avoid double-fetching)
            logger.info(f"Now syncing {len(findings_list)} findings with created assets...")

            findings_processed = self.update_regscale_findings(iter(findings_list))
            logger.info(f"Successfully processed {findings_processed} findings in RegScale")

            # Collect and upload evidence files
            create_evidence = kwargs.get("create_evidence", True)
            if create_evidence and self._qradar_client is not None:
                logger.info("Collecting QRadar event evidence...")
                evidence_uploaded = self._collect_and_upload_evidence(
                    evidence_as_attachment=kwargs.get("evidence_as_attachment", True),
                    control_ids=kwargs.get("evidence_control_ids"),
                )
                if evidence_uploaded:
                    logger.info("Successfully uploaded QRadar evidence files")
                else:
                    logger.warning("No evidence files were uploaded")

            # Log completion summary
            logger.info(
                f"QRadar sync completed successfully: {findings_processed} findings processed, {assets_processed} assets created"
            )

        return findings_processed, assets_processed

    def _create_finding_from_event(self, event: QRadarEvent) -> IntegrationFinding:
        """
        Create an IntegrationFinding from a QRadar event.

        Args:
            event: QRadarEvent object

        Returns:
            IntegrationFinding object
        """
        # Extract basic event fields
        event_name = event.event_name or "Unknown Event"
        log_source = event.log_source or "Unknown"
        source_ip = event.source_ip or ""
        dest_ip = event.dest_ip or ""
        username = event.username or ""
        category = event.category or "Unknown"
        event_count = str(event.event_count)

        # Process event metadata
        event_time_str = self._convert_event_time(event)
        raw_magnitude = event.get_severity_value()
        severity = self._map_severity_from_magnitude(raw_magnitude, event_name)
        priority = self._map_priority_from_magnitude(raw_magnitude)

        # Build finding components
        control_labels = self._map_category_to_controls(category)
        description = self._build_event_description(event)
        evidence = self._build_event_evidence(event)
        external_id = self._build_external_id(event_name, source_ip, dest_ip, username, category, event.account_id)
        plugin_id = f"qradar-{event_name.lower().replace(' ', '-')}"

        # Determine asset identifier and title
        asset_identifier, title_source = self._determine_asset_and_title(event, source_ip, dest_ip)

        # Build extra data dictionary
        extra_data = self._build_extra_data(
            event, event_name, log_source, event_count, source_ip, dest_ip, username, category, raw_magnitude
        )

        # Create finding
        finding = IntegrationFinding(
            title=f"{event_name} from {title_source}",
            asset_identifier=asset_identifier,
            ip_address=source_ip or None,
            dns=username if username and "@" in username else None,
            severity=severity,
            status=IssueStatus.Open,
            priority=priority,
            category=category,
            plugin_name="QRadar SIEM",
            plugin_id=plugin_id,
            description=description,
            control_labels=control_labels,
            source_report=f"QRadar - {log_source}",
            identification="Security Event",
            date_created=event_time_str,
            first_seen=event_time_str,
            last_seen=event_time_str,
            issue_type="Risk",
            external_id=external_id,
            extra_data=extra_data,
            observations=f"Event Count: {event_count}",
            evidence=evidence,
        )

        self._log_finding_creation(finding)
        return finding

    def _convert_event_time(self, event: QRadarEvent) -> str:
        """Convert QRadar event time to ISO format string."""
        from datetime import datetime, timezone

        if event.event_time:
            event_datetime = datetime.fromtimestamp(event.event_time / 1000, tz=timezone.utc)
            return event_datetime.isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _map_severity_from_magnitude(self, raw_magnitude: int, event_name: str) -> IssueSeverity:
        """Map QRadar magnitude (0-10) to IssueSeverity enum."""
        if raw_magnitude >= 9:
            severity = IssueSeverity.Critical
        elif raw_magnitude >= 7:
            severity = IssueSeverity.High
        elif raw_magnitude >= 4:
            severity = IssueSeverity.Moderate
        elif raw_magnitude >= 1:
            severity = IssueSeverity.Low
        else:
            severity = IssueSeverity.NotAssigned

        logger.debug(
            f"Severity mapping for {event_name}: QRadar magnitude={raw_magnitude} → IssueSeverity.{severity.name}"
        )
        return severity

    def _map_priority_from_magnitude(self, raw_magnitude: int) -> str:
        """Map QRadar magnitude to priority string."""
        if raw_magnitude >= 9:
            return "Critical"
        elif raw_magnitude >= 7:
            return "High"
        elif raw_magnitude >= 4:
            return "Medium"
        elif raw_magnitude >= 1:
            return "Low"
        return "Info"

    def _build_external_id(
        self, event_name: str, source_ip: str, dest_ip: str, username: str, category: str, account_id: Optional[str]
    ) -> str:
        """Build stable external ID for finding deduplication."""
        stable_id_components = [
            event_name or "unknown",
            source_ip or "no-source",
            dest_ip or "no-dest",
            username or "no-user",
            category or "unknown-category",
            account_id or "no-account",
        ]
        stable_id_base = ":".join(stable_id_components)
        return f"qradar-{abs(hash(stable_id_base))}"

    def _determine_asset_and_title(self, event: QRadarEvent, source_ip: str, dest_ip: str) -> tuple[str, str]:
        """Determine asset identifier and title source based on event type."""
        if event.account_id and event.account_id != "":
            asset_identifier = event.account_id
            title_source = f"AWS Account {event.account_name or event.account_id}"
        else:
            asset_identifier = source_ip or dest_ip or ""
            title_source = source_ip or "Unknown Source"
        return asset_identifier, title_source

    def _build_extra_data(
        self,
        event: QRadarEvent,
        event_name: str,
        log_source: str,
        event_count: str,
        source_ip: str,
        dest_ip: str,
        username: str,
        category: str,
        raw_magnitude: int,
    ) -> Dict[str, Any]:
        """Build extra data dictionary for finding."""
        return {
            "event_name": event_name,
            "log_source": log_source,
            "event_count": event_count,
            "source_ip": source_ip,
            "source_port": str(event.source_port) if event.source_port else "",
            "dest_ip": dest_ip,
            "dest_port": str(event.dest_port) if event.dest_port else "",
            "username": username,
            "low_level_category": category,
            "magnitude": raw_magnitude,
            "account_id": event.account_id or "",
            "account_name": event.account_name or "",
            "aws_access_key_id": event.aws_access_key_id or "",
        }

    def _log_finding_creation(self, finding: IntegrationFinding) -> None:
        """Log finding creation details."""
        logger.debug(
            f"Created IntegrationFinding: title='{finding.title}', "
            f"severity={finding.severity} (type={type(finding.severity).__name__}), "
            f"plugin_name='{finding.plugin_name}', plugin_id='{finding.plugin_id}'"
        )

    def _fetch_qradar_events(self) -> List[QRadarEvent]:
        """
        Fetch events from QRadar within the configured time window.

        Returns:
            List of validated QRadarEvent objects

        Raises:
            Exception: If QRadar API call fails
        """
        # Format times for QRadar API
        start_time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = self.end_time.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Fetching QRadar events from {start_time_str} to {end_time_str}")

        try:
            # Build filters dict with severity threshold and account_id for AQL WHERE clause
            filters = {}
            if self.severity_threshold > 0:
                # Add severity filter to AQL query - filter at API level for efficiency
                filters["severity"] = f">= {self.severity_threshold}"
                logger.info(f"Applying severity filter in QRadar query: severity >= {self.severity_threshold}")

            if self.account_id_filter:
                # Add AWS account ID filter for CloudTrail events
                filters["accountid"] = f"= '{self.account_id_filter}'"
                logger.info(f"Applying AWS account ID filter in QRadar query: accountid = '{self.account_id_filter}'")

            # Use the QRadar API client to fetch events with filters
            raw_events = self.qradar_client.get_events(
                start_time=start_time_str,
                end_time=end_time_str,
                filters=filters,
                limit=self.max_events,
            )

            logger.info(f"Retrieved {len(raw_events)} raw events from QRadar (after server-side severity filtering)")

            # Validate and parse events with Pydantic
            validated_events = []
            for idx, raw_event in enumerate(raw_events):
                try:
                    # Log severity fields from first few raw events for debugging
                    if idx < 3:
                        magnitude_val = raw_event.get("magnitude")
                        severity_val = raw_event.get("severity")
                        logger.debug(
                            f"Raw event {idx}: magnitude={magnitude_val} (type={type(magnitude_val).__name__}), "
                            f"severity={severity_val} (type={type(severity_val).__name__})"
                        )

                    event = QRadarEvent(**raw_event)

                    # Log validated event severity for first few events
                    if idx < 3:
                        logger.debug(
                            f"Validated event {idx}: magnitude={event.magnitude}, severity={event.severity}, "
                            f"get_severity_value()={event.get_severity_value()}"
                        )

                    validated_events.append(event)
                except Exception as e:
                    if idx == 0:
                        # Log first event structure for debugging
                        logger.debug(f"First event structure: {raw_event}")
                    logger.warning(f"Skipping invalid event at index {idx}: {str(e)}")
                    continue

            logger.info(f"Successfully validated {len(validated_events)} events")
            return validated_events

        except Exception as e:
            logger.error(f"Failed to fetch events from QRadar: {str(e)}")
            raise

    def _map_category_to_controls(self, category: str) -> List[str]:
        """
        Map QRadar event category to NIST 800-53 controls.

        Args:
            category: QRadar low-level category

        Returns:
            List of control IDs
        """
        # Category to control mapping
        category_mapping = {
            "authentication": ["AC-2", "AC-7", "IA-2", "IA-4"],
            "authorization": ["AC-3", "AC-6"],
            "access": ["AC-2", "AC-3", "AC-17"],
            "logon": ["AC-2", "AC-7", "IA-2"],
            "logoff": ["AC-2", "AC-12"],
            "account": ["AC-2", "IA-4"],
            "audit": ["AU-2", "AU-3", "AU-6", "AU-12"],
            "logging": ["AU-2", "AU-3", "AU-12"],
            "firewall": ["SC-7", "AC-4"],
            "intrusion": ["SI-4", "SI-7"],
            "malware": ["SI-3", "SI-7"],
            "vulnerability": ["RA-5", "SI-2"],
            "configuration": ["CM-2", "CM-6"],
            "system": ["SI-2", "SI-4"],
            "network": ["SC-7", "AC-17"],
            "encryption": ["SC-8", "SC-13"],
            "data": ["SC-28", "MP-4"],
            "incident": ["IR-4", "IR-6"],
        }

        # Normalize category to lowercase for matching
        category_lower = category.lower()

        # Find matching controls
        controls = []
        for keyword, control_list in category_mapping.items():
            if keyword in category_lower:
                controls.extend(control_list)

        # Remove duplicates and sort
        controls = sorted(set(controls))

        # Return default controls if no match found
        if not controls:
            controls = ["AU-6"]  # Default to audit and monitoring

        return controls

    def _build_event_description(self, event: QRadarEvent) -> str:
        """
        Build a detailed description from QRadar event data.

        Args:
            event: QRadarEvent object

        Returns:
            Formatted description string
        """
        description_parts = []

        # Event overview
        description_parts.append(f"**Event:** {event.event_name}")

        # Source and destination
        if event.source_ip:
            source_str = (
                f"{event.source_ip}:{event.source_port}"
                if event.source_port and event.source_port != 0
                else event.source_ip
            )
            description_parts.append(f"**Source:** {source_str}")

        if event.dest_ip:
            dest_str = (
                f"{event.dest_ip}:{event.dest_port}" if event.dest_port and event.dest_port != 0 else event.dest_ip
            )
            description_parts.append(f"**Destination:** {dest_str}")

        # User information
        if event.username:
            description_parts.append(f"**User:** {event.username}")

        # Event metadata
        description_parts.append(f"**Log Source:** {event.log_source}")
        description_parts.append(f"**Category:** {event.category}")
        description_parts.append(f"**Event Count:** {event.event_count}")
        description_parts.append(f"**Severity/Magnitude:** {event.get_severity_value()}")

        # Time information - convert from milliseconds to human-readable format
        if event.event_time:
            from datetime import datetime, timezone

            event_datetime = datetime.fromtimestamp(event.event_time / 1000, tz=timezone.utc)
            time_str = event_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            time_str = "Unknown"
        description_parts.append(f"**Time:** {time_str}")

        # Join all parts
        return "<br>".join(description_parts)

    def _build_event_evidence(self, event: QRadarEvent) -> str:
        """
        Build comprehensive evidence documentation from QRadar event data.

        This method extracts all relevant evidence from the QRadar event including
        network information, user context, event metadata, and any raw payload data.

        Args:
            event: QRadarEvent object

        Returns:
            Formatted evidence string with all available event data
        """
        evidence_parts: List[str] = []

        # Build evidence sections
        self._add_network_evidence(event, evidence_parts)
        self._add_identity_evidence(event, evidence_parts)
        self._add_event_context_evidence(event, evidence_parts)
        self._add_extra_fields_evidence(event, evidence_parts)
        self._add_evidence_attribution(evidence_parts)

        return "\n".join(evidence_parts)

    def _add_network_evidence(self, event: QRadarEvent, evidence_parts: List[str]) -> None:
        """Add network evidence section to evidence parts."""
        evidence_parts.append("## Network Evidence")
        if event.source_ip:
            source_info = self._format_address_with_port(event.source_ip, event.source_port)
            evidence_parts.append(f"- **Source Address:** {source_info}")
        if event.dest_ip:
            dest_info = self._format_address_with_port(event.dest_ip, event.dest_port)
            evidence_parts.append(f"- **Destination Address:** {dest_info}")

    def _format_address_with_port(self, ip_address: str, port: Optional[int]) -> str:
        """Format IP address with optional port."""
        if port and port != 0:
            return f"{ip_address}:{port}"
        return ip_address

    def _add_identity_evidence(self, event: QRadarEvent, evidence_parts: List[str]) -> None:
        """Add identity evidence section if username exists."""
        if event.username:
            evidence_parts.append("\n## Identity Evidence")
            evidence_parts.append(f"- **Username:** {event.username}")

    def _add_event_context_evidence(self, event: QRadarEvent, evidence_parts: List[str]) -> None:
        """Add event context evidence section."""
        evidence_parts.append("\n## Event Context")
        evidence_parts.append(f"- **Event Name:** {event.event_name}")
        evidence_parts.append(f"- **Log Source:** {event.log_source}")
        evidence_parts.append(f"- **Category:** {event.category}")
        evidence_parts.append(f"- **Severity/Magnitude:** {event.get_severity_value()}/10")
        evidence_parts.append(f"- **Event Count:** {event.event_count}")
        if event.event_time:
            evidence_parts.append(f"- **Event Time:** {event.event_time}")

    def _add_extra_fields_evidence(self, event: QRadarEvent, evidence_parts: List[str]) -> None:
        """Add evidence from extra Pydantic fields."""
        if not hasattr(event, "__pydantic_extra__") or not event.__pydantic_extra__:
            return

        extra_fields = event.__pydantic_extra__
        payload_fields = ["payload", "utf8_payload", "message", "event_data"]

        # Add payload data
        self._add_payload_evidence(extra_fields, payload_fields, evidence_parts)

        # Add other metadata
        self._add_other_metadata_evidence(extra_fields, payload_fields, evidence_parts)

    def _add_payload_evidence(
        self, extra_fields: Dict[str, Any], payload_fields: List[str], evidence_parts: List[str]
    ) -> None:
        """Add payload data evidence section."""
        has_payload = False
        for field_name in payload_fields:
            if field_name in extra_fields and extra_fields[field_name]:
                if not has_payload:
                    evidence_parts.append("\n## Raw Event Data")
                    has_payload = True
                payload_value = self._truncate_payload(extra_fields[field_name])
                evidence_parts.append(f"- **{field_name.replace('_', ' ').title()}:**\n```\n{payload_value}\n```")

    def _truncate_payload(self, payload_value: Any) -> str:
        """Truncate payload if too large."""
        if isinstance(payload_value, str) and len(payload_value) > 5000:
            return payload_value[:5000] + "\n... (truncated)"
        return str(payload_value)

    def _add_other_metadata_evidence(
        self, extra_fields: Dict[str, Any], payload_fields: List[str], evidence_parts: List[str]
    ) -> None:
        """Add other metadata evidence section."""
        other_fields = {k: v for k, v in extra_fields.items() if k not in payload_fields and v is not None}
        if other_fields:
            evidence_parts.append("\n## Additional Event Metadata")
            for key, value in sorted(other_fields.items()):
                if not key.startswith("_"):
                    evidence_parts.append(f"- **{key.replace('_', ' ').title()}:** {value}")

    def _add_evidence_attribution(self, evidence_parts: List[str]) -> None:
        """Add QRadar attribution footer."""
        evidence_parts.append("\n---")
        evidence_parts.append("*Evidence collected from QRadar SIEM*")

    def _collect_and_upload_evidence(
        self, evidence_as_attachment: bool = True, control_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Collect QRadar events and upload as evidence files.

        Args:
            evidence_as_attachment: If True, upload as SSP attachment; if False, create Evidence record
            control_ids: Optional list of control IDs to link evidence to

        Returns:
            bool: True if evidence was successfully uploaded
        """
        try:
            # Fetch events again for evidence (they were already fetched for findings)
            # In a production scenario, we'd cache these events to avoid re-fetching
            events = self._fetch_qradar_events()

            if not events:
                logger.info("No events to collect for evidence")
                return False

            # Import evidence collector and API
            from regscale.integrations.commercial.qradar.qradar_evidence import QRadarEvidenceCollector
            from regscale.core.app.api import Api

            # Extract control IDs from the events if not provided
            if control_ids is None:
                control_ids = self._extract_control_ids_from_events(events)

            # Create API instance for evidence upload
            api = Api()

            # Create evidence collector
            collector = QRadarEvidenceCollector(
                plan_id=self.plan_id,
                api=api,
                events=events,
                control_ids=control_ids,
                create_ssp_attachment=evidence_as_attachment,
            )

            # Collect and upload evidence
            success = collector.collect_and_upload_evidence()

            return success

        except Exception as e:
            logger.error(f"Failed to collect and upload evidence: {e}")
            logger.debug(f"Failed to collect and upload evidence: {e}", exc_info=True)
            return False

    def _extract_control_ids_from_events(self, events: List[QRadarEvent]) -> List[int]:
        """
        Extract unique control IDs from events based on their categories.

        Args:
            events: List of QRadarEvent objects

        Returns:
            List of control IDs
        """
        # This would map event categories to actual control IDs from RegScale
        # For now, return empty list - this can be enhanced later
        # to fetch control IDs from RegScale based on control_labels
        return []
