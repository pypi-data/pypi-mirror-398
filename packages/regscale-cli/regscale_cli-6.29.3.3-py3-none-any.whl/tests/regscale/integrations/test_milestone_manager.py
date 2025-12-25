#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MilestoneManager class."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.milestone_manager import MilestoneManager
from regscale.integrations.scanner_integration import IntegrationFinding
from regscale.models import regscale_models


logger = logging.getLogger("regscale")


@pytest.fixture
def milestone_manager():
    """Create a MilestoneManager instance for testing."""
    return MilestoneManager(
        integration_title="Test Integration",
        assessor_id="test-assessor-id",
        scan_date="2024-01-15T10:00:00Z",
    )


@pytest.fixture
def mock_issue():
    """Create a mock issue for testing."""
    issue = MagicMock(spec=regscale_models.Issue)
    issue.id = 123
    issue.status = regscale_models.IssueStatus.Open
    issue.dateCompleted = "2024-01-15T12:00:00Z"
    return issue


@pytest.fixture
def mock_finding():
    """Create a mock finding for testing."""
    finding = MagicMock(spec=IntegrationFinding)
    finding.external_id = "test-external-id-123"
    return finding


class TestMilestoneManagerInitialization:
    """Test MilestoneManager initialization."""

    def test_initialization(self):
        """Test that MilestoneManager initializes correctly."""
        manager = MilestoneManager(
            integration_title="Test Integration",
            assessor_id="assessor-123",
            scan_date="2024-01-15T10:00:00Z",
        )

        assert manager.integration_title == "Test Integration"
        assert manager.assessor_id == "assessor-123"
        assert manager.scan_date == "2024-01-15T10:00:00Z"


class TestMilestoneShouldCreateChecks:
    """Test the milestone creation decision logic."""

    def test_should_create_milestones_enabled(self, milestone_manager, mock_issue):
        """Test that milestones should be created when enabled and issue has ID."""
        with patch("regscale.integrations.milestone_manager.ScannerVariables") as mock_vars:
            mock_vars.useMilestones = True
            assert milestone_manager._should_create_milestones(mock_issue) is True

    def test_should_not_create_milestones_disabled(self, milestone_manager, mock_issue):
        """Test that milestones should not be created when disabled."""
        with patch("regscale.integrations.milestone_manager.ScannerVariables") as mock_vars:
            mock_vars.useMilestones = False
            assert milestone_manager._should_create_milestones(mock_issue) is False

    def test_should_not_create_milestones_no_id(self, milestone_manager):
        """Test that milestones should not be created when issue has no ID."""
        issue = MagicMock(spec=regscale_models.Issue)
        issue.id = None

        with patch("regscale.integrations.milestone_manager.ScannerVariables") as mock_vars:
            mock_vars.useMilestones = True
            assert milestone_manager._should_create_milestones(issue) is False


class TestMilestoneTransitionDetection:
    """Test detection of status transitions."""

    def test_should_create_reopened_milestone(self, milestone_manager, mock_issue):
        """Test detection of issue reopening (Closed -> Open)."""
        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Closed

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.status = regscale_models.IssueStatus.Open

        assert milestone_manager._should_create_reopened_milestone(existing_issue, current_issue) is True

    def test_should_not_create_reopened_milestone_same_status(self, milestone_manager):
        """Test that reopened milestone is not created when status doesn't change."""
        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Open

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.status = regscale_models.IssueStatus.Open

        assert milestone_manager._should_create_reopened_milestone(existing_issue, current_issue) is False

    def test_should_create_closed_milestone(self, milestone_manager):
        """Test detection of issue closing (Open -> Closed)."""
        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Open

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.status = regscale_models.IssueStatus.Closed

        assert milestone_manager._should_create_closed_milestone(existing_issue, current_issue) is True

    def test_should_not_create_closed_milestone_same_status(self, milestone_manager):
        """Test that closed milestone is not created when status doesn't change."""
        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Closed

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.status = regscale_models.IssueStatus.Closed

        assert milestone_manager._should_create_closed_milestone(existing_issue, current_issue) is False


