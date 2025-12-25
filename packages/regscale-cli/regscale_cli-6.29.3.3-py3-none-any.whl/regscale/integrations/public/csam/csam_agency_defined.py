#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM agencydefineddata into RegScale"""

from rich.progress import track
from typing import Optional, List
import logging
from regscale.core.app.application import Application
from regscale.models.regscale_models import SecurityPlan, FormFieldValue
from regscale.integrations.public.csam.csam_common import (
    retrieve_from_csam,
    build_form_values,
    retrieve_ssps_custom_form_map,
    SSP_BASIC_TAB,
    CSAM_FIELD_NAME,
)

logger = logging.getLogger("regscale")

AI_ML = "AI/ML Components"


def update_ssp_agency_details(import_ids: Optional[List[int]] = None) -> list:
    """
    Update the Agency Details of the SSPs
    This requires a call to the /system/{id}/agencydefineddataitems
    endpoint

    :param list import_ids: list of RegScale SSPs
    :return: list of updated SSPs
    :return_type: List[SecurityPlan]
    """
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    app = Application()
    agency_defined = app.config.get("csamAgencyDefinedDataItems", None)

    updated_ssps = []
    updated_ssps = update_agency_defined(ssps=ssps, map=agency_defined)

    return updated_ssps


def set_cloud_system(ssp: SecurityPlan, item: dict) -> SecurityPlan:
    """
    Set the cloud system values in the SSP
    :param SeucrityPlan ssp: RegScale Security Plan
    :param dict item: record from CSAM
    :return: SecurityPlan object with updated cloud system values
    :return_type: SecurityPlan
    """
    ssp.bDeployPublic = True if "Public" in item.get("value") else ssp.bDeployPublic
    ssp.bDeployPrivate = True if "Private" in item.get("value") else ssp.bDeployPrivate
    ssp.bDeployHybrid = True if "Hybrid" in item.get("value") else ssp.bDeployHybrid
    ssp.bDeployOther = True if "Community" in item.get("value") else ssp.bDeployOther
    if ssp.bDeployHybrid or ssp.bDeployOther:
        ssp.deployOtherRemarks = "Hybrid or Community"
    if "GovCloud" in item.get("value") or "Government" in item.get("value"):
        ssp.bDeployGov = True

    return ssp


def set_cloud_service(ssp: SecurityPlan, item: dict) -> SecurityPlan:
    """
    Set the cloud service model values in the SSP

    :param SecurityPlan ssp: RegScale Security Plan
    :param dict item: record from CSAM
    :return: Updated SecurityPlan object
    :return_type: SecurityPlan
    """
    ssp.bModelIaaS = True if "IaaS" in item.get("value") else ssp.bModelIaaS
    ssp.bModelPaaS = True if "PaaS" in item.get("value") else ssp.bModelPaaS
    ssp.bModelSaaS = True if "SaaS" in item.get("value") else ssp.bModelSaaS
    return ssp


def set_binary_fields(item: dict, ssp: SecurityPlan, custom_fields_map: dict) -> dict:
    """
    Logic to set the custom fields were the source are binary

    :param dict item: record from CSAM
    :param SecurityPlan ssp: RegScale Security Plan
    :param custom_fields_map: map of custom field names to ids
    :return: RegScale custom fields records
    :return_type: dict
    """
    return {
        "record_id": ssp.id,
        "form_field_id": custom_fields_map[item.get("attributeName")],
        "field_value": "Yes" if (item.get("value")) == "1" else "No",
    }


def update_agency_defined(ssps: list, map: dict) -> list:
    custom_fields_map = FormFieldValue.check_custom_fields(
        fields_list=map.values(), module_name="securityplans", tab_name="Agency Defined Data Items"
    )

    values = []
    updated_ssps = []
    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP agency details...",
    ):
        ssp = ssps[index]
        ssp_obj = SecurityPlan.get_object(object_id=ssp)
        csam_id = ssp_obj.otherIdentifier
        if not csam_id:
            logger.error(f"Could not find CSAM ID for SSP {ssp.systemName} id: {ssp.id}")
            continue

        results = retrieve_from_csam(
            csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/agencydefineddataitems",
        )
        if len(results) == 0:
            logger.error(f"Could not retrieve details for CSAM ID {csam_id}. RegScale SSP: Id: {ssp.id}")
            continue
        # Process system fields
        for item in results:
            value = build_agency_defined(
                result=item, ssp=ssp_obj, agency_fields=map, custom_fields_map=custom_fields_map
            )

            if len(value) > 0:
                values.append(value)

        updated_ssps.append(ssp)

    # Create custom fields
    if len(values) > 0:
        FormFieldValue.save_custom_fields(form_field_values=values)

    logger.info(f"Updated {len(updated_ssps)} Security Plans with Agency Details")
    return updated_ssps


def build_agency_defined(result: dict, ssp: SecurityPlan, agency_fields: dict, custom_fields_map: dict) -> dict:
    """
    Build out the ssp and custom fields for each record from CSAM

    :param result: record from CSAM
    :param ssp: RegScale Security Plan object
    :param agency_fields: dictionary of CSAM attributes to RegScale custom field
    :param custom_fields_map: dictionary of RegScale custom field to field Id
    :return: custom field dictionary
    """
    value = {}
    if result.get("attributeName") == "High Value Asset":
        ssp.hva = True if result.get("value") in ["1", "Yes"] else False
    # Binary Values
    if result.get("attributeName") in ["Cloud System", "Cloud Deployment Model"]:
        ssp = set_cloud_system(ssp, result)

    if result.get("attributeName") in ["Cloud Service Model", "Cloud System"]:
        ssp = set_cloud_service(ssp, result)
    if result.get("attributeName") in agency_fields.keys():
        form_field = agency_fields.get(result.get("attributeName"))
        csam_value = result.get("value")
        if csam_value == "1":
            field_value = "Yes"
        elif csam_value == "0":
            field_value = "No"
        else:
            field_value = csam_value

        value = {
            "record_id": ssp.id,
            "record_module": "securityplans",
            "form_field_id": custom_fields_map.get(form_field),
            "field_value": field_value,
        }
    # Save the SSP
    ssp.save()

    return value
