#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
from typing import List, Optional
from rich.progress import track
import click
from rich.console import Console
from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.core.utils.date import format_to_regscale_iso, date_obj
from regscale.core.app.utils.app_utils import error_and_exit, filter_list
from regscale.models.regscale_models import (
    Organization,
    SecurityPlan,
    User,
)
from regscale.models.regscale_models.module import Module
from regscale.models.regscale_models.form_field_value import FormFieldValue
from regscale.integrations.public.csam.csam_poam import import_csam_poams
from regscale.integrations.public.csam.csam_continuity import import_csam_contingency
from regscale.integrations.public.csam.csam_artifacts import import_csam_artifacts
from regscale.integrations.public.csam.csam_additional_status import import_csam_additional_status
from regscale.integrations.public.csam.csam_pocs import import_csam_pocs
from regscale.integrations.public.csam.csam_agency_defined import update_ssp_agency_details
from regscale.integrations.public.csam.csam_controls import (
    import_csam_controls,
    set_inheritable,
    import_csam_inheritance,
)
from regscale.integrations.public.csam.csam_common import (
    retrieve_ssps_custom_form_map,
    retrieve_custom_form_ssps_map,
    retrieve_from_csam,
    build_form_values,
    fix_form_field_value,
    test_csam_connection,
    get_sync_records,
    build_form_values,
    CSAM_FIELD_NAME,
    FISMA_FIELD_NAME,
    SSP_BASIC_TAB,
)


logger = logging.getLogger("regscale")
console = Console()

####################################################################################################
#
# IMPORT SSP / POAM FROM DoJ's CSAM GRC
# CSAM API Docs: https://csam.dhs.gov/CSAM/api/docs/index.html (required PIV)
#
####################################################################################################


SSP_SYSTEM_TAB = "System Information"
SSP_FINANCIAL_TAB = "Financial Info"
SSP_CONTINGENCY_TAB = "Continuity and Incident Response"
SSP_PRIVACY_TAB = "Privacy-Details"

CUSTOM_FIELDS_BASIC_LIST = [
    "acronym",
    "Classification",
    "FISMA Reportable",
    "Contractor System",
    "Critical Infrastructure",
    "Mission Essential",
    CSAM_FIELD_NAME,
    FISMA_FIELD_NAME,
]


@click.group()
def csam():
    """Integrate CSAM."""


@csam.command(name="import_ssp")
def import_ssp():
    """
    Import SSP from CSAM
    Into RegScale
    """

    import_csam_ssp()


@csam.command(name="import_poam")
def import_poam():
    """
    Import POAMS from CSAM
    Into RegScale
    """

    import_csam_poams()


@csam.command(name="test_csam")
def test_csam():
    """
    Test connection to CSAM
    """

    test_csam_connection()


def import_csam_ssp():
    """
    Import SSPs from CSAM
    Into RegScale
    According to a filter in init.yaml
    """

    logger.info("Gathering reference info...")
    # Check Custom Fields exist
    custom_fields_basic_map = FormFieldValue.check_custom_fields(
        CUSTOM_FIELDS_BASIC_LIST, "securityplans", SSP_BASIC_TAB
    )

    # Get a map of existing custom forms
    ssp_map = retrieve_custom_form_ssps_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    # Get a list of orgs and create a map to id
    orgs = Organization.get_list()
    org_map = {org.name: org.id for org in orgs}

    # Grab the data from CSAM
    app = Application()
    csam_filter = app.config.get("csamFilter", None)

    logger.info("Retrieving systems from CSAM...")
    results = retrieve_from_csam(
        csam_endpoint="/CSAM/api/v1/systems",
    )

    if not results:
        error_and_exit("Failure to retrieve plans from CSAM")
    else:
        logger.info("Retrieved plans from CSAM, parsing results...")

    results = filter_list(results, csam_filter)
    if not results:
        error_and_exit(
            "No results match filter in CSAM. \
                       Please check your CSAM configuration."
        )

    # Get any new csam records
    new_csam_ids, missing_csam_ids = get_sync_records(results=results, ssp_map=ssp_map)

    logger.info(f"Importing {len(new_csam_ids)} new systems... ")

    # Create new SSPs
    new_ssps = create_ssps(results=results, csam_ids=new_csam_ids)

    # Add the new ssps to the map
    for ssp in new_ssps:
        ssp_map[ssp.otherIdentifier] = ssp.id

    logger.info("Updaing existing systems... ")
    # Import front matter
    updated_ssps = []
    updated_ssps = save_ssp_front_matter(
        results=results,
        ssp_map=ssp_map,
        custom_fields_basic_map=custom_fields_basic_map,
        org_map=org_map,
    )

    # Import system detail
    update_ssp_agency_details(updated_ssps)

    # Import the authorization process and status
    import_csam_authorization(updated_ssps)

    # Import the Privacy date
    import_csam_privacy_info(updated_ssps)

    # Import the Contingency & IR data
    import_csam_contingency(updated_ssps)

    # Import the POCs
    import_csam_pocs(updated_ssps)

    # Import the additional Status
    import_csam_additional_status(updated_ssps)

    # Import the controls (only if new)
    if len(new_ssps) > 0:
        import_csam_controls(import_ids=[ssp.id for ssp in new_ssps])

    # Set inheritance if system type = program
    for result in results:
        if result.get("systemType") == "Program":
            # Get the RegScale SSP Id
            program_id = ssp_map.get(str(result["id"]))
            if not program_id:
                logger.error(
                    f"Could not find RegScale SSP for CSAM id: {result['externalId']}. \
                    Please create or import the Security Plan prior to importing inheritance."
                )
                continue

            # Set the inheritable flag
            set_inheritable(regscale_id=program_id)

    # Import the Inheritance
    if len(new_ssps) > 0:
        import_csam_inheritance(import_ids=[ssp.id for ssp in new_ssps])

    # Report out excess csam_ids
    logger.info(f"Imported or Updated {len(updated_ssps)} plans from CSAM")
    logger.info(f"The following SSP ids' CSAM Ids were not in the CSAM filtered results: {missing_csam_ids}")


