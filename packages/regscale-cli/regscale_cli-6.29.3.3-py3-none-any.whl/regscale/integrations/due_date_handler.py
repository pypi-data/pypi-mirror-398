#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Due Date Handler for Scanner Integrations"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

from regscale.core.app.application import Application
from regscale.core.utils.date import get_day_increment
from regscale.integrations.public.cisa import pull_cisa_kev
from regscale.models import regscale_models
from regscale.utils.threading import ThreadSafeDict

logger = logging.getLogger("regscale")

# Date format constant for consistent datetime string formatting
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class DueDateHandler:
    """
    Handles due date calculations for scanner integrations based on:
    1. Init.yaml timeline configurations per integration
    2. KEV (Known Exploited Vulnerabilities) dates from CISA
    3. Default severity-based timelines
    4. Configurable past due date validation (noPastDueDates setting)

    Configuration Options:
    - Global setting: issues.noPastDueDates (default: false - server-side validation removed)
    - Per-integration: issues.{integration_name}.noPastDueDates

    When noPastDueDates=true:
    - Due dates calculated in the past are automatically adjusted to future dates
    - Useful if client-side validation is needed

    When noPastDueDates=false (default):
    - Original due dates are preserved, even if they're in the past
    - Allows importing closed issues with past due dates
    - Server-side validation has been removed to support this
    """

    def __init__(self, integration_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DueDateHandler for a specific integration

        :param str integration_name: Name of the integration (e.g., 'wiz', 'qualys', 'tenable')
        :param Optional[Dict[str, Any]] config: Optional config override, uses Application config if None
        """
        self.integration_name = integration_name.lower()
        self.config = config or Application().config
        self._kev_data: Optional[ThreadSafeDict] = None

        # Default due date timelines (days)
        self.default_timelines = {
            regscale_models.IssueSeverity.Critical: 30,
            "critical": 30,
            regscale_models.IssueSeverity.High: 60,
            "high": 60,
            regscale_models.IssueSeverity.Moderate: 120,
            "moderate": 120,
            regscale_models.IssueSeverity.Low: 364,
            "low": 364,
            regscale_models.IssueSeverity.NotAssigned: 364,  # Default to Low severity timeline
            "notassigned": 364,
        }

        # Load integration-specific timelines from config
        self.integration_timelines = self._load_integration_timelines()

        # Load noPastDueDates setting (defaults to True)
        self.no_past_due_dates = self._load_no_past_due_dates_setting()

    def _load_integration_timelines(self) -> Dict[regscale_models.IssueSeverity, int]:
        """
                Load timeline configurations for this integration from init.yaml
        mv
                :return: Dictionary mapping severity to days
                :rtype: Dict[regscale_models.IssueSeverity, int]
        """
        timelines = self.default_timelines.copy()

        issues_config = self.config.get("issues", {})
        integration_config = issues_config.get(self.integration_name, {})

        if integration_config:
            logger.debug(f"Found timeline config for {self.integration_name}: {integration_config}")

            # Map config keys to severity levels
            severity_mapping = {
                "critical": regscale_models.IssueSeverity.Critical,
                "high": regscale_models.IssueSeverity.High,
                "moderate": regscale_models.IssueSeverity.Moderate,
                "medium": regscale_models.IssueSeverity.Moderate,  # Some integrations use 'medium'
                "low": regscale_models.IssueSeverity.Low,
                "notassigned": regscale_models.IssueSeverity.NotAssigned,  # Handle unassigned severities
            }

            for config_key, severity in severity_mapping.items():
                if config_key in integration_config:
                    timelines[severity] = integration_config[config_key]

        return timelines

    def _load_no_past_due_dates_setting(self) -> bool:
        """
        Load noPastDueDates setting for this integration from init.yaml

        Configuration hierarchy:
        1. Integration-specific setting: issues.{integration_name}.noPastDueDates
        2. Global setting: issues.noPastDueDates
        3. Default: False (allow past due dates - server-side validation removed)

        :return: True if past due dates should be automatically adjusted to future dates
        :rtype: bool
        """
        issues_config = self.config.get("issues", {})
        integration_config = issues_config.get(self.integration_name, {})

        # Check integration-specific setting first
        if "noPastDueDates" in integration_config:
            setting = integration_config["noPastDueDates"]
            logger.debug(f"Using integration-specific noPastDueDates={setting} for {self.integration_name}")
            return bool(setting)

        # Fall back to global setting
        if "noPastDueDates" in issues_config:
            setting = issues_config["noPastDueDates"]
            logger.debug(f"Using global noPastDueDates={setting} for {self.integration_name}")
            return bool(setting)

        # Default to False (allow past due dates - server-side validation removed)
        logger.debug(f"Using default noPastDueDates=False for {self.integration_name}")
        return False

    def _get_kev_data(self) -> ThreadSafeDict:
        """
        Get KEV data from CISA, using cache if available

        :return: Thread-safe dictionary containing KEV data
        :rtype: ThreadSafeDict
        """
        if self._kev_data is None:
            try:
                kev_data = pull_cisa_kev()
                self._kev_data = ThreadSafeDict()
                self._kev_data.update(kev_data)
                logger.debug("Loaded KEV data from CISA")
            except Exception as e:
                logger.warning(f"Failed to load KEV data: {e}")
                self._kev_data = ThreadSafeDict()

        return self._kev_data

    def _should_use_kev(self) -> bool:
        """
        Check if this integration should use KEV dates

        :return: True if KEV should be used for this integration
        :rtype: bool
        """
        issues_config = self.config.get("issues", {})
        integration_config = issues_config.get(self.integration_name, {})
        return integration_config.get("useKev", True)  # Default to True if not specified

    def _get_kev_due_date(self, cve: str) -> Optional[str]:
        """
        Get the KEV due date for a specific CVE

        :param str cve: The CVE identifier
        :return: KEV due date string if found, None otherwise
        :rtype: Optional[str]
        """
        if not self._should_use_kev() or not cve:
            return None

        kev_data = self._get_kev_data()

        # Find the KEV entry for this CVE
        kev_entry = next(
            (entry for entry in kev_data.get("vulnerabilities", []) if entry.get("cveID", "").upper() == cve.upper()),
            None,
        )

        if kev_entry:
            kev_due_date = kev_entry.get("dueDate")
            if kev_due_date:
                logger.debug(f"Found KEV due date for {cve}: {kev_due_date}")
                return kev_due_date

        return None

    def calculate_due_date(
        self,
        severity: Union[regscale_models.IssueSeverity, str],
        created_date: str,
        cve: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        Calculate the due date for an issue based on severity, KEV status, and integration config

        :param Union[regscale_models.IssueSeverity, str] severity: The severity of the issue
        :param str created_date: The creation date of the issue
        :param Optional[str] cve: The CVE identifier (if applicable)
        :param Optional[str] title: The title of the issue (for additional context)
        :return: The calculated due date string
        :rtype: str
        """
        # First, check if this CVE has a KEV due date
        if cve:
            kev_due_date = self._get_kev_due_date(cve)
            if kev_due_date:
                # Parse the KEV due date and created date
                try:
                    from dateutil.parser import parse as date_parse

                    kev_date = date_parse(kev_due_date).date()
                    created_dt = date_parse(created_date).date()

                    # If KEV due date is after creation date, use KEV date but ensure it's not in the past
                    # If KEV due date is before creation date, add the difference to creation date
                    if kev_date >= created_dt:
                        # Ensure KEV due date is not in the past
                        kev_due_validated = self._ensure_future_due_date(
                            kev_due_date, 30
                        )  # Use 30 days as fallback for KEV
                        logger.debug(f"Using KEV due date {kev_due_validated} for CVE {cve}")
                        return kev_due_validated
                    else:
                        # KEV date has passed, calculate new due date from creation
                        days_diff = (created_dt - kev_date).days
                        # Give at least 30 days from creation for critical KEV items
                        adjusted_days = max(30, days_diff)
                        calculated_due_date_obj = get_day_increment(start=created_date, days=adjusted_days)
                        calculated_due_date = datetime.combine(calculated_due_date_obj, datetime.min.time()).strftime(
                            DATETIME_FORMAT
                        )
                        # Ensure the adjusted due date is not in the past
                        due_date = self._ensure_future_due_date(calculated_due_date, adjusted_days)
                        logger.debug(f"KEV date passed, using adjusted due date {due_date} for CVE {cve}")
                        return due_date

                except Exception as e:
                    logger.warning(f"Failed to parse KEV due date {kev_due_date}: {e}")

        # Fall back to severity-based timeline from integration config
        days = self.integration_timelines.get(severity, self.default_timelines[severity])
        calculated_due_date_obj = get_day_increment(start=created_date, days=days)
        calculated_due_date = datetime.combine(calculated_due_date_obj, datetime.min.time()).strftime(DATETIME_FORMAT)

        # Ensure due date is never in the past (allow yesterday for timezone differences)
        due_date = self._ensure_future_due_date(calculated_due_date, days)

        logger.debug(
            f"Using {self.integration_name} timeline: {severity.name if isinstance(severity, regscale_models.IssueSeverity) else severity} = {days} days, due date = {due_date}"
        )

        return due_date

    def _ensure_future_due_date(self, calculated_due_date: str, original_days: int) -> str:
        """
        Ensure the due date is not in the past. If it is, set it to today + original timeline days.
        Behavior is controlled by the noPastDueDates configuration setting.

        :param str calculated_due_date: The originally calculated due date
        :param int original_days: The original number of days for this severity
        :return: A due date that respects the noPastDueDates setting
        :rtype: str
        """
        # If noPastDueDates is disabled, return the original date without validation
        if not self.no_past_due_dates:
            logger.debug(
                f"noPastDueDates=False for {self.integration_name}, returning original due date: {calculated_due_date}"
            )
            return calculated_due_date

        from dateutil.parser import parse as date_parse
        from datetime import date

        try:
            calculated_date = date_parse(calculated_due_date).date()
            today = date.today()

            # Use > instead of >= to ensure due dates set to "today" are moved to tomorrow
            # This prevents API validation errors when the time component (00:00:00) has already passed
            if calculated_date > today:
                return calculated_due_date
            else:
                # Due date is in the past or today, calculate new due date from today
                # Use minimum 1 day to ensure it's always in the future
                safe_days = max(1, original_days)
                new_due_date_obj = get_day_increment(start=today, days=safe_days)
                new_due_date = datetime.combine(new_due_date_obj, datetime.min.time()).strftime(DATETIME_FORMAT)
                logger.debug(
                    f"Due date {calculated_due_date} was in the past or today for {self.integration_name}. "
                    f"Adjusted to {new_due_date} ({safe_days} days from today)."
                )
                return new_due_date

        except Exception as e:
            logger.warning(f"Failed to validate due date {calculated_due_date}: {e}")
            # If we can't parse the date, return a safe fallback only if noPastDueDates is enabled
            if self.no_past_due_dates:
                safe_days = max(1, original_days)
                fallback_due_date_obj = get_day_increment(start=date.today(), days=safe_days)
                return datetime.combine(fallback_due_date_obj, datetime.min.time()).strftime(DATETIME_FORMAT)
            else:
                return calculated_due_date

    def get_integration_config(self) -> Dict[str, Any]:
        """
        Get the full integration configuration from init.yaml

        :return: Integration configuration dictionary
        :rtype: Dict[str, Any]
        """
        issues_config = self.config.get("issues", {})
        return issues_config.get(self.integration_name, {})

    def get_timeline_info(self) -> Dict[str, Any]:
        """
        Get information about current timeline configuration

        :return: Dictionary with timeline information
        :rtype: Dict[str, Any]
        """
        return {
            "integration_name": self.integration_name,
            "use_kev": self._should_use_kev(),
            "no_past_due_dates": self.no_past_due_dates,
            "timelines": {severity.name: days for severity, days in self.integration_timelines.items()},
            "config_source": "init.yaml",
        }