class TestMilestoneCreation:
    """Test actual milestone creation."""

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_create_new_issue_milestone(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding
    ):
        """Test creation of milestone for new issue."""
        mock_vars.useMilestones = True
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone

        milestone_manager.create_milestones_for_issue(
            issue=mock_issue,
            finding=mock_finding,
            existing_issue=None,
        )

        # Verify Milestone was created with correct parameters
        mock_milestone_class.assert_called_once_with(
            title="Issue created from Test Integration scan",
            milestoneDate=milestone_manager.scan_date,
            responsiblePersonId=milestone_manager.assessor_id,
            parentID=mock_issue.id,
            parentModule="issues",
        )
        mock_milestone.create_or_update.assert_called_once()

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    @patch("regscale.integrations.milestone_manager.get_current_datetime")
    def test_create_reopened_milestone(
        self, mock_datetime, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding
    ):
        """Test creation of milestone for reopened issue."""
        mock_vars.useMilestones = True
        mock_datetime.return_value = "2024-01-15T14:00:00Z"
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone

        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Closed

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.id = 123
        current_issue.status = regscale_models.IssueStatus.Open

        milestone_manager.create_milestones_for_issue(
            issue=current_issue,
            finding=mock_finding,
            existing_issue=existing_issue,
        )

        # Verify Milestone was created with correct parameters
        mock_milestone_class.assert_called_once_with(
            title="Issue reopened from Test Integration scan",
            milestoneDate="2024-01-15T14:00:00Z",
            responsiblePersonId=milestone_manager.assessor_id,
            parentID=current_issue.id,
            parentModule="issues",
        )
        mock_milestone.create_or_update.assert_called_once()

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_create_closed_milestone(self, mock_vars, mock_milestone_class, milestone_manager, mock_finding):
        """Test creation of milestone for closed issue."""
        mock_vars.useMilestones = True
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone

        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Open

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.id = 123
        current_issue.status = regscale_models.IssueStatus.Closed
        current_issue.dateCompleted = "2024-01-15T12:00:00Z"

        milestone_manager.create_milestones_for_issue(
            issue=current_issue,
            finding=mock_finding,
            existing_issue=existing_issue,
        )

        # Verify Milestone was created with correct parameters
        mock_milestone_class.assert_called_once_with(
            title="Issue closed from Test Integration scan",
            milestoneDate=current_issue.dateCompleted,
            responsiblePersonId=milestone_manager.assessor_id,
            parentID=current_issue.id,
            parentModule="issues",
        )
        mock_milestone.create_or_update.assert_called_once()

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_no_milestone_for_existing_open_issue(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding
    ):
        """Test that no milestone is created when existing issue remains open."""
        mock_vars.useMilestones = True

        existing_issue = MagicMock(spec=regscale_models.Issue)
        existing_issue.status = regscale_models.IssueStatus.Open

        current_issue = MagicMock(spec=regscale_models.Issue)
        current_issue.id = 123
        current_issue.status = regscale_models.IssueStatus.Open

        milestone_manager.create_milestones_for_issue(
            issue=current_issue,
            finding=mock_finding,
            existing_issue=existing_issue,
        )

        # Verify no Milestone was created
        mock_milestone_class.assert_not_called()


class TestMilestoneCreationErrors:
    """Test error handling in milestone creation."""

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_milestone_creation_error_handled(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding, caplog
    ):
        """Test that milestone creation errors are handled gracefully."""
        mock_vars.useMilestones = True
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone
        mock_milestone.create_or_update.side_effect = Exception("Database error")

        with caplog.at_level(logging.WARNING):
            milestone_manager.create_milestones_for_issue(
                issue=mock_issue,
                finding=mock_finding,
                existing_issue=None,
            )

        # Verify error was logged
        assert "Failed to create new milestone" in caplog.text
        assert "Database error" in caplog.text