def _process_sorn_status(system_id: int, privacy_map: dict, ssp: int) -> list:
    """
    Process SORN status for a given system

    :param int system_id: CSAM system ID
    :param dict privacy_map: Map of custom fields
    :param int ssp: RegScale SSP ID
    :return: List of field values for SORN
    :return_type: list
    """
    result = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/sorn")

    if len(result) == 0:
        logger.debug(f"Could not retrieve SORN for CSAM ID {system_id}. RegScale SSP id: {ssp}")
        return []

    sorn_date = 0
    sorn_id = ""
    for sorn_status in result:
        if date_obj(sorn_status.get("publishedDate")) > date_obj(sorn_date):
            sorn_date = sorn_status.get("publishedDate")
            sorn_id = sorn_status.get("systemOfRecordsNoticeId").strip()

    return [
        {
            "record_id": ssp,
            "record_module": "securityplans",
            "form_field_id": privacy_map.get("SORN Id"),
            "field_value": sorn_id,
        },
        {
            "record_id": ssp,
            "record_module": "securityplans",
            "form_field_id": privacy_map.get("SORN Date"),
            "field_value": sorn_date,
        },
    ]


def _process_privacy_for_ssp(ssp: int, system_id: int, privacy_map: dict, privacy_custom_fields: dict) -> list:
    """
    Process privacy information for a single SSP

    :param int ssp: RegScale SSP ID
    :param int system_id: CSAM system ID
    :param dict privacy_map: Map of custom fields
    :param dict privacy_custom_fields: Custom fields mapping
    :return: List of field values
    :return_type: list
    """
    result = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/privacy")
    if len(result) == 0:
        logger.error(f"Could not retrieve privacy for CSAM ID {system_id}. RegScale SSP id: {ssp}")
        return []

    field_values = build_form_values(
        ssp=ssp, result=result, custom_map=privacy_map, custom_fields=privacy_custom_fields
    )

    # Get SORN Status
    sorn_values = _process_sorn_status(system_id=system_id, privacy_map=privacy_map, ssp=ssp)
    field_values.extend(sorn_values)

    return field_values


def import_csam_privacy_info(import_ids: Optional[List[int]] = None):
    """
    Import the Privacy Info from CSAM
    Into RegScale
    """

    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    if len(ssps) == 0:
        return

    # Get Privacy Custom Fields
    privacy_custom_fields = {
        "PTA Date": "privacyThresholdAnalysisDateCompleted",
        "PII": "personallyIdentifiableInformation",
        "PIA Date": "privacyImpactAssessmentDateCompleted",
        "PIA Status": "privacyImpactAssessmentStatus",
        "SORN Date": "publishedDate",
        "SORN Status": "systemOfRecordsNoticeStatus",
        "SORN Id": "systemOfRecordsNoticdId",
    }

    privacy_map = FormFieldValue.check_custom_fields(
        list(privacy_custom_fields.keys()), "securityplans", "Privacy Info"
    )
    field_values = []
    updated_ssps = []

    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP privacy...",
    ):
        ssp = ssps[index]
        system_id = ssp_map.get(ssp)
        if not system_id:
            logger.error(f"Could not find CSAM ID for SSP id: {ssp}")
            continue

        updated_ssps.append(ssp)
        ssp_field_values = _process_privacy_for_ssp(ssp, system_id, privacy_map, privacy_custom_fields)
        field_values.extend(ssp_field_values)

    # Save the Custom Fields
    if len(field_values) > 0:
        field_values = fix_form_field_value(field_values)
        FormFieldValue.save_custom_fields(field_values)

        logger.info(f"Updated {len(updated_ssps)} Security Plans with privacy data")


