#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
from typing import List, Tuple
from urllib.parse import urljoin
from regscale.core.app.application import Application
from regscale.core.app.api import Api

from regscale.models.regscale_models import SecurityPlan, Module
from regscale.models.regscale_models.regscale_model import RegScaleModel
from regscale.integrations.control_matcher import ControlMatcher
from regscale.models.regscale_models.form_field_value import FormFieldValue

SSP_BASIC_TAB = "Basic Info"
CSAM_FIELD_NAME = "CSAM Id"
FISMA_FIELD_NAME = "FISMA Id"
SYSTEM_ID = "System ID"

logger = logging.getLogger("regscale")


def retrieve_custom_form_ssps_map(tab_name: str, field_form_id: int) -> dict:
    """
    Retreives a list of the SSPs in RegScale
    Returns a map of Custom Field Value: RegScale Id

    :param str tab_name: The RegScale tab name where the custom field is located
    :param int field_form_id: The RegScale Form Id of custom field
    :param int tab_id: The RegScale tab id
    :return: dictionary of FieldForm Id: regscale_ssp_id
    :return_type: dict
    """
    tab = Module.get_tab_by_name(regscale_module_name="securityplans", regscale_tab_name=tab_name)

    field_form_map = {}
    ssps = SecurityPlan.get_ssp_list()
    form_values = []
    for ssp in ssps:
        form_values = FormFieldValue.get_field_values(
            record_id=ssp["id"], module_name=SecurityPlan.get_module_slug(), form_id=tab.id
        )

        for form in form_values:
            if form.formFieldId == field_form_id and form.data:
                field_form_map[form.data] = ssp["id"]
        form_values = []
    return field_form_map


def retrieve_ssps_custom_form_map(tab_name: str, field_form_id: int) -> dict:
    """
    Retreives a list of the SSPs in RegScale
    Returns a map of Custom Field Value: RegScale Id

    :param str tab_name: The RegScale tab name where the custom field is located
    :param int field_form_id: The RegScale Form Id of custom field
    :param int tab_id: The RegScale tab id
    :return: dictionary of FieldForm Id: regscale_ssp_id
    :return_type: dict
    """
    tab = Module.get_tab_by_name(regscale_module_name="securityplans", regscale_tab_name=tab_name)

    field_form_map = {}
    ssps = SecurityPlan.get_ssp_list()
    form_values = []
    for ssp in ssps:
        form_values = FormFieldValue.get_field_values(
            record_id=ssp["id"], module_name=SecurityPlan.get_module_slug(), form_id=tab.id
        )

        for form in form_values:
            if form.formFieldId == field_form_id and form.data:
                field_form_map[ssp["id"]] = form.data
        form_values = []
    return field_form_map


def retrieve_from_csam(csam_endpoint: str) -> list:
    """
    Connect to CSAM and retrieve data

    :param str csam_endpoint: API Endpoint
    :return: List of dict objects
    :return_type: list
    """
    logger.debug("Retrieving data from CSAM")
    app = Application()
    api = Api()
    csam_token = app.config.get("csamToken")
    csam_url = app.config.get("csamURL")

    if not csam_token or csam_token == "<mySecretGoesHere>":
        logger.warning("No CSAM Token in init.yaml")
        return []

    if not csam_url or csam_token == "<myCSAMURLgoeshere>":
        logger.warning("No CSAM URL in init.yaml")
        return []

    if "Bearer" not in csam_token:
        csam_token = f"Bearer {csam_token}"

    url = urljoin(csam_url, csam_endpoint)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": csam_token,
    }

    issue_response = api.get(url=url, headers=headers)
    if not issue_response:
        logger.warning(f"Call to {url} returned no response")
        return []
    elif issue_response.status_code in [204, 404]:
        logger.warning(f"Call to {url} Returned error: {issue_response.text}")
        return []
    if issue_response.ok:
        return issue_response.json()

    return []


def build_form_values(ssp: int, result: dict, custom_map: dict, custom_fields: dict) -> list:
    """
    Takes a RegScale ssp id, a list of results from CSAM,
    a map of Custom Field names to CSAM fields, and
    a map of Custom Field names to FormField ids
    and builds formfieldvalue dictionaries to upload

    :param ssp: id of Security Plan
    :param result: list of results from CSAM
    :param custom_map: dict of Custom Field names to FormField ids
    :param custom_fields: dict of Custom Field names to CSAM Fields
    :return: list of FormField Values to upload
    """
    field_values = []
    for key, value in custom_fields.items():
        if not custom_map.get(key):
            continue
        csam_value = result.get(value)
        if csam_value is None:
            continue
        if isinstance(csam_value, bool):
            field_value = "Yes" if csam_value else "No"
        else:
            field_value = str(csam_value)
        if field_value:
            field_values.append(
                {
                    "record_id": ssp,
                    "record_module": "securityplans",
                    "form_field_id": custom_map.get(key),
                    "field_value": field_value,
                }
            )
    return field_values


def fix_form_field_value(form_fields: list) -> list:
    """
    Cleans up a list of FormFieldValue dicts to prevent
    400 errors due to misformed values

    :param form_fields: list of formFieldValue dicts
    :return: list of fixed formFieldValues dicts
    """
    new_field_values = []
    for field_value in form_fields:
        # Check if record_id, record_module, and form_field_id are set
        if (field_value.get("record_id") is None) or (field_value.get("record_id") == 0):
            continue
        if (field_value.get("form_field_id") is None) or (field_value.get("form_field_id") == 0):
            continue

        # Check if value == "None"
        if field_value.get("field_value") == "None":
            field_value["field_value"] = ""

        new_field_values.append(field_value)
    return new_field_values


def test_csam_connection():
    """
    Tests connections to CSAM
    """
    response = retrieve_from_csam(csam_endpoint="/CSAM/api/v1/components")

    if response:
        logger.info("Successfully connected to CSAM")


def get_sync_records(results: list, ssp_map: dict) -> Tuple[List, List]:
    """
    Checks lists of CSAM ids and SSP ids and returns
    The CSAM ids missing from Regscale (new_csam_ids)
    and the SSP Ids that are not in CSAM

    :param results: list of csam system objects
    :param ssp_map: map of CSAM Ids to SSPs
    :return: new_csam_ids: SSPs that need to be created
    :return: missing_csam_ids: SSPs that need to be deleted
    :return_type: Tuple[List,List]
    """
    csam_ids = [str(result.get("id")) for result in results]
    new_csam_ids = []
    for csam_id in csam_ids:
        if csam_id not in ssp_map.keys():
            new_csam_ids.append(csam_id)
    missing_csam_ids = []
    for ssp_id in ssp_map.keys():
        if ssp_id not in csam_ids:
            missing_csam_ids.append(ssp_id)

    return new_csam_ids, missing_csam_ids
