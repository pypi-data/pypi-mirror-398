"""Module for Wiz vulnerability scanning integration."""

import datetime
import json
import logging
import os
import re
from collections.abc import Iterator
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

from regscale.core.app.utils.app_utils import check_file_path, error_and_exit, get_current_datetime
from regscale.core.utils import get_base_protocol_from_port
from regscale.core.utils.date import format_to_regscale_iso
from regscale.integrations.commercial.wizv2.core.client import run_async_queries
from regscale.integrations.commercial.wizv2.core.file_operations import FileOperations
from regscale.integrations.commercial.wizv2.core.constants import (
    END_OF_LIFE_FILE_PATH,
    EXTERNAL_ATTACK_SURFACE_FILE_PATH,
    INVENTORY_FILE_PATH,
    INVENTORY_QUERY,
    NETWORK_EXPOSURE_FILE_PATH,
    SECRET_FINDINGS_FILE_PATH,
    WizVulnerabilityType,
    get_wiz_vulnerability_queries,
)
from regscale.integrations.commercial.wizv2.parsers import (
    collect_components_to_create,
    fetch_wiz_data,
    get_disk_storage,
    get_latest_version,
    get_network_info,
    get_product_ids,
    get_software_name_from_cpe,
    handle_container_image_version,
    handle_provider,
    handle_software_version,
    pull_resource_info_from_props,
)
from regscale.integrations.commercial.wizv2.utils import (
    create_asset_type,
    get_notes_from_wiz_props,
    handle_management_type,
    map_category,
)
from regscale.integrations.commercial.wizv2.variables import WizVariables
from regscale.integrations.variables import ScannerVariables
from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate
from regscale.integrations.scanner_integration import (
    IntegrationAsset,
    IntegrationFinding,
    ScannerIntegration,
)
from regscale.models import IssueStatus, regscale_models
from regscale.models.regscale_models.compliance_settings import ComplianceSettings
from regscale.models.regscale_models.regscale_model import RegScaleModel

logger = logging.getLogger("regscale")