class TestMilestoneBackfilling:
    """Test milestone backfilling functionality."""

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    def test_get_existing_milestones(self, mock_milestone_class, milestone_manager, mock_issue):
        """Test retrieval of existing milestones for an issue."""
        # Mock milestones
        mock_milestone1 = MagicMock()
        mock_milestone1.title = "Issue created from Test Integration scan"
        mock_milestone2 = MagicMock()
        mock_milestone2.title = "Some other milestone"

        mock_milestone_class.get_by_parent.return_value = [mock_milestone1, mock_milestone2]

        milestones = milestone_manager.get_existing_milestones(mock_issue)

        assert len(milestones) == 2
        mock_milestone_class.get_by_parent.assert_called_once_with(parent_id=mock_issue.id, parent_module="issues")

    def test_get_existing_milestones_no_id(self, milestone_manager):
        """Test that get_existing_milestones returns empty list when issue has no ID."""
        issue = MagicMock(spec=regscale_models.Issue)
        issue.id = None

        milestones = milestone_manager.get_existing_milestones(issue)

        assert milestones == []

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    def test_has_creation_milestone_true(self, mock_milestone_class, milestone_manager, mock_issue):
        """Test detection of existing creation milestone."""
        mock_milestone = MagicMock()
        mock_milestone.title = "Issue created from Test Integration scan"

        mock_milestone_class.get_by_parent.return_value = [mock_milestone]

        assert milestone_manager.has_creation_milestone(mock_issue) is True

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    def test_has_creation_milestone_false(self, mock_milestone_class, milestone_manager, mock_issue):
        """Test detection when no creation milestone exists."""
        mock_milestone = MagicMock()
        mock_milestone.title = "Issue closed from Test Integration scan"

        mock_milestone_class.get_by_parent.return_value = [mock_milestone]

        assert milestone_manager.has_creation_milestone(mock_issue) is False

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    def test_has_creation_milestone_empty(self, mock_milestone_class, milestone_manager, mock_issue):
        """Test detection when no milestones exist."""
        mock_milestone_class.get_by_parent.return_value = []

        assert milestone_manager.has_creation_milestone(mock_issue) is False

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_ensure_creation_milestone_exists_backfill(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding, caplog
    ):
        """Test backfilling of missing creation milestone."""
        mock_vars.useMilestones = True

        # Mock no existing creation milestone
        mock_milestone_class.get_by_parent.return_value = []

        # Mock Milestone creation
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone

        # Set issue dateCreated
        mock_issue.dateCreated = "2024-01-10T10:00:00Z"

        with caplog.at_level(logging.INFO):
            milestone_manager.ensure_creation_milestone_exists(issue=mock_issue, finding=mock_finding)

        # Verify milestone was created with issue's dateCreated
        mock_milestone_class.assert_called_once_with(
            title="Issue created from Test Integration scan",
            milestoneDate=mock_issue.dateCreated,
            responsiblePersonId=milestone_manager.assessor_id,
            parentID=mock_issue.id,
            parentModule="issues",
        )
        mock_milestone.create_or_update.assert_called_once()

        assert "Backfilling missing creation milestone" in caplog.text

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_ensure_creation_milestone_exists_no_backfill_exists(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding
    ):
        """Test that no milestone is created when one already exists."""
        mock_vars.useMilestones = True

        # Mock has_creation_milestone to return True (issue already has creation milestone)
        with patch.object(milestone_manager, "has_creation_milestone", return_value=True):
            milestone_manager.ensure_creation_milestone_exists(issue=mock_issue, finding=mock_finding)

        # Verify no new milestone was created (constructor not called)
        mock_milestone_class.assert_not_called()

    @patch("regscale.integrations.milestone_manager.regscale_models.Milestone")
    @patch("regscale.integrations.milestone_manager.ScannerVariables")
    def test_ensure_creation_milestone_exists_uses_scan_date_fallback(
        self, mock_vars, mock_milestone_class, milestone_manager, mock_issue, mock_finding
    ):
        """Test that scan_date is used when issue.dateCreated is None."""
        mock_vars.useMilestones = True

        # Mock no existing creation milestone
        mock_milestone_class.get_by_parent.return_value = []

        # Mock Milestone creation
        mock_milestone = MagicMock()
        mock_milestone_class.return_value = mock_milestone

        # Set issue dateCreated to None
        mock_issue.dateCreated = None

        milestone_manager.ensure_creation_milestone_exists(issue=mock_issue, finding=mock_finding)

        # Verify milestone was created with scan_date as fallback
        mock_milestone_class.assert_called_once_with(
            title="Issue created from Test Integration scan",
            milestoneDate=milestone_manager.scan_date,
            responsiblePersonId=milestone_manager.assessor_id,
            parentID=mock_issue.id,
            parentModule="issues",
        )
        mock_milestone.create_or_update.assert_called_once()
