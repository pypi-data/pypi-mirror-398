#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Milestone Manager for Issue Tracking

Handles creation of milestones for issues based on status transitions (created, reopened, closed).
Also handles backfilling of missing milestones for existing issues.
"""
import logging
from typing import TYPE_CHECKING, List, Optional

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.variables import ScannerVariables
from regscale.models import regscale_models

if TYPE_CHECKING:
    from regscale.integrations.scanner_integration import IntegrationFinding

logger = logging.getLogger("regscale")


class MilestoneManager:
    """
    Manages milestone creation for issues based on status transitions.

    Milestones are created when:
    - A new issue is created
    - An existing issue is reopened (Closed -> Open)
    - An existing issue is closed (Open -> Closed)
    """

    def __init__(self, integration_title: str, assessor_id: str, scan_date: str):
        """
        Initialize the milestone manager.

        :param str integration_title: Name of the integration (used in milestone titles)
        :param str assessor_id: ID of the assessor/responsible person for milestones
        :param str scan_date: Date of the scan (used for new issue milestones)
        """
        self.integration_title = integration_title
        self.assessor_id = assessor_id
        self.scan_date = scan_date

    def create_milestones_for_issue(
        self,
        issue: regscale_models.Issue,
        finding: Optional["IntegrationFinding"] = None,
        existing_issue: Optional[regscale_models.Issue] = None,
    ) -> None:
        """
        Create appropriate milestones for an issue based on status transitions.

        :param regscale_models.Issue issue: The issue to create milestones for
        :param Optional[IntegrationFinding] finding: The finding data (for logging/context)
        :param Optional[regscale_models.Issue] existing_issue: Previous state of issue for comparison
        """
        if not self._should_create_milestones(issue):
            return

        if self._should_create_reopened_milestone(existing_issue, issue):
            self._create_reopened_milestone(issue, finding)
        elif self._should_create_closed_milestone(existing_issue, issue):
            self._create_closed_milestone(issue, finding)
        elif not existing_issue:
            self._create_new_issue_milestone(issue, finding)
        else:
            logger.debug(
                "No milestone created for issue %s (no status transition detected)",
                issue.id,
            )

    def _should_create_milestones(self, issue: regscale_models.Issue) -> bool:
        """
        Check if milestones should be created for this issue.

        :param regscale_models.Issue issue: The issue to check
        :return: True if milestones should be created
        :rtype: bool
        """
        if not ScannerVariables.useMilestones:
            logger.debug("Milestone creation disabled (useMilestones=False)")
            return False

        if not issue.id:
            logger.debug("Cannot create milestone - issue has no ID")
            return False

        return True

    def _should_create_reopened_milestone(
        self, existing_issue: Optional[regscale_models.Issue], issue: regscale_models.Issue
    ) -> bool:
        """
        Check if a reopened milestone should be created.

        :param Optional[regscale_models.Issue] existing_issue: The existing issue
        :param regscale_models.Issue issue: The current issue
        :return: True if reopened milestone should be created
        :rtype: bool
        """
        return (
            existing_issue is not None
            and existing_issue.status == regscale_models.IssueStatus.Closed
            and issue.status == regscale_models.IssueStatus.Open
        )

    def _should_create_closed_milestone(
        self, existing_issue: Optional[regscale_models.Issue], issue: regscale_models.Issue
    ) -> bool:
        """
        Check if a closed milestone should be created.

        :param Optional[regscale_models.Issue] existing_issue: The existing issue
        :param regscale_models.Issue issue: The current issue
        :return: True if closed milestone should be created
        :rtype: bool
        """
        return (
            existing_issue is not None
            and existing_issue.status == regscale_models.IssueStatus.Open
            and issue.status == regscale_models.IssueStatus.Closed
        )

    def _create_reopened_milestone(
        self,
        issue: regscale_models.Issue,
        finding: Optional["IntegrationFinding"] = None,
    ) -> None:
        """
        Create a milestone for a reopened issue.

        :param regscale_models.Issue issue: The issue being reopened
        :param Optional[IntegrationFinding] finding: The finding data (for logging)
        """
        milestone_date = get_current_datetime()
        self._create_milestone(
            issue=issue,
            title=f"Issue reopened from {self.integration_title} scan",
            milestone_date=milestone_date,
            milestone_type="reopened",
            finding=finding,
        )

    def _create_closed_milestone(
        self,
        issue: regscale_models.Issue,
        finding: Optional["IntegrationFinding"] = None,
    ) -> None:
        """
        Create a milestone for a closed issue.

        :param regscale_models.Issue issue: The issue being closed
        :param Optional[IntegrationFinding] finding: The finding data (for logging)
        """
        milestone_date = issue.dateCompleted or get_current_datetime()
        self._create_milestone(
            issue=issue,
            title=f"Issue closed from {self.integration_title} scan",
            milestone_date=milestone_date,
            milestone_type="closed",
            finding=finding,
        )

    def _create_new_issue_milestone(
        self,
        issue: regscale_models.Issue,
        finding: Optional["IntegrationFinding"] = None,
    ) -> None:
        """
        Create a milestone for a newly created issue.

        :param regscale_models.Issue issue: The newly created issue
        :param Optional[IntegrationFinding] finding: The finding data (for logging)
        """
        self._create_milestone(
            issue=issue,
            title=f"Issue created from {self.integration_title} scan",
            milestone_date=self.scan_date,
            milestone_type="new",
            finding=finding,
        )

    def _create_milestone(
        self,
        issue: regscale_models.Issue,
        title: str,
        milestone_date: str,
        milestone_type: str,
        finding: Optional["IntegrationFinding"] = None,
    ) -> None:
        """
        Create a milestone with error handling.

        :param regscale_models.Issue issue: The issue to create milestone for
        :param str title: Title of the milestone
        :param str milestone_date: Date for the milestone
        :param str milestone_type: Type of milestone (for logging: new, reopened, closed)
        :param Optional[IntegrationFinding] finding: The finding data (for logging)
        """
        try:
            regscale_models.Milestone(
                title=title,
                milestoneDate=milestone_date,
                dateCompleted=get_current_datetime(),
                responsiblePersonId=self.assessor_id,
                parentID=issue.id,
                parentModule="issues",
            ).create_or_update()

            logger.debug(f"Created {milestone_type} milestone for issue {issue.id}")

        except Exception as e:
            logger.warning(f"Failed to create {milestone_type} milestone for issue {issue.id}: {e}")

    def get_existing_milestones(self, issue: regscale_models.Issue) -> List[regscale_models.Milestone]:
        """
        Get all existing milestones for an issue.

        :param regscale_models.Issue issue: The issue to check
        :return: List of existing milestones
        :rtype: List[regscale_models.Milestone]
        """
        if not issue.id:
            return []

        try:
            milestones = regscale_models.Milestone.get_by_parent(parent_id=issue.id, parent_module="issues")
            return milestones if milestones else []
        except Exception as e:
            logger.debug(f"Could not retrieve milestones for issue {issue.id}: {e}")
            return []

    def has_creation_milestone(self, issue: regscale_models.Issue) -> bool:
        """
        Check if an issue has a creation milestone.

        :param regscale_models.Issue issue: The issue to check
        :return: True if creation milestone exists
        :rtype: bool
        """
        milestones = self.get_existing_milestones(issue)

        # Check for creation milestone patterns
        creation_patterns = [
            "Issue created from",
            "created from",
        ]

        for milestone in milestones:
            milestone_title = milestone.title.lower() if milestone.title else ""
            if any(pattern.lower() in milestone_title for pattern in creation_patterns):
                logger.debug(f"Found existing creation milestone for issue {issue.id}: {milestone.title}")
                return True

        return False

    def ensure_creation_milestone_exists(
        self,
        issue: regscale_models.Issue,
        finding: Optional["IntegrationFinding"] = None,
    ) -> None:
        """
        Ensure an issue has a creation milestone, backfilling if necessary.

        This method checks if an issue has a creation milestone. If not, it creates one
        based on the issue's dateCreated field to backfill missing milestones.

        :param regscale_models.Issue issue: The issue to check
        :param Optional[IntegrationFinding] finding: The finding data (for logging)
        """
        if not self._should_create_milestones(issue):
            return

        # Check if creation milestone already exists
        if self.has_creation_milestone(issue):
            logger.debug(f"Issue {issue.id} already has creation milestone, skipping backfill")
            return

        # Backfill missing creation milestone
        logger.debug(f"Backfilling missing creation milestone for issue {issue.id}")

        # Use issue's dateCreated if available, otherwise use scan_date
        milestone_date = issue.dateCreated if issue.dateCreated else self.scan_date

        self._create_milestone(
            issue=issue,
            title=f"Issue created from {self.integration_title} scan",
            milestone_date=milestone_date,
            milestone_type="backfilled",
            finding=finding,
        )