class WizVulnerabilityIntegration(ScannerIntegration):
    """Integration class for Wiz vulnerability scanning."""

    title = "Wiz"
    # Server-side batch deduplication requires a standard RegScale Asset field name
    # The Wiz ID is stored in otherTrackingNumber for deduplication purposes
    asset_identifier_field = "otherTrackingNumber"
    issue_identifier_field = "wizId"
    finding_severity_map = {
        "Critical": regscale_models.IssueSeverity.Critical,
        "High": regscale_models.IssueSeverity.High,
        "Medium": regscale_models.IssueSeverity.Moderate,
        "Low": regscale_models.IssueSeverity.Low,
        "Informational": regscale_models.IssueSeverity.NotAssigned,
        "Info": regscale_models.IssueSeverity.NotAssigned,
        "None": regscale_models.IssueSeverity.NotAssigned,
    }
    asset_lookup = "vulnerableAsset"
    wiz_token = None
    _compliance_settings = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Suppress generic asset not found errors but use enhanced diagnostics instead
        self.suppress_asset_not_found_errors = True
        # Track unique missing asset types for summary reporting
        self._missing_asset_types = set()

    @staticmethod
    def get_variables() -> Dict[str, Any]:
        """
        Returns default variables for first and filterBy for Wiz GraphQL queries.

        :return: Default variables for Wiz queries
        :rtype: Dict[str, Any]
        """
        return {
            "first": 100,
            "filterBy": {},
        }

    def get_finding_identifier(self, finding) -> str:
        """
        Gets the finding identifier for Wiz findings.
        For Wiz integrations, prioritize external_id since plugin_id can be non-unique.

        :param finding: The finding
        :return: The finding identifier
        :rtype: str
        """
        # We could have a string truncation error platform side on IntegrationFindingId nvarchar(450)
        prefix = f"{self.plan_id}:"

        # For Wiz, prioritize external_id since plugin_id can be non-unique
        if finding.external_id:
            prefix += self.hash_string(finding.external_id).__str__()
        else:
            prefix += (
                finding.cve or finding.plugin_id or finding.rule_id or self.hash_string(finding.external_id).__str__()
            )

        if ScannerVariables.issueCreation.lower() == "perasset":
            res = f"{prefix}:{finding.asset_identifier}"
            return res[:450]
        return prefix[:450]

    def authenticate(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> None:
        """
        Authenticates to Wiz using the client ID and client secret

        :param Optional[str] client_id: Wiz client ID
        :param Optional[str] client_secret: WiZ client secret
        :rtype: None
        """
        client_id = client_id or WizVariables.wizClientId
        client_secret = client_secret or WizVariables.wizClientSecret
        logger.info("Authenticating to Wiz...")
        self.wiz_token = wiz_authenticate(client_id, client_secret)

    def get_query_types(self, project_id: str, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get the query types for vulnerability scanning.

        :param str project_id: The project ID to get queries for
        :param Optional[Dict[str, Any]] filter_by: Optional filter criteria (used by subclasses)
        :return: List of query types
        :rtype: List[Dict[str, Any]]
        """
        # Base class ignores filter_by, subclasses can override to use it
        return get_wiz_vulnerability_queries(project_id=project_id, filter_by=filter_by)

    def fetch_findings(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetches Wiz findings using async GraphQL queries for improved performance

        This method automatically uses async concurrent queries by default for better performance,
        with fallback to synchronous queries if async fails.

        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        # Check if async processing should be disabled (for debugging or compatibility)
        use_async = kwargs.get("use_async", True)  # Default to async

        if use_async:
            try:
                # Use async concurrent queries for better performance
                yield from self.fetch_findings_async(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Async query failed, falling back to sync: {e!s}")
                # Fallback to synchronous method
                yield from self.fetch_findings_sync(**kwargs)
        else:
            # Use synchronous method if explicitly requested
            yield from self.fetch_findings_sync(**kwargs)

    def _validate_project_id(self, project_id: Optional[str]) -> str:
        """
        Validate and format the Wiz project ID.

        :param Optional[str] project_id: Project ID to validate
        :return: Validated project ID
        :rtype: str
        :raises ValueError: If project ID is invalid or missing
        """
        if not project_id:
            error_and_exit("Wiz project ID is required")

        # Clean and validate project ID format
        project_id = project_id.strip()
        if len(project_id) != 36:
            error_and_exit(
                f"Invalid Wiz project ID format. Expected 36 characters (UUID), "
                f"got {len(project_id)} characters: '{project_id}'"
            )

        # UUID format validation
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(uuid_pattern, project_id, re.IGNORECASE):
            error_and_exit(f"Invalid Wiz project ID format. Must be a valid UUID: '{project_id}'")

        return project_id

    def _setup_authentication_headers(self) -> Dict[str, str]:
        """
        Setup authentication headers for API requests.

        :return: Headers dictionary with authentication
        :rtype: Dict[str, str]
        """
        if not self.wiz_token:
            self.authenticate()

        # Debug authentication
        logger.debug(f"Wiz token exists: {bool(self.wiz_token)}")
        logger.debug(f"Wiz token length: {len(self.wiz_token) if self.wiz_token else 0}")
        if self.wiz_token:
            logger.debug(f"Wiz token starts with: {self.wiz_token[:20]}...")

        headers = {"Authorization": f"Bearer {self.wiz_token}", "Content-Type": "application/json"}
        logger.debug(f"Headers for async request: {headers}")
        return headers

    def _execute_concurrent_queries(
        self, query_configs: List[Dict[str, Any]], headers: Dict[str, str]
    ) -> List[Tuple[str, List[Dict[str, Any]], Optional[Exception]]]:
        """
        Execute GraphQL queries concurrently or load cached data.

        :param List[Dict[str, Any]] query_configs: Query configurations
        :param Dict[str, str] headers: Request headers
        :return: Query results
        :rtype: List[Tuple[str, List[Dict[str, Any]], Optional[Exception]]]
        """
        should_fetch_fresh = self._should_fetch_fresh_data(query_configs)

        if should_fetch_fresh:
            logger.info(f"Starting {len(query_configs)} concurrent queries to Wiz API...")
            return run_async_queries(
                endpoint=WizVariables.wizUrl,
                headers=headers,
                query_configs=query_configs,
                progress_tracker=self.finding_progress,
                max_concurrent=5,
            )
        return self._load_cached_data_with_progress(query_configs)

    def _process_query_results(
        self,
        results: List[Tuple[str, List[Dict[str, Any]], Optional[Exception]]],
        query_configs: List[Dict[str, Any]],
        project_id: str,
        should_fetch_fresh: bool,
    ) -> Iterator[IntegrationFinding]:
        """
        Process query results and yield findings.

        :param results: Query results from concurrent execution
        :param query_configs: Original query configurations
        :param project_id: Project ID for filtering
        :param should_fetch_fresh: Whether fresh data was fetched
        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        parse_task = self._init_progress_task(len(results))

        for query_type_str, nodes, error in results:
            if error:
                logger.error(f"Error fetching {query_type_str}: {error}")
                self._advance_progress(parse_task)
                continue

            vulnerability_type, config = self._find_vulnerability_config(query_type_str, query_configs)
            if not vulnerability_type or not config:
                logger.warning(f"Could not find vulnerability type for {query_type_str}")
                self._advance_progress(parse_task)
                continue

            if should_fetch_fresh and nodes:
                self._save_data_to_cache(nodes, config.get("file_path"))

            nodes = self._apply_project_filtering(nodes, vulnerability_type, project_id, query_type_str)

            logger.info(f"Processing {len(nodes)} {query_type_str} findings...")
            yield from self.parse_findings(nodes, vulnerability_type)
            self._advance_progress(parse_task)

        self._finalize_progress(parse_task)

    def _init_progress_task(self, total_results: int):
        """
        Initialize progress tracking task.

        :param int total_results: Total number of results to process
        :return: Task ID or None
        """
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            return self.finding_progress.add_task("[magenta]Processing fetched findings...", total=total_results)
        return None

    def _advance_progress(self, parse_task) -> None:
        """
        Advance progress bar by one step.

        :param parse_task: Progress task ID
        :rtype: None
        """
        if parse_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "advance"):
            self.finding_progress.advance(parse_task, 1)

    def _finalize_progress(self, parse_task) -> None:
        """
        Finalize progress tracking with completion message.

        :param parse_task: Progress task ID
        :rtype: None
        """
        if parse_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                parse_task, description=f"[green]✓ Processed all findings ({self.num_findings_to_process} total)"
            )

    def _find_vulnerability_config(
        self, query_type_str: str, query_configs: List[Dict[str, Any]]
    ) -> Tuple[Optional[WizVulnerabilityType], Optional[Dict[str, Any]]]:
        """
        Find vulnerability type and config for a query type string.

        :param str query_type_str: Query type string to find
        :param List[Dict[str, Any]] query_configs: List of query configurations
        :return: Tuple of vulnerability type and config, or (None, None) if not found
        :rtype: Tuple[Optional[WizVulnerabilityType], Optional[Dict[str, Any]]]
        """
        for query_config in query_configs:
            if query_config["type"].value == query_type_str:
                return query_config["type"], query_config
        return None, None

    def _apply_project_filtering(
        self,
        nodes: List[Dict[str, Any]],
        vulnerability_type: WizVulnerabilityType,
        project_id: str,
        query_type_str: str,
    ) -> List[Dict[str, Any]]:
        """
        Apply project filtering for vulnerability types that need it.

        :param List[Dict[str, Any]] nodes: Nodes to filter
        :param WizVulnerabilityType vulnerability_type: Vulnerability type
        :param str project_id: Project ID to filter by
        :param str query_type_str: Query type string for logging
        :return: Filtered nodes
        :rtype: List[Dict[str, Any]]
        """
        filter_required_types = {
            WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING,
            WizVulnerabilityType.NETWORK_EXPOSURE_FINDING,
            WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE,
        }

        if vulnerability_type in filter_required_types:
            original_count = len(nodes)
            nodes = self._filter_findings_by_project(nodes, project_id)
            if len(nodes) != original_count:
                logger.info(f"Filtered {query_type_str}: {len(nodes)}/{original_count} match project")

        return nodes

    def _add_progress_task(self, description: str, total: int):
        """
        Add a progress task if finding_progress is available.

        :param str description: Task description
        :param int total: Total number of items
        :return: Task ID or None
        :rtype: Optional[Any]
        """
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            return self.finding_progress.add_task(description, total=total)
        return None

    def _update_progress_task(self, task_id, description: str, completed: int, total: int) -> None:
        """
        Update a progress task if available.

        :param task_id: Task ID to update
        :param str description: Updated description
        :param int completed: Number of completed items
        :param int total: Total number of items
        :rtype: None
        """
        if task_id is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(task_id, description=description, completed=completed, total=total)

    def fetch_findings_async(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetches Wiz findings using async GraphQL queries for improved performance

        This method runs multiple GraphQL queries concurrently, significantly reducing
        the total time needed to fetch all finding types from Wiz.

        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        try:
            # Step 1: Validate project ID
            project_id = self._validate_project_id(kwargs.get("wiz_project_id"))

            # Step 2: Initialize progress tracking
            logger.info("Fetching Wiz findings using async concurrent queries...")
            self.num_findings_to_process = 0
            # Pass filter_by_override if provided
            filter_by = kwargs.get("filter_by_override")
            query_configs = self.get_query_types(project_id=project_id, filter_by=filter_by)

            # Create progress task
            main_task = self._add_progress_task("[cyan]Running concurrent GraphQL queries...", len(query_configs))

            # Step 3: Setup authentication
            headers = self._setup_authentication_headers()

            # Step 4: Execute queries
            results = self._execute_concurrent_queries(query_configs, headers)
            should_fetch_fresh = self._should_fetch_fresh_data(query_configs)

            # Step 5: Update progress after queries complete
            self._update_progress_task(
                main_task, "[green]✓ Completed all concurrent queries", len(query_configs), len(query_configs)
            )

            # Step 6: Process results
            yield from self._process_query_results(results, query_configs, project_id, should_fetch_fresh)

            # Step 7: Complete main task
            self._update_progress_task(
                main_task, "[green]✓ Completed processing all Wiz findings", len(query_configs), len(query_configs)
            )

        except Exception as e:
            logger.error(f"Error in async findings fetch: {e!s}", exc_info=True)
            # Update progress with error if task exists
            if "main_task" in locals():
                self._update_progress_task(
                    main_task,
                    f"[red]✗ Error in concurrent queries: {str(e)[:50]}...",
                    len(query_configs) if "query_configs" in locals() else 0,
                    len(query_configs) if "query_configs" in locals() else 0,
                )
            # Fallback to synchronous method
            logger.info("Falling back to synchronous query method...")
            yield from self.fetch_findings_sync(**kwargs)

        # Log summary of missing asset types if any were found
        if hasattr(self, "_missing_asset_types") and self._missing_asset_types:
            logger.warning(
                "Summary: Found references to missing asset types: %s. "
                "Consider adding these to RECOMMENDED_WIZ_INVENTORY_TYPES in constants.py",
                ", ".join(sorted(self._missing_asset_types)),
            )

        logger.info(
            "Finished async fetching Wiz findings. Total findings to process: %d", self.num_findings_to_process or 0
        )

    def _should_fetch_fresh_data(self, query_configs: List[Dict[str, Any]]) -> bool:
        """
        Check if we should fetch fresh data or use cached data.

        :param List[Dict[str, Any]] query_configs: Query configurations
        :return: True if fresh data should be fetched
        :rtype: bool
        """
        import datetime
        import os

        fetch_interval = datetime.timedelta(hours=WizVariables.wizFullPullLimitHours or 8)
        current_time = datetime.datetime.now()

        # Check if any file is missing or older than the fetch interval
        for config in query_configs:
            file_path = config.get("file_path")
            if not file_path or not os.path.exists(file_path):
                return True

            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if current_time - file_mod_time >= fetch_interval:
                return True

        return False

    def _load_cached_data_with_progress(
        self, query_configs: List[Dict[str, Any]]
    ) -> List[Tuple[str, List[Dict[str, Any]], Optional[Exception]]]:
        """
        Load cached data with progress tracking.

        :param List[Dict[str, Any]] query_configs: Query configurations
        :return: Results in the same format as async queries
        :rtype: List[Tuple[str, List[Dict[str, Any]], Optional[Exception]]]
        """
        # Backwards compatibility: check if finding_progress exists and has add_task method
        cache_task = None
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            cache_task = self.finding_progress.add_task("[green]Loading cached Wiz data...", total=len(query_configs))

        def progress_callback(query_type: str, status: str):
            if status == "loaded":
                # Backwards compatibility: check if finding_progress exists and has advance method
                if (
                    cache_task is not None
                    and self.finding_progress is not None
                    and hasattr(self.finding_progress, "advance")
                ):
                    self.finding_progress.advance(cache_task, 1)

        results = FileOperations.load_cached_findings(query_configs, progress_callback)

        # Backwards compatibility: check if finding_progress exists and has update method
        if cache_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                cache_task, description=f"[green]✓ Loaded cached data for {len(query_configs)} query types"
            )

        return results

    def _save_data_to_cache(self, nodes: List[Dict[str, Any]], file_path: Optional[str]) -> None:
        """
        Save fetched data to cache file.

        :param List[Dict[str, Any]] nodes: Data to save
        :param Optional[str] file_path: File path to save to
        :rtype: None
        """
        if not file_path:
            return

        success = FileOperations.save_json_file(nodes, file_path, create_dir=True)
        if success:
            logger.debug(f"Saved {len(nodes)} nodes to cache file: {file_path}")

    def fetch_findings_sync(self, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Original synchronous method for fetching findings (renamed for fallback)
        :param List[Dict[str, Any]] kwargs: Query configurations
        :return: Results in the same format as async queries
        :rtype: Iterator[IntegrationFinding]
        """
        project_id = self._validate_project_id(kwargs.get("wiz_project_id"))
        logger.info("Fetching Wiz findings using synchronous queries...")
        self.num_findings_to_process = 0

        filter_by = kwargs.get("filter_by_override")
        query_types = self.get_query_types(project_id=project_id, filter_by=filter_by)

        main_task = self._create_main_progress_task(len(query_types))

        for i, wiz_vulnerability_type in enumerate(query_types, 1):
            yield from self._process_single_query_type(
                wiz_vulnerability_type, project_id, i, len(query_types), main_task
            )

        self._complete_main_progress_task(main_task)
        self._log_missing_asset_types_summary()

    def _create_main_progress_task(self, total_query_types: int):
        """
        Create main progress tracking task.

        :param int total_query_types: Total number of query types
        :return: Task ID or None
        """
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            return self.finding_progress.add_task(
                "[cyan]Fetching Wiz findings across all query types...", total=total_query_types
            )
        return None

    def _process_single_query_type(
        self, wiz_vulnerability_type: dict, project_id: str, step: int, total_steps: int, main_task
    ) -> Iterator[IntegrationFinding]:
        """
        Process a single query type and yield findings.

        :param dict wiz_vulnerability_type: Query type configuration
        :param str project_id: Project ID for filtering
        :param int step: Current step number
        :param int total_steps: Total number of steps
        :param main_task: Main progress task ID
        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        vulnerability_name = self._get_friendly_vulnerability_name(wiz_vulnerability_type["type"])
        self._update_main_progress_description(main_task, step, total_steps, vulnerability_name)

        query_task = self._create_query_task(vulnerability_name)
        nodes = self._fetch_query_data(wiz_vulnerability_type, vulnerability_name, query_task)
        nodes = self._apply_query_filtering(wiz_vulnerability_type, nodes, project_id, vulnerability_name)

        if nodes:
            yield from self._parse_query_results(nodes, wiz_vulnerability_type["type"], vulnerability_name)

        self._complete_query_tasks(query_task, main_task)

    def _update_main_progress_description(
        self, main_task, step: int, total_steps: int, vulnerability_name: str
    ) -> None:
        """
        Update main progress task description.

        :param main_task: Main task ID
        :param int step: Current step
        :param int total_steps: Total steps
        :param str vulnerability_name: Vulnerability name
        :rtype: None
        """
        if main_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                main_task, description=f"[cyan]Step {step}/{total_steps}: Fetching {vulnerability_name}..."
            )

    def _create_query_task(self, vulnerability_name: str):
        """
        Create query-specific progress task.

        :param str vulnerability_name: Vulnerability name
        :return: Task ID or None
        """
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            return self.finding_progress.add_task(f"[yellow]Querying Wiz API for {vulnerability_name}...", total=None)
        return None

    def _fetch_query_data(self, wiz_vulnerability_type: dict, vulnerability_name: str, query_task) -> list:
        """
        Fetch data for a single query type.

        :param dict wiz_vulnerability_type: Query type configuration
        :param str vulnerability_name: Vulnerability name
        :param query_task: Query task ID
        :return: List of nodes
        :rtype: list
        """
        variables = wiz_vulnerability_type.get("variables", self.get_variables())
        nodes = self.fetch_wiz_data_if_needed(
            query=wiz_vulnerability_type["query"],
            variables=variables,
            topic_key=wiz_vulnerability_type["topic_key"],
            file_path=wiz_vulnerability_type["file_path"],
        )

        if query_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                query_task, description=f"[green]✓ Fetched {len(nodes)} {vulnerability_name} from Wiz API"
            )

        return nodes

    def _apply_query_filtering(
        self, wiz_vulnerability_type: dict, nodes: list, project_id: str, vulnerability_name: str
    ) -> list:
        """
        Apply project filtering if needed for the query type.

        :param dict wiz_vulnerability_type: Query type configuration
        :param list nodes: Nodes to filter
        :param str project_id: Project ID
        :param str vulnerability_name: Vulnerability name
        :return: Filtered nodes
        :rtype: list
        """
        if wiz_vulnerability_type["type"] not in [
            WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING,
            WizVulnerabilityType.NETWORK_EXPOSURE_FINDING,
            WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE,
        ]:
            return nodes

        filter_task = None
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            filter_task = self.finding_progress.add_task(
                f"[blue]Filtering {vulnerability_name} by project...", total=len(nodes)
            )

        nodes = self._filter_findings_by_project_with_progress(nodes, project_id, filter_task)

        if filter_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                filter_task, description=f"[green]✓ Filtered to {len(nodes)} {vulnerability_name} for project"
            )

        return nodes

    def _parse_query_results(
        self, nodes: list, vulnerability_type, vulnerability_name: str
    ) -> Iterator[IntegrationFinding]:
        """
        Parse nodes and yield findings.

        :param list nodes: Nodes to parse
        :param vulnerability_type: Vulnerability type
        :param str vulnerability_name: Vulnerability name
        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        parse_task = None
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            parse_task = self.finding_progress.add_task(
                f"[magenta]Parsing {len(nodes)} {vulnerability_name}...", total=len(nodes)
            )

        yield from self.parse_findings_with_progress(nodes, vulnerability_type, parse_task)

        if parse_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                parse_task, description=f"[green]✓ Parsed {len(nodes)} {vulnerability_name} successfully"
            )

    def _complete_query_tasks(self, query_task, main_task) -> None:
        """
        Mark query and main tasks as progressing.

        :param query_task: Query task ID
        :param main_task: Main task ID
        :rtype: None
        """
        if query_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(query_task, completed=1, total=1)

        if main_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "advance"):
            self.finding_progress.advance(main_task, 1)

    def _complete_main_progress_task(self, main_task) -> None:
        """
        Complete main progress task with final message.

        :param main_task: Main task ID
        :rtype: None
        """
        if main_task is not None and self.finding_progress is not None and hasattr(self.finding_progress, "update"):
            self.finding_progress.update(
                main_task,
                description=f"[green]✓ Completed fetching all Wiz findings ({self.num_findings_to_process or 0} total)",
            )

    def _log_missing_asset_types_summary(self) -> None:
        """
        Log summary of missing asset types if any were found.

        :rtype: None
        """
        if hasattr(self, "_missing_asset_types") and self._missing_asset_types:
            logger.warning(
                "Summary: Found references to missing asset types: %s. "
                "Consider adding these to RECOMMENDED_WIZ_INVENTORY_TYPES in constants.py",
                ", ".join(sorted(self._missing_asset_types)),
            )

        logger.info(
            "Finished synchronous fetching Wiz findings. Total findings to process: %d",
            self.num_findings_to_process or 0,
        )

    def _get_friendly_vulnerability_name(self, vulnerability_type: WizVulnerabilityType) -> str:
        """
        Convert vulnerability type enum to user-friendly name for progress display.

        :param WizVulnerabilityType vulnerability_type: The vulnerability type enum
        :return: User-friendly name
        :rtype: str
        """
        friendly_names = {
            WizVulnerabilityType.VULNERABILITY: "Vulnerabilities",
            WizVulnerabilityType.CONFIGURATION: "Configuration Findings",
            WizVulnerabilityType.HOST_FINDING: "Host Findings",
            WizVulnerabilityType.DATA_FINDING: "Data Findings",
            WizVulnerabilityType.SECRET_FINDING: "Secret Findings",
            WizVulnerabilityType.NETWORK_EXPOSURE_FINDING: "Network Exposures",
            WizVulnerabilityType.END_OF_LIFE_FINDING: "End-of-Life Findings",
            WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE: "External Attack Surface",
            WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING: "Excessive Access Findings",
            WizVulnerabilityType.ISSUE: "Issues",
        }
        return friendly_names.get(vulnerability_type, vulnerability_type.value.replace("_", " ").title())

    def parse_findings_with_progress(
        self, nodes: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType, task_id: Optional[Any] = None
    ) -> Iterator[IntegrationFinding]:
        """
        Parse findings with progress tracking.

        :param List[Dict[str, Any]] nodes: List of Wiz finding nodes
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :param Optional[Any] task_id: Progress task ID for tracking
        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        findings_count = 0
        total_nodes = len(nodes)

        for i, node in enumerate(nodes, 1):
            if finding := self.parse_finding(node, vulnerability_type):
                findings_count += 1
                yield finding

            # Update progress if task_id provided
            # Backwards compatibility: check if finding_progress exists and has advance method
            if task_id is not None and self.finding_progress is not None and hasattr(self.finding_progress, "advance"):
                self.finding_progress.advance(task_id, 1)

        # Log parsing results for this type
        if findings_count != total_nodes:
            logger.info(
                "Parsed %d/%d %s findings successfully (%d failed/skipped)",
                findings_count,
                total_nodes,
                vulnerability_type.value,
                total_nodes - findings_count,
            )

        # Update the total count once at the end to prevent flashing
        self.num_findings_to_process = (self.num_findings_to_process or 0) + findings_count

    def _filter_findings_by_project_with_progress(
        self, nodes: List[Dict[str, Any]], project_id: str, task_id: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter findings by project ID with progress tracking.

        :param List[Dict[str, Any]] nodes: List of finding nodes
        :param str project_id: Project ID to filter by
        :param Optional[Any] task_id: Progress task ID for tracking
        :return: Filtered list of nodes
        :rtype: List[Dict[str, Any]]
        """
        filtered_nodes = []
        original_count = len(nodes)

        for i, node in enumerate(nodes, 1):
            # Check if any of the node's projects match the target project ID
            projects = node.get("projects", [])
            if any(project.get("id") == project_id for project in projects):
                filtered_nodes.append(node)

            # Update progress if task_id provided
            # Backwards compatibility: check if finding_progress exists and has advance method
            if task_id is not None and self.finding_progress is not None and hasattr(self.finding_progress, "advance"):
                self.finding_progress.advance(task_id, 1)

        filtered_count = len(filtered_nodes)
        if filtered_count != original_count:
            logger.info(
                "Filtered findings by project: %d/%d findings match project %s",
                filtered_count,
                original_count,
                project_id,
            )

        return filtered_nodes

    def _filter_findings_by_project(self, nodes: List[Dict[str, Any]], project_id: str) -> List[Dict[str, Any]]:
        """
        Filter findings by project ID for queries that don't support API-level project filtering.

        :param List[Dict[str, Any]] nodes: List of finding nodes
        :param str project_id: Project ID to filter by
        :return: Filtered list of nodes
        :rtype: List[Dict[str, Any]]
        """
        filtered_nodes = []
        original_count = len(nodes)

        for node in nodes:
            # Check if any of the node's projects match the target project ID
            projects = node.get("projects", [])
            if any(project.get("id") == project_id for project in projects):
                filtered_nodes.append(node)

        filtered_count = len(filtered_nodes)
        if filtered_count != original_count:
            logger.info(
                "Filtered findings by project: %d/%d findings match project %s",
                filtered_count,
                original_count,
                project_id,
            )

        return filtered_nodes

    def parse_findings(
        self, nodes: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> Iterator[IntegrationFinding]:
        """
        Parses a list of Wiz finding nodes into IntegrationFinding objects.
        Groups findings by rule and scope for consolidation when appropriate.

        :param List[Dict[str, Any]] nodes: List of Wiz finding nodes
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :yield: IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        logger.debug(f"VULNERABILITY PROCESSING ANALYSIS: Received {len(nodes)} raw Wiz vulnerabilities for processing")

        # Count issues by severity for analysis
        severity_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for node in nodes:
            severity = node.get("severity", "Low")
            status = node.get("status", "OPEN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

        logger.debug(f"Raw vulnerability breakdown by severity: {severity_counts}")
        logger.debug(f"Raw vulnerability breakdown by status: {status_counts}")

        # Filter nodes by minimum severity configuration
        filtered_nodes = []
        filtered_out_count = 0
        for node in nodes:
            wiz_severity = node.get("severity", "Low")
            wiz_id = node.get("id", "unknown")

            # Log sample record for NONE severity (only first occurrence per session)
            if wiz_severity and wiz_severity.upper() == "NONE":
                if not hasattr(self, "_none_severity_sample_logged"):
                    logger.info(
                        f"SAMPLE RECORD - Vulnerability with NONE severity (treating as informational): "
                        f"ID={node.get('id', 'Unknown')}, "
                        f"Name={node.get('name', 'Unknown')}, "
                        f"Type={node.get('type', 'Unknown')}, "
                        f"Severity={wiz_severity}"
                    )
                    self._none_severity_sample_logged = True

            if self.should_process_finding_by_severity(wiz_severity):
                filtered_nodes.append(node)
            else:
                filtered_out_count += 1
                logger.debug(
                    f"FILTERED BY SEVERITY: Vulnerability {wiz_id} with severity '{wiz_severity}' "
                    f"filtered due to minimumSeverity configuration"
                )

        logger.info(
            f"After severity filtering: {len(filtered_nodes)} vulnerabilities kept, {filtered_out_count} filtered out"
        )

        if not filtered_nodes:
            logger.warning(
                "All vulnerabilities filtered out by severity configuration - check your minimumSeverity setting"
            )
            return

        # Apply consolidation logic for findings that support it
        if self._should_apply_consolidation(vulnerability_type):
            yield from self._parse_findings_with_consolidation(filtered_nodes, vulnerability_type)
        else:
            # Use original parsing for vulnerability types that shouldn't be consolidated
            yield from self.parse_findings_with_progress(filtered_nodes, vulnerability_type, task_id=None)

    def _should_apply_consolidation(self, vulnerability_type: WizVulnerabilityType) -> bool:
        """
        Determine if consolidation should be applied for this vulnerability type.

        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :return: True if consolidation should be applied
        :rtype: bool
        """
        # Apply consolidation to finding types that commonly affect multiple assets
        consolidation_types = {
            WizVulnerabilityType.HOST_FINDING,
            WizVulnerabilityType.DATA_FINDING,
            WizVulnerabilityType.VULNERABILITY,
        }
        return vulnerability_type in consolidation_types

    def _parse_findings_with_consolidation(
        self, nodes: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> Iterator[IntegrationFinding]:
        """
        Parse findings with consolidation logic applied.

        :param List[Dict[str, Any]] nodes: List of Wiz finding nodes
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :yield: Consolidated IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        # Group nodes for potential consolidation
        grouped_nodes = self._group_findings_for_consolidation(nodes)

        # Process each group
        for group_key, group_nodes in grouped_nodes.items():
            if len(group_nodes) > 1:
                # Multiple nodes with same rule - attempt consolidation
                if consolidated_finding := self._create_consolidated_scanner_finding(group_nodes, vulnerability_type):
                    yield consolidated_finding
            else:
                # Single node - process normally
                if finding := self.parse_finding(group_nodes[0], vulnerability_type):
                    yield finding

    def _group_findings_for_consolidation(self, nodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group findings by rule and appropriate scope for consolidation.
        - Database findings: group by server
        - App Configuration findings: group by resource group
        - Other findings: group by full resource path

        :param List[Dict[str, Any]] nodes: List of Wiz finding nodes
        :return: Dictionary mapping group keys to lists of nodes
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        groups = {}

        for node in nodes:
            # Create a grouping key based on rule and appropriate scope
            rule_name = self._get_rule_name_from_node(node)
            provider_id = self._get_provider_id_from_node(node)

            # Determine the appropriate grouping scope based on resource type
            grouping_scope = self._determine_grouping_scope(provider_id, rule_name)

            # Group key combines rule name and scope
            group_key = f"{rule_name}|{grouping_scope}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(node)

        return groups

    def _get_rule_name_from_node(self, node: Dict[str, Any]) -> str:
        """Get rule name from various node structures."""
        # Try different ways to get rule name
        if source_rule := node.get("sourceRule"):
            return source_rule.get("name", "")
        return node.get("name", node.get("title", ""))

    def _get_provider_id_from_node(self, node: Dict[str, Any]) -> str:
        """Get provider ID from various node structures."""
        # Try different ways to get provider ID
        if entity_snapshot := node.get("entitySnapshot"):
            return entity_snapshot.get("providerId", "")

        # Try other asset lookup patterns
        asset_fields = ["vulnerableAsset", "entity", "resource", "relatedEntity", "sourceEntity", "target"]
        for field in asset_fields:
            if asset_obj := node.get(field):
                if provider_id := asset_obj.get("providerId"):
                    return provider_id
                # For vulnerability nodes, use asset ID if providerId is not available
                if field == "vulnerableAsset" and (asset_id := asset_obj.get("id")):
                    return asset_id

        return ""

    def _determine_grouping_scope(self, provider_id: str, rule_name: str) -> str:
        """
        Determine the appropriate grouping scope for consolidation.

        :param str provider_id: The provider ID
        :param str rule_name: The rule name
        :return: The grouping scope (server, resource group, or full path)
        :rtype: str
        """
        # For database issues, group by server
        if "/databases/" in provider_id:
            return provider_id.split("/databases/")[0]

        # For App Configuration issues, group by resource group to consolidate multiple stores
        if (
            "app configuration" in rule_name.lower()
            and "/microsoft.appconfiguration/configurationstores/" in provider_id
        ):
            # Extract resource group path: /subscriptions/.../resourcegroups/rg_name
            parts = provider_id.split("/resourcegroups/")
            if len(parts) >= 2:
                rg_part = parts[1].split("/")[0]  # Get just the resource group name
                return f"{parts[0]}/resourcegroups/{rg_part}"

        # For other resources, use the full provider path (no consolidation)
        return provider_id

    def _create_consolidated_scanner_finding(
        self, nodes: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> Optional[IntegrationFinding]:
        """
        Create a consolidated finding from multiple nodes with the same rule.

        :param List[Dict[str, Any]] nodes: List of nodes to consolidate
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :return: Consolidated IntegrationFinding or None
        :rtype: Optional[IntegrationFinding]
        """
        # Use the first node as the base
        base_node = nodes[0]

        # Collect all asset identifiers and provider IDs
        asset_ids = []
        provider_ids = []

        for node in nodes:
            if asset_id := self.get_asset_id_from_node(node, vulnerability_type):
                asset_ids.append(asset_id)
            if provider_id := self.get_provider_unique_id_from_node(node, vulnerability_type):
                provider_ids.append(provider_id)

        # If we couldn't extract asset info, fall back to normal parsing
        if not asset_ids:
            return self.parse_finding(base_node, vulnerability_type)

        # Create the finding using normal parsing, then override asset identifiers
        base_finding = self.parse_finding(base_node, vulnerability_type)
        if not base_finding:
            return None

        # Override with consolidated asset information
        base_finding.asset_identifier = asset_ids[0]  # Use first asset as primary
        base_finding.issue_asset_identifier_value = "\n".join(provider_ids) if provider_ids else None

        return base_finding

    @classmethod
    def get_issue_severity(cls, severity: str) -> regscale_models.IssueSeverity:
        """
        Get the issue severity from the Wiz severity

        :param str severity: The severity of the vulnerability
        :return: The issue severity
        :rtype: regscale_models.IssueSeverity
        """
        normalized_severity = severity.strip().capitalize() if severity else ""
        return cls.finding_severity_map.get(normalized_severity, regscale_models.IssueSeverity.Low)

    def should_process_finding_by_severity(self, wiz_severity: str) -> bool:
        """
        Check if finding should be processed based on minimum severity configuration.

        :param str wiz_severity: The Wiz severity level (e.g., "INFORMATIONAL", "Low", "Medium", etc.)
        :return: True if finding should be processed, False if it should be filtered out
        :rtype: bool
        """
        # Define severity hierarchy mapping (lower priority = higher severity)
        # Maps normalized lowercase severity strings to (IssueSeverity enum, priority level)
        severity_priority_map = {
            "critical": (regscale_models.IssueSeverity.Critical, 0),
            "high": (regscale_models.IssueSeverity.High, 1),
            "medium": (regscale_models.IssueSeverity.Moderate, 2),
            "low": (regscale_models.IssueSeverity.Low, 3),
            "informational": (regscale_models.IssueSeverity.NotAssigned, 4),
            "info": (regscale_models.IssueSeverity.NotAssigned, 4),
            "none": (regscale_models.IssueSeverity.NotAssigned, 4),
        }

        # Validate and cache minimum severity configuration (only once to avoid spam)
        if not hasattr(self, "_validated_min_severity"):
            min_severity_config = self.app.config.get("scanners", {}).get("wiz", {}).get("minimumSeverity", "low")
            min_severity_normalized = min_severity_config.strip().lower() if min_severity_config else "low"

            # Try to intelligently map common variations and synonyms
            severity_aliases = {
                "moderate": "medium",
                "med": "medium",
                "minimal": "low",
                "highest": "critical",
                "crit": "critical",
                "none": "informational",
                "info": "informational",
            }

            # Check if it's a valid value or a known alias
            if min_severity_normalized not in severity_priority_map:
                if min_severity_normalized in severity_aliases:
                    mapped_value = severity_aliases[min_severity_normalized]
                    logger.info(
                        f"Mapped minimumSeverity config '{min_severity_config}' to '{mapped_value}'. "
                        f"Consider using standard values: {', '.join(severity_priority_map.keys())}."
                    )
                    min_severity_normalized = mapped_value
                else:
                    logger.warning(
                        f"Invalid minimumSeverity config: '{min_severity_config}'. "
                        f"Valid values are: {', '.join(severity_priority_map.keys())}. Defaulting to 'low'."
                    )
                    min_severity_normalized = "low"

            self._validated_min_severity = min_severity_normalized
            logger.debug(f"SEVERITY FILTER CONFIG: minimumSeverity = '{min_severity_normalized}'")

        try:
            # Clean and normalize the finding severity string
            wiz_severity_normalized = wiz_severity.strip().lower() if wiz_severity else "informational"

            # Check if finding severity is valid
            if wiz_severity_normalized not in severity_priority_map:
                logger.warning(
                    f"Unknown severity level: '{wiz_severity}' (normalized: '{wiz_severity_normalized}'). "
                    f"Valid values are: {', '.join(severity_priority_map.keys())}. Processing anyway."
                )
                return True

            _, finding_priority = severity_priority_map[wiz_severity_normalized]
            _, min_priority = severity_priority_map[self._validated_min_severity]

            # Process if finding priority is equal or lower (higher severity) than minimum
            return finding_priority <= min_priority
        except Exception as e:
            # If any error occurs, default to processing it
            logger.warning(f"Error processing severity level: {wiz_severity}. Error: {e}. Processing anyway.")
            return True

    def process_comments(self, comments_dict: Dict) -> Optional[str]:
        """
        Processes comments from Wiz findings to match RegScale's comment format.

        :param Dict comments_dict: The comments from the Wiz finding
        :return: If available the Processed comments in RegScale format
        :rtype:  Optional[str]
        """
        result = None

        if comments := comments_dict.get("comments", {}).get("edges", []):
            formatted_comments = [
                f"{edge.get('node', {}).get('author', {}).get('name', 'Unknown')}: "
                f"{edge.get('node', {}).get('body', 'No comment')}"
                for edge in comments
            ]
            # Join with newlines
            result = "\n".join(formatted_comments)
        return result

    def get_asset_id_from_node(self, node: Dict[str, Any], vulnerability_type: WizVulnerabilityType) -> Optional[str]:
        """
        Get the asset ID from a node based on the vulnerability type.

        :param Dict[str, Any] node: The Wiz finding node
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :return: The asset ID or None if not found
        :rtype: Optional[str]
        """
        # Define asset lookup patterns for different vulnerability types
        asset_lookup_patterns = {
            WizVulnerabilityType.VULNERABILITY: "vulnerableAsset",
            WizVulnerabilityType.CONFIGURATION: "resource",
            WizVulnerabilityType.HOST_FINDING: "resource",
            WizVulnerabilityType.DATA_FINDING: "resource",
            WizVulnerabilityType.SECRET_FINDING: "resource",
            WizVulnerabilityType.NETWORK_EXPOSURE_FINDING: "exposedEntity",
            WizVulnerabilityType.END_OF_LIFE_FINDING: "vulnerableAsset",
            WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE: "exposedEntity",
            WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING: "scope",
            WizVulnerabilityType.ISSUE: "entitySnapshot",
        }

        asset_lookup_key = asset_lookup_patterns.get(vulnerability_type, "vulnerableAsset")

        if asset_lookup_key == "scope":
            # Handle special case for excessive access findings where ID is nested
            scope = node.get("scope", {})
            graph_entity = scope.get("graphEntity", {})
            return graph_entity.get("id")

        # Standard case - direct id access
        asset_container = node.get(asset_lookup_key) or {}
        asset_id = asset_container.get("id") if isinstance(asset_container, dict) else None

        # Add debug logging to help diagnose missing assets
        if not asset_id:
            logger.debug(
                f"No asset ID found for {vulnerability_type.value} using key '{asset_lookup_key}'. "
                f"Available keys in node: {list(node.keys())}"
            )
            # Try alternative lookup patterns as fallback
            fallback_keys = ["vulnerableAsset", "resource", "exposedEntity", "entitySnapshot"]
            for fallback_key in fallback_keys:
                if fallback_key != asset_lookup_key and fallback_key in node:
                    fallback_asset = node.get(fallback_key) or {}
                    if isinstance(fallback_asset, dict) and (fallback_id := fallback_asset.get("id")):
                        logger.debug(
                            f"Found asset ID using fallback key '{fallback_key}' for {vulnerability_type.value}"
                        )
                        return fallback_id

        return asset_id

    def get_provider_unique_id_from_node(
        self, node: Dict[str, Any], vulnerability_type: WizVulnerabilityType
    ) -> Optional[str]:
        """
        Get the providerUniqueId from a node based on the vulnerability type.
        This provides more meaningful asset identification for eMASS exports.

        :param Dict[str, Any] node: The Wiz finding node
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :return: The providerUniqueId or fallback to asset name/ID
        :rtype: Optional[str]
        """
        # Define asset lookup patterns for different vulnerability types - aligned with get_asset_id_from_node
        asset_lookup_patterns = {
            WizVulnerabilityType.VULNERABILITY: "vulnerableAsset",
            WizVulnerabilityType.CONFIGURATION: "resource",
            WizVulnerabilityType.HOST_FINDING: "resource",
            WizVulnerabilityType.DATA_FINDING: "resource",
            WizVulnerabilityType.SECRET_FINDING: "resource",
            WizVulnerabilityType.NETWORK_EXPOSURE_FINDING: "exposedEntity",
            WizVulnerabilityType.END_OF_LIFE_FINDING: "vulnerableAsset",
            WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE: "exposedEntity",
            WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING: "scope",
            WizVulnerabilityType.ISSUE: "entitySnapshot",
        }

        asset_lookup_key = asset_lookup_patterns.get(vulnerability_type, "entitySnapshot")

        if asset_lookup_key == "scope":
            # Handle special case for excessive access findings where ID is nested
            scope = node.get("scope", {})
            graph_entity = scope.get("graphEntity", {})
            # Try providerUniqueId first, fallback to name, then id
            return graph_entity.get("providerUniqueId") or graph_entity.get("name") or graph_entity.get("id")

        # Standard case - get asset container and extract provider identifier
        asset_container = node.get(asset_lookup_key) or {}

        # Ensure asset_container is a dict before accessing
        if not isinstance(asset_container, dict):
            return None

        # For Issue queries, the field is called 'providerId' instead of 'providerUniqueId'
        if vulnerability_type == WizVulnerabilityType.ISSUE:
            return (
                asset_container.get("providerId")
                or asset_container.get("providerUniqueId")
                or asset_container.get("name")
                or asset_container.get("id")
            )

        # For other queries, try providerUniqueId first
        return asset_container.get("providerUniqueId") or asset_container.get("name") or asset_container.get("id")

    def parse_finding(
        self, node: Dict[str, Any], vulnerability_type: WizVulnerabilityType
    ) -> Optional[IntegrationFinding]:
        """
        Parses a Wiz finding node into an IntegrationFinding object

        :param Dict[str, Any] node: The Wiz finding node to parse
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        try:
            # Route to specific parsing method based on vulnerability type
            if vulnerability_type == WizVulnerabilityType.SECRET_FINDING:
                return self._parse_secret_finding(node)
            if vulnerability_type == WizVulnerabilityType.NETWORK_EXPOSURE_FINDING:
                return self._parse_network_exposure_finding(node)
            if vulnerability_type == WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE:
                return self._parse_external_attack_surface_finding(node)
            if vulnerability_type == WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING:
                return self._parse_excessive_access_finding(node)
            if vulnerability_type == WizVulnerabilityType.END_OF_LIFE_FINDING:
                return self._parse_end_of_life_finding(node)
            # Fallback to generic parsing for any other types
            return self._parse_generic_finding(node, vulnerability_type)
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Error parsing Wiz finding: %s", str(e), exc_info=True)
            return None

    def _get_secret_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to secret findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: Dictionary containing secret-specific data
        :rtype: Dict[str, Any]
        """
        secret_type = node.get("type", "Unknown Secret")
        resource_name = node.get("resource", {}).get("name", "Unknown Resource")
        # Build description with secret details
        description_parts = [
            f"Secret type: {secret_type}",
            f"Confidence: {node.get('confidence', 'Unknown')}",
            f"Encrypted: {node.get('isEncrypted', False)}",
            f"Managed: {node.get('isManaged', False)}",
        ]

        if rule := node.get("rule", {}):
            description_parts.append(f"Detection rule: {rule.get('name', 'Unknown')}")

        return {
            "category": "Wiz Secret Detection",
            "title": f"Secret Detected: {secret_type} in {resource_name}",
            "description": "\n".join(description_parts),
            "remediation": f"Remove or properly secure the {secret_type} secret found in {resource_name}",
            "plugin_name": f"Wiz Secret Detection - {secret_type}",
            "identification": "Secret Scanning",
        }

    def _parse_secret_finding(self, node: Dict[str, Any]) -> Optional[IntegrationFinding]:
        """
        Parse secret finding from Wiz.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        finding_data = self._get_secret_finding_data(node)
        return self._create_integration_finding(node, WizVulnerabilityType.SECRET_FINDING, finding_data)

    def _create_integration_finding(
        self, node: Dict[str, Any], vulnerability_type: WizVulnerabilityType, finding_data: Dict[str, Any]
    ) -> Optional[IntegrationFinding]:
        """
        Unified method to create IntegrationFinding objects from Wiz data.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :param Dict[str, Any] finding_data: Finding-specific data (title, description, etc.)
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        # Get asset identifier
        asset_id = self.get_asset_id_from_node(node, vulnerability_type)
        if not asset_id:
            logger.debug(
                f"Skipping {vulnerability_type.value} finding '{node.get('name', 'Unknown')}' "
                f"(ID: {node.get('id', 'Unknown')}) - no asset identifier found"
            )
            return None

        # Get meaningful asset identifier for eMASS exports
        provider_unique_id = self.get_provider_unique_id_from_node(node, vulnerability_type)

        # Parse dates
        first_seen = self._get_first_seen_date(node)
        last_seen = self._get_last_seen_date(node, first_seen)
        # Get severity and calculate due date
        severity = self.get_issue_severity(finding_data.get("severity") or node.get("severity", "Low"))
        due_date = regscale_models.Issue.get_due_date(severity, self.app.config, "wiz", first_seen)

        # Get status with diagnostic logging
        wiz_status = node.get("status", "Open")
        logger.debug(f"Processing Wiz finding {node.get('id', 'Unknown')}: raw status from node = '{wiz_status}'")
        status = self.map_status_to_issue_status(wiz_status)

        # Add diagnostic logging for unexpected issue closure
        if status == regscale_models.IssueStatus.Closed and wiz_status.upper() not in ["RESOLVED", "REJECTED"]:
            logger.warning(
                f"Unexpected issue closure: Wiz status '{wiz_status}' mapped to Closed status "
                f"for finding {node.get('id', 'Unknown')} - '{finding_data.get('title', 'Unknown')}'. "
                f"This may indicate a mapping configuration issue."
            )

        # Process comments if available
        comments_dict = node.get("commentThread", {})
        formatted_comments = self.process_comments(comments_dict) if comments_dict else None

        # Build IntegrationFinding with unified data structure
        integration_finding_data = {
            "control_labels": [],
            "category": finding_data.get("category", "Wiz Vulnerability"),
            "title": finding_data.get("title", node.get("name", "Unknown vulnerability")),
            "description": finding_data.get("description", node.get("description", "")),
            "severity": severity,
            "status": status,
            "asset_identifier": asset_id,
            "issue_asset_identifier_value": provider_unique_id,
            "external_id": finding_data.get("external_id", node.get("id")),
            "first_seen": first_seen,
            "date_created": first_seen,
            "last_seen": last_seen,
            "remediation": finding_data.get("remediation", node.get("description", "")),
            "plugin_name": finding_data.get("plugin_name", node.get("name", "Unknown")),
            "vulnerability_type": vulnerability_type.value,
            "due_date": due_date,
            "date_last_updated": format_to_regscale_iso(get_current_datetime()),
            "identification": finding_data.get("identification", "Vulnerability Assessment"),
        }

        # Add optional fields if present
        if formatted_comments:
            integration_finding_data["comments"] = formatted_comments
            integration_finding_data["poam_comments"] = formatted_comments

        # Add CVE-specific fields for generic findings
        if finding_data.get("cve"):
            integration_finding_data["cve"] = finding_data["cve"]
        if finding_data.get("cvss_score"):
            integration_finding_data["cvss_score"] = finding_data["cvss_score"]
            integration_finding_data["cvss_v3_base_score"] = finding_data["cvss_score"]
        if finding_data.get("source_rule_id"):
            integration_finding_data["source_rule_id"] = finding_data["source_rule_id"]

        return IntegrationFinding(**integration_finding_data)

    def _get_first_seen_date(self, node: Dict[str, Any]) -> str:
        """
        Get the first seen date from a Wiz node, with fallbacks.

        :param Dict[str, Any] node: The Wiz finding node
        :return: ISO formatted first seen date
        :rtype: str
        """
        first_seen = node.get("firstSeenAt") or node.get("firstDetectedAt") or get_current_datetime()
        return format_to_regscale_iso(first_seen)

    def _get_last_seen_date(self, node: Dict[str, Any], first_seen_fallback: str) -> str:
        """
        Get the last seen date from a Wiz node, with fallbacks.

        :param Dict[str, Any] node: The Wiz finding node
        :param str first_seen_fallback: Fallback date if no last seen available
        :return: ISO formatted last seen date
        :rtype: str
        """
        last_seen = (
            node.get("lastSeenAt")
            or node.get("lastDetectedAt")
            or node.get("analyzedAt")
            or first_seen_fallback
            or get_current_datetime()
        )
        return format_to_regscale_iso(last_seen)

    def _get_network_exposure_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to network exposure findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: Dictionary containing network exposure-specific data
        :rtype: Dict[str, Any]
        """
        exposed_entity = node.get("exposedEntity", {})
        entity_name = exposed_entity.get("name", "Unknown Entity")
        port_range = node.get("portRange", "Unknown Port")
        # Build description with network details
        description_parts = [
            f"Exposed entity: {entity_name} ({exposed_entity.get('type', 'Unknown Type')})",
            f"Port range: {port_range}",
            f"Source IP range: {node.get('sourceIpRange', 'Unknown')}",
            f"Destination IP range: {node.get('destinationIpRange', 'Unknown')}",
        ]

        if protocols := node.get("appProtocols"):
            description_parts.append(f"Application protocols: {', '.join(protocols)}")
        if net_protocols := node.get("networkProtocols"):
            description_parts.append(f"Network protocols: {', '.join(net_protocols)}")

        return {
            "category": "Wiz Network Exposure",
            "title": f"Network Exposure: {entity_name} on {port_range}",
            "description": "\n".join(description_parts),
            "severity": "Medium",  # Network exposures typically don't have explicit severity
            "remediation": f"Review and restrict network access to {entity_name} on {port_range}",
            "plugin_name": f"Wiz Network Exposure - {port_range}",
            "identification": "Network Security Assessment",
        }

    def _parse_network_exposure_finding(self, node: Dict[str, Any]) -> Optional[IntegrationFinding]:
        """Parse network exposure finding from Wiz.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        finding_data = self._get_network_exposure_finding_data(node)
        return self._create_integration_finding(node, WizVulnerabilityType.NETWORK_EXPOSURE_FINDING, finding_data)

    def _get_external_attack_surface_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to external attack surface findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: Dictionary containing external attack surface-specific data
        :rtype: Dict[str, Any]
        """
        exposed_entity = node.get("exposedEntity", {})
        entity_name = exposed_entity.get("name", "Unknown Entity")
        port_range = node.get("portRange", "Unknown Port")
        # Build description with attack surface details
        description_parts = [
            f"Externally exposed entity: {entity_name} ({exposed_entity.get('type', 'Unknown Type')})",
            f"Exposed port range: {port_range}",
            f"Source IP range: {node.get('sourceIpRange', 'Public Internet')}",
        ]

        if protocols := node.get("appProtocols"):
            description_parts.append(f"Application protocols: {', '.join(protocols)}")
        if endpoints := node.get("applicationEndpoints"):
            endpoint_names = [ep.get("name", "Unknown") for ep in endpoints[:3]]  # Limit to first 3
            description_parts.append(f"Application endpoints: {', '.join(endpoint_names)}")

        return {
            "category": "Wiz External Attack Surface",
            "title": f"External Attack Surface: {entity_name} exposed on {port_range}",
            "description": "\n".join(description_parts),
            "severity": "High",  # External attack surface findings are typically high severity
            "remediation": f"Review external exposure of {entity_name} and implement proper access controls",
            "plugin_name": f"Wiz External Attack Surface - {port_range}",
            "identification": "External Attack Surface Assessment",
        }

    def _parse_external_attack_surface_finding(self, node: Dict[str, Any]) -> Optional[IntegrationFinding]:
        """Parse external attack surface finding from Wiz.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        finding_data = self._get_external_attack_surface_finding_data(node)
        return self._create_integration_finding(node, WizVulnerabilityType.EXTERNAL_ATTACH_SURFACE, finding_data)

    def _get_excessive_access_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to excessive access findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: Dictionary containing excessive access-specific data
        :rtype: Dict[str, Any]
        """
        # Add remediation details
        remediation_parts = [node.get("description", "")]
        if remediation_instructions := node.get("remediationInstructions"):
            remediation_parts.append(f"Remediation: {remediation_instructions}")
        if policy_name := node.get("builtInPolicyRemediationName"):
            remediation_parts.append(f"Built-in policy: {policy_name}")

        return {
            "category": "Wiz Excessive Access",
            "title": node.get("name", "Excessive Access Detected"),
            "description": node.get("description", ""),
            "remediation": "\n".join(filter(None, remediation_parts)),
            "plugin_name": f"Wiz Excessive Access - {node.get('remediationType', 'Unknown')}",
            "identification": "Access Control Assessment",
        }

    def _parse_excessive_access_finding(self, node: Dict[str, Any]) -> Optional[IntegrationFinding]:
        """Parse excessive access finding from Wiz.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: The parsed IntegrationFinding or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        finding_data = self._get_excessive_access_finding_data(node)
        return self._create_integration_finding(node, WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING, finding_data)

    def _get_end_of_life_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to end of life findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :return: Dictionary containing end of life-specific data
        :rtype: Dict[str, Any]
        """
        name = node.get("name", "Unknown Technology")

        # Build description with EOL details
        description_parts = [node.get("description", "")]
        if eol_date := node.get("technologyEndOfLifeAt"):
            description_parts.append(f"End of life date: {eol_date}")
        if recommended_version := node.get("recommendedVersion"):
            description_parts.append(f"Recommended version: {recommended_version}")

        return {
            "category": "Wiz End of Life",
            "title": f"End of Life: {name}",
            "description": "\n".join(filter(None, description_parts)),
            "severity": "High",  # End of life findings are typically high severity
            "remediation": f"Upgrade {name} to a supported version",
            "plugin_name": f"Wiz End of Life - {name}",
            "identification": "Technology Lifecycle Assessment",
        }

    def _parse_end_of_life_finding(self, node: Dict[str, Any]) -> Optional[IntegrationFinding]:
        """Parse end of life finding from Wiz."""
        finding_data = self._get_end_of_life_finding_data(node)
        return self._create_integration_finding(node, WizVulnerabilityType.END_OF_LIFE_FINDING, finding_data)

    def _get_generic_finding_data(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to generic findings.

        :param Dict[str, Any] node: The Wiz finding node to parse
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :return: Dictionary containing generic finding-specific data
        :rtype: Dict[str, Any]
        """
        name: str = node.get("name", "")
        cve = (
            name
            if name and (name.startswith("CVE") or name.startswith("GHSA")) and not node.get("cve")
            else node.get("cve", name)
        )

        return {
            "category": "Wiz Vulnerability",
            "title": node.get("name", "Unknown vulnerability"),
            "description": node.get("description", ""),
            "external_id": f"{node.get('sourceRule', {'id': cve}).get('id')}",
            "remediation": node.get("description", ""),
            "plugin_name": cve,
            "identification": "Vulnerability Assessment",
            "cve": cve,
            "cvss_score": node.get("score"),
            "source_rule_id": node.get("sourceRule", {}).get("id"),
        }

    def _parse_generic_finding(
        self, node: Dict[str, Any], vulnerability_type: WizVulnerabilityType
    ) -> Optional[IntegrationFinding]:
        """Generic parsing method for fallback cases."""
        finding_data = self._get_generic_finding_data(node)
        return self._create_integration_finding(node, vulnerability_type, finding_data)

    def get_compliance_settings(self):
        """
        Get compliance settings for status mapping

        :return: Compliance settings instance
        :rtype: Optional[ComplianceSettings]
        """
        if self._compliance_settings is None:
            try:
                settings = ComplianceSettings.get_by_current_tenant()
                self._compliance_settings = next(
                    (comp for comp in settings if comp.title == "Wiz Compliance Setting"), None
                )
                if not self._compliance_settings:
                    logger.debug("No Wiz Compliance Setting found, using default status mapping")
                else:
                    logger.debug("Using Wiz Compliance Setting for status mapping")
            except Exception as e:
                logger.debug(f"Error getting Compliance Setting: {e}")
                self._compliance_settings = None
        return self._compliance_settings

    def map_status_to_issue_status(self, status: str) -> IssueStatus:
        """
        Maps the Wiz status to issue status using compliance settings if available

        :param str status: Status of the vulnerability
        :return: Issue status
        :rtype: IssueStatus
        """
        compliance_settings = self.get_compliance_settings()

        if compliance_settings:
            mapped_status = self._get_status_from_compliance_settings(status, compliance_settings)
            if mapped_status:
                return mapped_status

        # Fallback to default mapping
        return self._get_default_issue_status_mapping(status)

    def _get_status_from_compliance_settings(self, status: str, compliance_settings) -> Optional[IssueStatus]:
        """
        Get issue status from compliance settings

        :param str status: Wiz status
        :param compliance_settings: Compliance settings object
        :return: Issue status or None if not found
        :rtype: Optional[IssueStatus]
        """
        try:
            status_labels = compliance_settings.get_field_labels("status")
            status_lower = status.lower()

            for label in status_labels:
                mapped_status = self._match_wiz_status_to_label(status_lower, label)
                if mapped_status:
                    return mapped_status

            logger.debug(f"No matching compliance setting found for status: {status}")
            return None

        except Exception as e:
            logger.debug(f"Error using compliance settings for status mapping: {e}")
            return None

    def _match_wiz_status_to_label(self, status_lower: str, label: str) -> Optional[IssueStatus]:
        """
        Match a Wiz status to a compliance label and return appropriate IssueStatus

        :param str status_lower: Lowercase Wiz status
        :param str label: Compliance setting label to check
        :return: Matched IssueStatus or None
        :rtype: Optional[IssueStatus]
        """
        label_lower = label.lower()

        logger.debug(f"Checking compliance label matching: status='{status_lower}', label='{label_lower}'")

        # Check for open status mappings (including IN_PROGRESS)
        if status_lower in ["open", "in_progress"] and label_lower in [
            "open",
            "active",
            "new",
            "in progress",
            "in_progress",
        ]:
            logger.debug(f"Matched status '{status_lower}' with label '{label_lower}' -> IssueStatus.Open")
            return IssueStatus.Open

        # Check for closed status mappings
        if status_lower in ["resolved", "rejected"] and label_lower in ["closed", "resolved", "rejected", "completed"]:
            logger.debug(f"Matched status '{status_lower}' with label '{label_lower}' -> IssueStatus.Closed")
            return IssueStatus.Closed

        return None

    def _get_default_issue_status_mapping(self, status: str) -> IssueStatus:
        """
        Get default issue status mapping for a Wiz status

        :param str status: Wiz status
        :return: Default issue status
        :rtype: IssueStatus
        """
        status_lower = status.lower()

        # Add debug logging to trace status mapping
        logger.debug(f"Mapping Wiz status: original='{status}', lowercase='{status_lower}'")

        # Map open and in-progress statuses to Open
        if status_lower in ["open", "in_progress"]:
            logger.debug(f"Wiz status '{status}' mapped to IssueStatus.Open")
            return IssueStatus.Open
        # Map resolved and rejected statuses to Closed
        if status_lower in ["resolved", "rejected"]:
            logger.debug(f"Wiz status '{status}' mapped to IssueStatus.Closed")
            return IssueStatus.Closed
        # Default to Open for any unknown status
        logger.debug(f"Unknown Wiz status '{status}' encountered, defaulting to Open")
        return IssueStatus.Open

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """
        Fetches Wiz assets using the GraphQL API with detailed progress tracking

        :yields: Iterator[IntegrationAsset]
        """
        # Create main task for asset fetching process
        main_task = self.asset_progress.add_task("[cyan]Fetching Wiz assets...", total=3)  # Auth, Query, Parse steps

        # Step 1: Authentication
        auth_task = self.asset_progress.add_task("[yellow]Authenticating to Wiz API...", total=None)

        self.authenticate(kwargs.get("client_id"), kwargs.get("client_secret"))

        self.asset_progress.update(
            auth_task, description="[green]✓ Successfully authenticated to Wiz API", completed=1, total=1
        )
        self.asset_progress.advance(main_task, 1)

        # Step 2: Query preparation and execution
        wiz_project_id: str = kwargs.get("wiz_project_id", "")
        filter_by_override: Dict[str, Any] = kwargs.get("filter_by_override") or WizVariables.wizInventoryFilterBy or {}
        filter_by = self.get_filter_by(filter_by_override, wiz_project_id)

        variables = self.get_variables()
        variables["filterBy"].update(filter_by)

        query_task = self.asset_progress.add_task(
            f"[yellow]Querying Wiz inventory for project {wiz_project_id[:8]}...", total=None
        )

        nodes = self.fetch_wiz_data_if_needed(
            query=INVENTORY_QUERY, variables=variables, topic_key="cloudResources", file_path=INVENTORY_FILE_PATH
        )

        self.asset_progress.update(
            query_task, description=f"[green]✓ Fetched {len(nodes)} assets from Wiz inventory", completed=1, total=1
        )
        self.asset_progress.advance(main_task, 1)

        self.num_assets_to_process = len(nodes)

        # Step 3: Parse assets with progress tracking
        if nodes:
            parse_task = self.asset_progress.add_task(f"[magenta]Parsing {len(nodes)} Wiz assets...", total=len(nodes))

            parsed_count = 0
            for i, node in enumerate(nodes, 1):
                if asset := self.parse_asset(node):
                    parsed_count += 1
                    yield asset

                self.asset_progress.advance(parse_task, 1)

            self.asset_progress.update(
                parse_task, description=f"[green]✓ Successfully parsed {parsed_count}/{len(nodes)} assets"
            )

        self.asset_progress.advance(main_task, 1)
        self.asset_progress.update(
            main_task, description=f"[green]✓ Completed Wiz asset fetching ({self.num_assets_to_process} assets)"
        )

        logger.info("Fetched %d Wiz assets.", len(nodes))

    @staticmethod
    def get_filter_by(filter_by_override: Union[str, Dict[str, Any]], wiz_project_id: str) -> Dict[str, Any]:
        """
        Constructs the filter_by dictionary for fetching assets

        :param Union[str, Dict[str, Any]] filter_by_override: Override for the filter_by dictionary
        :param str wiz_project_id: The Wiz project ID
        :return: The filter_by dictionary
        :rtype: Dict[str, Any]
        """
        if filter_by_override:
            return json.loads(filter_by_override) if isinstance(filter_by_override, str) else filter_by_override
        filter_by = {"project": wiz_project_id}
        if WizVariables.wizLastInventoryPull and not WizVariables.wizFullPullLimitHours:
            filter_by["updatedAt"] = {"after": WizVariables.wizLastInventoryPull}  # type: ignore
        return filter_by

    def get_software_details(
        self, wiz_entity_properties: dict, node: dict[str, Any], software_name_dict: dict[str, str], name: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Gets the software version, vendor, and name from the Wiz entity properties and node.
        Handles container images differently by extracting the version and name from the image tags.
        :param Dict wiz_entity_properties: The properties of the Wiz entity
        :param Dict node: The Wiz node containing the entity
        :param Dict software_name_dict: Dictionary containing software name and vendor
        :param str name: The name of the software or container image
        :return: A tuple containing software_version, software_vendor, and software_name
        :rtype: Tuple[Optional[str], Optional[str], Optional[str]]
        """
        if node.get("type", "") == "CONTAINER_IMAGE":
            software_version = handle_container_image_version(
                image_tags=wiz_entity_properties.get("imageTags", []), name=name
            )
            software_name = name.split(":")[0].split("/")[-1] if name else ""
            software_vendor = name.split(":")[0].split("/")[1] if len(name.split(":")[0].split("/")) > 1 else None
        else:
            software_version = self.get_software_version(wiz_entity_properties, node)
            software_name = self.get_software_name(software_name_dict, wiz_entity_properties, node)
            software_vendor = self.get_software_vendor(software_name_dict, wiz_entity_properties, node)

        return software_version, software_vendor, software_name

    @lru_cache()
    def get_user_id(self) -> str:
        """Function to return the default user ID
        :return: The default user ID as a string
        """
        return RegScaleModel.get_user_id()

    def parse_asset(self, node: Dict[str, Any]) -> Optional[IntegrationAsset]:
        """
        Parses Wiz assets

        :param Dict[str, Any] node: The Wiz asset to parse
        :return: The parsed IntegrationAsset
        :rtype: Optional[IntegrationAsset]
        """

        wiz_entity = node.get("graphEntity", {})
        name = wiz_entity.get("providerUniqueId") or node.get("name", "")
        if not wiz_entity:
            logger.warning("No graph entity found for asset %s", name)
            return None

        wiz_entity_properties = wiz_entity.get("properties", {})
        is_public = False
        if (public_exposures := wiz_entity.get("publicExposures")) and (
            exposure_count := public_exposures.get("totalCount")
        ):
            is_public = exposure_count > 0

        network_dict = get_network_info(wiz_entity_properties)
        handle_provider_dict = handle_provider(wiz_entity_properties)
        software_name_dict = get_software_name_from_cpe(wiz_entity_properties, name)
        software_list = self.create_name_version_dict(wiz_entity_properties.get("installedPackages", []))
        ports_and_protocols = self.get_ports_and_protocols(wiz_entity_properties)

        software_version, software_vendor, software_name = self.get_software_details(
            wiz_entity_properties, node, software_name_dict, name
        )

        return IntegrationAsset(
            name=name,
            external_id=node.get("name"),
            asset_tag_number=node.get("id", ""),
            other_tracking_number=node.get("id", ""),
            identifier=node.get("id", ""),
            asset_type=create_asset_type(node.get("type", "")),
            asset_owner_id=self.get_user_id(),
            parent_id=self.plan_id,
            parent_module=regscale_models.SecurityPlan.get_module_slug(),
            asset_category=map_category(node),
            date_last_updated=wiz_entity.get("lastSeen", ""),
            management_type=handle_management_type(wiz_entity_properties),
            status=self.map_wiz_status(wiz_entity_properties.get("status")),
            ip_address=network_dict.get("ip4_address"),
            ipv6_address=network_dict.get("ip6_address"),
            software_vendor=software_vendor,
            software_version=software_version,
            software_name=software_name,
            location=wiz_entity_properties.get("region"),
            notes=get_notes_from_wiz_props(wiz_entity_properties, node.get("id", "")),
            model=wiz_entity_properties.get("nativeType"),
            manufacturer=wiz_entity_properties.get("cloudPlatform"),
            serial_number=get_product_ids(wiz_entity_properties),
            is_public_facing=is_public,
            azure_identifier=handle_provider_dict.get("azureIdentifier", ""),
            mac_address=wiz_entity_properties.get("macAddress"),
            fqdn=network_dict.get("dns") or wiz_entity_properties.get("dnsName"),
            disk_storage=get_disk_storage(wiz_entity_properties) or 0,
            cpu=pull_resource_info_from_props(wiz_entity_properties)[1] or 0,
            ram=pull_resource_info_from_props(wiz_entity_properties)[0] or 0,
            operating_system=wiz_entity_properties.get("operatingSystem"),
            os_version=wiz_entity_properties.get("version"),
            end_of_life_date=wiz_entity_properties.get("versionEndOfLifeDate"),
            vlan_id=wiz_entity_properties.get("zone"),
            uri=network_dict.get("url"),
            aws_identifier=handle_provider_dict.get("awsIdentifier", ""),
            google_identifier=handle_provider_dict.get("googleIdentifier", ""),
            other_cloud_identifier=handle_provider_dict.get("otherCloudIdentifier", ""),
            patch_level=get_latest_version(wiz_entity_properties),
            cpe=wiz_entity_properties.get("cpe"),
            component_names=collect_components_to_create([node], []),
            source_data=node,
            url=wiz_entity_properties.get("cloudProviderURL"),
            ports_and_protocols=ports_and_protocols,
            software_inventory=software_list,
        )

    @staticmethod
    def get_ports_and_protocols(wiz_entity_properties: dict) -> List[Dict[str, Union[int, str]]]:
        """
        Extracts ports and protocols from Wiz entity properties using the "portStart","portEnd", and "protocol" keys.

        :param dict wiz_entity_properties: Dictionary containing Wiz entity properties
        :return: A list of dictionaries containing start_port, end_port, and protocol
        :rtype: List[Dict[str, Union[int, str]]]
        """
        start_port = wiz_entity_properties.get("portStart")
        if start_port is not None and isinstance(start_port, (int, str)):
            end_port = wiz_entity_properties.get("portEnd", start_port)
            if not isinstance(end_port, (int, str)):
                end_port = start_port

            protocol = wiz_entity_properties.get("protocols") or wiz_entity_properties.get("protocol")
            if not protocol or protocol == "other":
                protocol = get_base_protocol_from_port(start_port) or "tcp"

            # Ensure protocol is a string
            if not isinstance(protocol, str):
                protocol = "tcp"

            return [{"start_port": start_port, "end_port": end_port, "protocol": protocol}]
        return []

    @staticmethod
    def get_software_vendor(software_name_dict: dict, wiz_entity_properties: dict, node: dict) -> Optional[str]:
        """
        Gets the software vendor from the software name dictionary or Wiz entity properties.

        :param dict software_name_dict: Dictionary containing software name and vendor
        :param dict wiz_entity_properties: Properties of the Wiz entity
        :param dict node: Node dictionary
        :return: Software vendor
        :rtype: Optional[str]
        """

        if map_category(node) == regscale_models.AssetCategory.Software:
            return software_name_dict.get("software_vendor") or wiz_entity_properties.get("cloudPlatform")
        return None

    @staticmethod
    def get_software_version(wiz_entity_properties: dict, node: dict) -> Optional[str]:
        """
        Gets the software version from the Wiz entity properties or handles it based on the node type.

        :param dict wiz_entity_properties: Properties of the Wiz entity
        :param dict node: Node dictionary
        :return: Software version
        :rtype: Optional[str]
        """
        if map_category(node) == regscale_models.AssetCategory.Software:
            return handle_software_version(wiz_entity_properties, regscale_models.AssetCategory.Software) or "1.0"
        return None

    @staticmethod
    def get_software_name(software_name_dict: dict, wiz_entity_properties: dict, node: dict) -> Optional[str]:
        """
        Gets the software name from the software name dictionary or Wiz entity properties.
        If no software name is present, assigns a name based on the parent asset and assigned component type.

        :param dict software_name_dict: Dictionary containing software name and vendor
        :param dict wiz_entity_properties: Properties of the Wiz entity
        :param dict node: Node dictionary
        :return: Software name
        :rtype: Optional[str]
        """
        if map_category(node) != regscale_models.AssetCategory.Software:
            return None

        # First try CPE-derived software name
        if software_name := software_name_dict.get("software_name"):
            return software_name

        # Then try nativeType if it exists and looks meaningful
        native_type = wiz_entity_properties.get("nativeType")
        if native_type and not native_type.startswith(("Microsoft.", "AWS::", "Google.")):
            return native_type

        # Finally, generate a name based on parent asset and component type
        parent_name = node.get("name", "")
        component_type = node.get("type", "").replace("_", " ").title()

        if not parent_name:
            return component_type

        # Clean up parent name for better readability by removing
        # common prefixes/suffixes that aren't meaningful
        cleaned_parent = parent_name
        for prefix in ["1-", "temp-", "test-"]:
            if cleaned_parent.lower().startswith(prefix):
                cleaned_parent = cleaned_parent[len(prefix) :]
        return f"{cleaned_parent} - {component_type}" if cleaned_parent else component_type

    # Pre-compiled regex for better performance (ReDoS-safe pattern)
    _PACKAGE_PATTERN = re.compile(r"([^()]+) \(([^()]+)\)")

    @classmethod
    def create_name_version_dict(cls, package_list: List[str]) -> List[Dict[str, str]]:
        """
        Creates a list of dictionaries with package names and versions from formatted strings.

        :param List[str] package_list: List of strings in format "name (version)"
        :return: List of dictionaries with name and version keys
        :rtype: List[Dict[str, str]]
        """
        # Use list comprehension with pre-compiled regex for better performance
        return [
            {"name": match.group(1).strip(), "version": match.group(2).strip()}
            for package in package_list
            if (match := cls._PACKAGE_PATTERN.match(package))
        ]

    @staticmethod
    def map_wiz_status(wiz_status: Optional[str]) -> regscale_models.AssetStatus:
        """Map Wiz status to RegScale status."""
        return regscale_models.AssetStatus.Active if wiz_status != "Inactive" else regscale_models.AssetStatus.Inactive

    def fetch_wiz_data_if_needed(self, query: str, variables: Dict, topic_key: str, file_path: str) -> List[Dict]:
        """
        Fetch Wiz data if needed and save to file if not already fetched within the last 8 hours and return the data

        :param str query: GraphQL query string
        :param Dict variables: Query variables
        :param str topic_key: The key for the data in the response
        :param str file_path: Path to save the fetched data
        :return: List of nodes as dictionaries
        :rtype: List[Dict]
        """
        max_age_hours = WizVariables.wizFullPullLimitHours or 8

        def fetch_fresh_data():
            # Ensure we have a valid token (should already be set by caller)
            if not self.wiz_token:
                error_and_exit("Wiz token is not set. Please authenticate before calling fetch_wiz_data_if_needed.")

            return fetch_wiz_data(
                query=query,
                variables=variables,
                api_endpoint_url=WizVariables.wizUrl,
                token=self.wiz_token,
                topic_key=topic_key,
            )

        return FileOperations.load_cache_or_fetch(
            file_path=file_path,
            fetch_fn=fetch_fresh_data,
            max_age_hours=max_age_hours,
            save_cache=True,
        )

    def get_asset_by_identifier(self, identifier: str) -> Optional[regscale_models.Asset]:
        """
        Enhanced asset lookup with diagnostic logging for Wiz integration

        :param str identifier: The identifier of the asset
        :return: The asset
        :rtype: Optional[regscale_models.Asset]
        """
        # First try to get asset using parent method
        asset = self.asset_map_by_identifier.get(identifier)

        # If asset not found and we haven't already alerted for this asset
        if not asset and identifier not in self.alerted_assets:
            self.alerted_assets.add(identifier)

            # Add debug logging to confirm this method is being called
            logger.debug("WizVulnerabilityIntegration.get_asset_by_identifier called for %s", identifier)

            # Try to provide more diagnostic information
            if not getattr(self, "suppress_asset_not_found_errors", False):
                self._log_missing_asset_diagnostics(identifier)
                # Still log the original warning for consistency
                logger.warning("1. Asset not found for identifier %s", identifier)

        return asset

    def _log_missing_asset_diagnostics(self, identifier: str) -> None:
        """
        Log diagnostic information about missing assets to help identify patterns

        :param str identifier: The missing asset identifier
        :rtype: None
        """
        # Only log detailed diagnostics for the first occurrence of each asset
        if identifier in self.alerted_assets:
            return

        logger.debug("Analyzing missing asset: %s", identifier)

        # Define inventory files to search (constant moved up for clarity)
        inventory_files = (
            INVENTORY_FILE_PATH,
            SECRET_FINDINGS_FILE_PATH,
            NETWORK_EXPOSURE_FILE_PATH,
            END_OF_LIFE_FILE_PATH,
            EXTERNAL_ATTACK_SURFACE_FILE_PATH,
        )

        # Search for asset information across files
        asset_info, source_file = self._search_asset_in_files(identifier, inventory_files)

        # Log results based on what was found
        if asset_info:
            self._log_found_asset_details(identifier, asset_info, source_file)
        else:
            self._log_asset_not_found(identifier)

    def _search_asset_in_files(self, identifier: str, file_paths: tuple) -> tuple[Optional[Dict], Optional[str]]:
        """
        Search for asset information across multiple JSON files

        :param str identifier: Asset identifier to search for
        :param tuple file_paths: Tuple of file paths to search
        :return: Tuple of (asset_info, source_file) or (None, None)
        :rtype: tuple[Optional[Dict], Optional[str]]
        """
        return FileOperations.search_json_files(
            identifier=identifier,
            file_paths=list(file_paths),
            match_fn=self._find_asset_in_node,
        )

    def _log_found_asset_details(self, identifier: str, asset_info: Dict, source_file: str) -> None:
        """
        Log details for found asset with actionable recommendations

        :param str identifier: Asset identifier
        :param Dict asset_info: Asset information from file
        :param str source_file: Source file where asset was found
        :rtype: None
        """
        asset_type = self._extract_asset_type_from_node(asset_info)
        asset_name = self._extract_asset_name_from_node(asset_info)

        # Track missing asset types for summary reporting
        self._missing_asset_types.add(asset_type)

        logger.info(
            "Missing asset found in cached data - ID: %s, Type: %s, Name: '%s', Source: %s\n"
            "   Action: Consider adding '%s' to RECOMMENDED_WIZ_INVENTORY_TYPES in constants.py\n"
            "   Then re-run: regscale wiz inventory --wiz_project_id <project_id> -id <plan_id>",
            identifier,
            asset_type,
            asset_name,
            source_file,
            asset_type,
        )

    def _log_asset_not_found(self, identifier: str) -> None:
        """
        Log message when asset is not found in any cached files

        :param str identifier: Asset identifier
        :rtype: None
        """
        logger.debug(
            "Asset not found in cached data - ID: %s. Possible reasons: "
            "(1) Asset from different Wiz project, "
            "(2) Asset type not included in queries, "
            "(3) Asset deleted from Wiz",
            identifier,
        )

    # Class-level constants for better performance (avoid recreating lists)
    _ASSET_ID_PATHS = (
        ("id",),
        ("resource", "id"),
        ("exposedEntity", "id"),
        ("vulnerableAsset", "id"),
        ("scope", "graphEntity", "id"),
        ("entitySnapshot", "id"),
    )

    _ASSET_TYPE_PATHS = (
        ("type",),
        ("resource", "type"),
        ("exposedEntity", "type"),
        ("vulnerableAsset", "type"),
        ("scope", "graphEntity", "type"),
        ("entitySnapshot", "type"),
    )

    _ASSET_NAME_PATHS = (
        ("name",),
        ("resource", "name"),
        ("exposedEntity", "name"),
        ("vulnerableAsset", "name"),
        ("scope", "graphEntity", "name"),
        ("entitySnapshot", "name"),
    )

    def _find_asset_in_node(self, node: Dict[str, Any], identifier: str) -> bool:
        """
        Check if a node contains the specified asset identifier.

        :param Dict[str, Any] node: Node to search in
        :param str identifier: Asset identifier to find
        :return: True if identifier found, False otherwise
        :rtype: bool
        """
        return any(self._get_nested_value(node, path) == identifier for path in self._ASSET_ID_PATHS)

    def _extract_asset_type_from_node(self, node: Dict[str, Any]) -> str:
        """
        Extract asset type from a node for diagnostic purposes.

        :param Dict[str, Any] node: Node to extract type from
        :return: Asset type or "Unknown Type"
        :rtype: str
        """
        for path in self._ASSET_TYPE_PATHS:
            value = self._get_nested_value(node, path)
            if isinstance(value, str):
                return value
        return "Unknown Type"

    def _extract_asset_name_from_node(self, node: Dict[str, Any]) -> str:
        """
        Extract asset name from a node for diagnostic purposes.

        :param Dict[str, Any] node: Node to extract name from
        :return: Asset name or "Unknown Name"
        :rtype: str
        """
        for path in self._ASSET_NAME_PATHS:
            value = self._get_nested_value(node, path)
            if isinstance(value, str):
                return value
        return "Unknown Name"

    def _get_nested_value(self, data: Dict[str, Any], path: tuple) -> Any:
        """
        Get a nested value from a dictionary using a path tuple.

        :param Dict[str, Any] data: Dictionary to traverse
        :param tuple path: Tuple of keys representing the path
        :return: Value at path or None if not found
        :rtype: Any
        """
        current = data
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current
