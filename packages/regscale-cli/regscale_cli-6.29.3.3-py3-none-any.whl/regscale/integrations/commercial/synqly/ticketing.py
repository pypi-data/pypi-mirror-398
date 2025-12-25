# flake8: noqa E501
# pylint: disable=line-too-long

"""Ticketing connector commands for the RegScale CLI"""

import click
from regscale.models import regscale_id, regscale_module


@click.group()
def ticketing() -> None:
    """Ticketing connector commands for the RegScale CLI"""
    pass


@ticketing.command(name="sync_autotask")
@regscale_id()
@regscale_module()
@click.option(
    "--default_issue_type",
    type=click.INT,
    help="Default Issue Type (Ticket Category) for the integration. If provided, the issue_type field becomes optional in ticket creation requests. In Autotask, this corresponds to the Ticket Category ID.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.INT,
    help="Default Project (Company ID) for the integration. If provided, the project field becomes optional in ticket creation requests. In Autotask, this corresponds to the Company ID associated with tickets.",
    required=False,
)
def sync_autotask(regscale_id: int, regscale_module: str, default_issue_type: int, default_project: int) -> None:
    """Sync Ticketing data between Autotask and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_autotask = Ticketing("autotask")
    ticketing_autotask.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        default_issue_type=default_issue_type,
        default_project=default_project,
    )


@ticketing.command(name="sync_freshdesk")
@regscale_id()
@regscale_module()
@click.option(
    "--name",
    type=click.STRING,
    help="freshdesk name",
    required=True,
    prompt="freshdesk name",
)
@click.option(
    "--subject",
    type=click.STRING,
    help="freshdesk subject",
    required=True,
    prompt="freshdesk subject",
)
@click.option(
    "--default_contact",
    type=click.STRING,
    help="Default contact email for ticket creation. If provided, the contact field becomes optional in ticket creation requests. If not provided, the contact field is required.",
    required=False,
)
@click.option(
    "--default_type",
    type=click.STRING,
    help='Default issue type for ticket creation (e.g., "Incident", "Problem", "Question"). If provided, the type field becomes optional. If not provided, the type field is required.',
    required=False,
)
def sync_freshdesk(
    regscale_id: int, regscale_module: str, name: str, subject: str, default_contact: str, default_type: str
) -> None:
    """Sync Ticketing data between Freshdesk and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_freshdesk = Ticketing("freshdesk")
    ticketing_freshdesk.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        name=name,
        subject=subject,
        default_contact=default_contact,
        default_type=default_type,
    )


@ticketing.command(name="sync_ivanti")
@regscale_id()
@regscale_module()
@click.option(
    "--name",
    type=click.STRING,
    help="ivanti name",
    required=True,
    prompt="ivanti name",
)
@click.option(
    "--sync_attachments",
    type=click.BOOL,
    help="Whether to sync attachments between Ivanti and RegScale",
    required=False,
    default=True,
)
def sync_ivanti(regscale_id: int, regscale_module: str, name: str, sync_attachments: bool) -> None:
    """Sync Ticketing data between Ivanti and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_ivanti = Ticketing("ivanti")
    ticketing_ivanti.run_sync(
        regscale_id=regscale_id, regscale_module=regscale_module, name=name, sync_attachments=sync_attachments
    )


@ticketing.command(name="sync_jira")
@regscale_id()
@regscale_module()
@click.option(
    "--project",
    type=click.STRING,
    help="jira project",
    required=True,
    prompt="jira project",
)
@click.option(
    "--default_issue_type",
    type=click.STRING,
    help="Default Issue Type for the integration. If provided, the issue_type field becomes optional in ticket creation requests.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.STRING,
    help="Default Project for the integration.",
    required=False,
)
@click.option(
    "--sync_attachments",
    type=click.BOOL,
    help="Whether to sync attachments between Jira and RegScale",
    required=False,
    default=True,
)
def sync_jira(
    regscale_id: int,
    regscale_module: str,
    project: str,
    default_issue_type: str,
    default_project: str,
    sync_attachments: bool,
) -> None:
    """Sync Ticketing data between Jira and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_jira = Ticketing("jira")
    ticketing_jira.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        project=project,
        default_issue_type=default_issue_type,
        default_project=default_project,
        sync_attachments=sync_attachments,
    )


