# flake8: noqa E501
# pylint: disable=line-too-long

"""Assets connector commands for the RegScale CLI"""

import click
from regscale.models import regscale_ssp_id


@click.group()
def assets() -> None:
    """Assets connector commands for the RegScale CLI"""
    pass


@assets.command(name="build-query")
@click.option(
    "--provider",
    required=False,
    help="Provider ID (e.g., assets_armis_centrix). If not specified, starts interactive mode.",
)
@click.option("--validate", help="Validate a filter string against provider capabilities")
@click.option("--list-fields", is_flag=True, default=False, help="List all available fields for the provider")
def build_query(provider, validate, list_fields):
    """
    Build and validate filter queries for Assets connectors.

    Examples:
        # Build a filter query
        regscale assets build-query

        # List all fields for a specific provider
        regscale assets build-query --provider assets_armis_centrix --list-fields

        # Validate a filter string
        regscale assets build-query --provider assets_armis_centrix --validate "device.ip[eq]192.168.1.1"
    """
    from regscale.integrations.commercial.synqly.query_builder import handle_build_query

    handle_build_query("assets", provider, validate, list_fields)


@assets.command(name="sync_armis_centrix")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_armis_centrix(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Armis Centrix to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_armis_centrix = Assets("armis_centrix")
    assets_armis_centrix.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_axonius")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_axonius(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Axonius to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_axonius = Assets("axonius")
    assets_axonius.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_claroty_xdome")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_claroty_xdome(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Claroty Xdome to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_claroty_xdome = Assets("claroty_xdome")
    assets_claroty_xdome.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_crowdstrike")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
@click.option(
    "--url",
    type=click.STRING,
    help="Base URL for the CrowdStrike Falcon Spotlight API.",
    required=False,
)
def sync_crowdstrike(regscale_ssp_id: int, filter: str, url: str) -> None:
    """Sync Assets from Crowdstrike to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_crowdstrike = Assets("crowdstrike")
    assets_crowdstrike.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [], url=url)


@assets.command(name="sync_ivanti_neurons")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_ivanti_neurons(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Ivanti Neurons to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_ivanti_neurons = Assets("ivanti_neurons")
    assets_ivanti_neurons.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_nozomi_vantage")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_nozomi_vantage(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Nozomi Vantage to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_nozomi_vantage = Assets("nozomi_vantage")
    assets_nozomi_vantage.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_qualys_cloud")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_qualys_cloud(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Qualys Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_qualys_cloud = Assets("qualys_cloud")
    assets_qualys_cloud.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_servicenow")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_servicenow(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Servicenow to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_servicenow = Assets("servicenow")
    assets_servicenow.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_sevco")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_sevco(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Sevco to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_sevco = Assets("sevco")
    assets_sevco.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


@assets.command(name="sync_tanium_cloud")
@regscale_ssp_id()
@click.option(
    "--filter",
    help='STRING: Apply filters to the query. Can be a single filter "field[operator]value" or semicolon-separated filters "field1[op]value1;field2[op]value2"',
    required=False,
    type=str,
    default=None,
)
def sync_tanium_cloud(regscale_ssp_id: int, filter: str) -> None:
    """Sync Assets from Tanium Cloud to RegScale."""
    from regscale.models.integration_models.synqly_models.connectors import Assets

    assets_tanium_cloud = Assets("tanium_cloud")
    assets_tanium_cloud.run_sync(regscale_ssp_id=regscale_ssp_id, filter=filter.split(";") if filter else [])


# pylint: enable=line-too-long