def import_csam_authorization(import_ids: Optional[List[int]] = None):
    """
    Update the Authorization of the SSPs
    This requires a call to the /system/{id}/securityauthorization
    endpoint

    :param list import_ids: Filtered list of SSPs
    :return: None
    """
    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    # Get Authorization Custom Fields
    authorization_custom_fields = {
        "Authorization Process": "authorizationProcess",
        "ATO Date": "lastAuthorizationDate",
        "ATO Status": "authorizationStatus",
        "Initial Authorization Date": "initialAuthorizationDate",
        "Authorization Next Due Date": "authorizationNextDueDate",
    }

    authorization_map = FormFieldValue.check_custom_fields(
        list(authorization_custom_fields.keys()), "securityplans", "Authorization"
    )

    updated_ssps = []
    field_values = []
    if len(ssps) == 0:
        return
    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP authorization...",
    ):
        ssp = ssps[index]
        csam_id = ssp_map.get(ssp)
        if not csam_id:
            logger.error(f"Could not find CSAM ID for SSP id: {ssp}")
            continue
        else:
            updated_ssps.append(ssp)

        result = retrieve_from_csam(
            csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/securityauthorization",
        )
        if len(result) == 0:
            logger.error(
                f"Could not retrieve securityauthorization details for CSAM ID {csam_id}. RegScale SSP id: {ssp}"
            )
            continue

        # Set the authorization expiration date
        ssp_obj = SecurityPlan.get_object(object_id=ssp)
        if ssp_obj:
            ssp_obj.authorizationTerminationDate = result.get("authorizationExpirationDate")
            ssp_obj.save()
        else:
            logger.debug(f"Failed to retrieve Security Plan id: {ssp}")
        # Get the custom fields
        field_values.extend(
            build_form_values(
                ssp=ssp, result=result, custom_map=authorization_map, custom_fields=authorization_custom_fields
            )
        )
    # Save the Custom Fields
    if len(field_values) > 0:
        field_values = fix_form_field_value(field_values)
        FormFieldValue.save_custom_fields(field_values)

    logger.info(f"Updated {len(updated_ssps)} Security Plans with authorization data")


def update_ssp_general(ssp: SecurityPlan, record: dict, org_map: dict) -> SecurityPlan:
    """
    Update or Create the SSP Record
    Based upon the values in Record

    :param SecurityPlan ssp: RegScale Security Plan
    :param dict record: record of values
    :param dict org_map: map of org names to orgId
    :return: SecurityPlan Object
    :return_type: SecurityPlan
    """

    ssp.otherIdentifier = record["id"]
    ssp.overallCategorization = record["categorization"]
    ssp.confidentiality = record["categorization"]
    ssp.integrity = record["categorization"]
    ssp.availability = record["categorization"]
    ssp.status = record["operationalStatus"]
    ssp.systemType = record["systemType"]
    ssp.description = record["purpose"]
    ssp.defaultAssessmentDays = 0
    if record["organization"] and org_map.get(record["organization"]):
        ssp.orgId = org_map.get(record["organization"])

    if ssp.id == 0:
        new_ssp = ssp.create()
    else:
        new_ssp = ssp.save()

    return new_ssp


def create_ssps(results: list, csam_ids: list) -> list:
    """
    Create ssps for csam ids that don't exist

    :param results: list of csam objects
    :param csam_ids: list of new CSAM_ids
    :return: list of updated SSPs
    :return_type List(SecurityPlan)
    """
    updated_ssps = []
    for index in track(range(len(results)), description=f"Creating {len(csam_ids)} New RegScale SSPs..."):
        result = results[index]
        # If result in csam_ids... its new:
        if str(result.get("id")) in csam_ids:
            ssp = SecurityPlan(systemName=result.get("name"), otherIdentifier=str(result.get("id")))
            new_ssp = ssp.create()
            if new_ssp.id > 0:
                updated_ssps.append(new_ssp)
    return updated_ssps