@ticketing.command(name="sync_jira_service_management")
@regscale_id()
@regscale_module()
@click.option(
    "--project",
    type=click.STRING,
    help="jira_service_management project",
    required=True,
    prompt="jira_service_management project",
)
@click.option(
    "--default_issue_type",
    type=click.STRING,
    help="Default issue type when creating tickets.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.STRING,
    help="Default project when listing, creating, or editing tickets.",
    required=False,
)
@click.option(
    "--sync_attachments",
    type=click.BOOL,
    help="Whether to sync attachments between Jira Service Management and RegScale",
    required=False,
    default=True,
)
def sync_jira_service_management(
    regscale_id: int,
    regscale_module: str,
    project: str,
    default_issue_type: str,
    default_project: str,
    sync_attachments: bool,
) -> None:
    """Sync Ticketing data between Jira Service Management and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_jira_service_management = Ticketing("jira_service_management")
    ticketing_jira_service_management.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        project=project,
        default_issue_type=default_issue_type,
        default_project=default_project,
        sync_attachments=sync_attachments,
    )


@ticketing.command(name="sync_pagerduty")
@regscale_id()
@regscale_module()
@click.option(
    "--name",
    type=click.STRING,
    help="pagerduty name",
    required=True,
    prompt="pagerduty name",
)
@click.option(
    "--default_creator",
    type=click.STRING,
    help="Default email address for the creator field. If provided, the creator field becomes optional for ticket and comment creation. If not provided, the creator field is required.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.STRING,
    help="Default PagerDuty service ID for ticket creation. If provided, the project field becomes optional in ticket creation requests. If not provided, the project field is required.",
    required=False,
)
def sync_pagerduty(
    regscale_id: int, regscale_module: str, name: str, default_creator: str, default_project: str
) -> None:
    """Sync Ticketing data between Pagerduty and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_pagerduty = Ticketing("pagerduty")
    ticketing_pagerduty.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        name=name,
        default_creator=default_creator,
        default_project=default_project,
    )


@ticketing.command(name="sync_servicenow")
@regscale_id()
@regscale_module()
@click.option(
    "--default_issue_type",
    type=click.STRING,
    help="Default Issue Type for the integration. If provided, the issue_type field becomes optional in ticket creation requests.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.STRING,
    help="Default Project for the integration. This maps to the custom table for tickets. This table should be derived from Incident table. Defaults to the incident table if not specified.",
    required=False,
)
def sync_servicenow(regscale_id: int, regscale_module: str, default_issue_type: str, default_project: str) -> None:
    """Sync Ticketing data between Servicenow and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_servicenow = Ticketing("servicenow")
    ticketing_servicenow.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        default_issue_type=default_issue_type,
        default_project=default_project,
    )


@ticketing.command(name="sync_servicenow_sir")
@regscale_id()
@regscale_module()
@click.option(
    "--default_creator",
    type=click.STRING,
    help="Default Creator (email) for the integration. If provided, the creator field becomes optional in ticket creation requests.",
    required=False,
)
@click.option(
    "--default_issue_type",
    type=click.STRING,
    help="Default Issue Type for the integration. If provided, the issue_type field becomes optional in ticket creation requests.",
    required=False,
)
@click.option(
    "--default_project",
    type=click.STRING,
    help="Default Project for the integration. This maps to the custom table for tickets. This table should be derived from Security Incident table. Defaults to the security incident table if not specified.",
    required=False,
)
def sync_servicenow_sir(
    regscale_id: int, regscale_module: str, default_creator: str, default_issue_type: str, default_project: str
) -> None:
    """Sync Ticketing data between Servicenow Sir and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_servicenow_sir = Ticketing("servicenow_sir")
    ticketing_servicenow_sir.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        default_creator=default_creator,
        default_issue_type=default_issue_type,
        default_project=default_project,
    )


@ticketing.command(name="sync_torq")
@regscale_id()
@regscale_module()
@click.option(
    "--name",
    type=click.STRING,
    help="torq name",
    required=True,
    prompt="torq name",
)
@click.option(
    "--default_creator",
    type=click.STRING,
    help="Default Creator (email) for the integration. If provided, the creator field becomes optional in ticket creation requests.",
    required=False,
)
@click.option(
    "--default_issue_type",
    type=click.STRING,
    help="Default Issue Type for the integration. If provided, the issue_type field becomes optional in ticket creation requests.",
    required=False,
)
def sync_torq(regscale_id: int, regscale_module: str, name: str, default_creator: str, default_issue_type: str) -> None:
    """Sync Ticketing data between Torq and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_torq = Ticketing("torq")
    ticketing_torq.run_sync(
        regscale_id=regscale_id,
        regscale_module=regscale_module,
        name=name,
        default_creator=default_creator,
        default_issue_type=default_issue_type,
    )


@ticketing.command(name="sync_zendesk")
@regscale_id()
@regscale_module()
@click.option(
    "--name",
    type=click.STRING,
    help="zendesk name",
    required=True,
    prompt="zendesk name",
)
@click.option(
    "--subject",
    type=click.STRING,
    help="zendesk subject",
    required=True,
    prompt="zendesk subject",
)
def sync_zendesk(regscale_id: int, regscale_module: str, name: str, subject: str) -> None:
    """Sync Ticketing data between Zendesk and RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Ticketing

    ticketing_zendesk = Ticketing("zendesk")
    ticketing_zendesk.run_sync(regscale_id=regscale_id, regscale_module=regscale_module, name=name, subject=subject)


# pylint: enable=line-too-long