def save_ssp_front_matter(results: list, ssp_map: dict, custom_fields_basic_map: dict, org_map: dict) -> list:
    """
    Save the SSP data from the /systems endpoint

    :param list results: list of results from CSAM
    :param dict ssp_map: CSAM_ID to SSP Id
    :param dict custom_fields_basic_map: map of custom fields in RegScale
    :param dict org_map: map of existing orgs in RegScale
    :return: list of updated SSPs
    :return_type: List[SecurityPlan]
    """

    updated_ssps = []
    for index in track(
        range(len(results)),
        description=f"Importing {len(results)} SSP front matter...",
    ):
        result = results[index]

        # Get the existing SSP:
        ssp_id = ssp_map.get(str(result["id"]))
        if ssp_id:
            ssp = SecurityPlan.get_object(ssp_id)
        else:
            ssp = SecurityPlan(systemName=result["name"])
        # Update the SSP
        ssp = update_ssp_general(ssp, result, org_map)

        # Grab the Custom Fields
        field_values = set_front_matter_fields(ssp=ssp, result=result, custom_fields_basic_map=custom_fields_basic_map)

        # System Custom Fields
        field_values = fix_form_field_value(field_values)
        FormFieldValue.save_custom_fields(field_values)
        updated_ssps.append(ssp.id)
    logger.info(f"Updated {len(results)} Security Plans Front Matter")
    return updated_ssps


def set_front_matter_fields(ssp: SecurityPlan, result: dict, custom_fields_basic_map: dict) -> list:
    """
    parse the front matter custom fields
    and return a list of field values to be saved

    :param SecurityPlan ssp: RegScale Security Plan object
    :param dict result: response from CSAM
    :param dict custom_fields_basic_map: map of basic custom fields
    :return: list of dictionaries with field values
    :return_type: list
    """
    custom_fields_financial_list = [
        "Financial System",
        "omb Exhibit",
        "Investment Name",
        "Portfolio",
        "Prior Fy Funding",
        "Current Fy Funding",
        "Next Fy Funding",
        "Funding Import Status",
        "uiiCode",
    ]

    custom_fields_financial_map = FormFieldValue.check_custom_fields(
        custom_fields_financial_list, "securityplans", SSP_FINANCIAL_TAB
    )

    custom_fields_map = {
        "acronym": "acronym",
        "Classification": "classification",
        "FISMA Reportable": "fismaReportable",
        "Contractor System": "contractorSystem",
        "Critical Infrastructure": "criticalInfrastructure",
        "Mission Essential": "missionCritical",
    }
    custom_fields_fin_map = {
        "financialSystem": "Financial System",
        "ombExhibit": "omb Exhibit",
        "investmentName": "Investment Name",
        "portfolio": "Portfolio",
        "priorFyFunding": "Prior Fy Funding",
        "currentFyFunding": "Current Fy Funding",
        "nextFyFunding": "Next Fy Funding",
        "fundingImportStatus": "Funding Import Status",
        "uiiCode": "uiiCode",
    }

    # Pre-compute field mappings to avoid nested lookups
    basic_field_mapping = FormFieldValue.check_custom_fields(
        fields_list=list(custom_fields_map.keys()), module_name="securityplans", tab_name=SSP_BASIC_TAB
    )

    financial_field_mapping = {
        field: custom_fields_financial_map[mapped_name]
        for field, mapped_name in custom_fields_fin_map.items()
        if mapped_name in custom_fields_financial_map and field in result
    }

    # Start with required ID fields
    field_values = [
        {
            "record_id": ssp.id,
            "record_module": "securityplans",
            "form_field_id": custom_fields_basic_map[FISMA_FIELD_NAME],
            "field_value": str(result["externalId"]),
        },
        {
            "record_id": ssp.id,
            "record_module": "securityplans",
            "form_field_id": custom_fields_basic_map[CSAM_FIELD_NAME],
            "field_value": str(result["id"]),
        },
    ]

    # Process basic tab fields
    field_values.extend(
        build_form_values(ssp=ssp.id, result=result, custom_map=basic_field_mapping, custom_fields=custom_fields_map)
    )

    # Process financial tab fields
    field_values.extend(_create_financial_field_values(ssp.id, result, financial_field_mapping))

    return field_values


def _create_financial_field_values(record_id: int, result: dict, field_mapping: dict) -> list:
    """Helper function to create financial field values with proper handling of funding fields"""
    funding_fields = ["priorFyFunding", "currentFyFunding", "nextFyFunding"]

    field_values = []
    for field, field_id in field_mapping.items():
        value = result.get(field)
        # Handle blank dollar values
        if field in funding_fields:
            field_value = str(value) if value else "0"
        else:
            field_value = str(value)

        field_values.append(
            {
                "record_id": record_id,
                "record_module": "securityplans",
                "form_field_id": field_id,
                "field_value": field_value,
            }
        )
    return field_values
