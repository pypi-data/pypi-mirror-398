#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
from typing import List, Optional
from rich.progress import track
from regscale.models.regscale_models import User, SecurityPlan
from regscale.models.regscale_models.form_field_value import FormFieldValue
from regscale.integrations.public.csam.csam_common import (
    retrieve_from_csam,
    retrieve_ssps_custom_form_map,
    build_form_values,
    fix_form_field_value,
    CSAM_FIELD_NAME,
    SSP_BASIC_TAB,
)

logger = logging.getLogger("regscale")

CONTINUITY_TESTS = "Continuity Tests"


def import_csam_additional_status(import_ids: Optional[List[int]] = None):
    """
    Update Additional Statuses
    This requires a call to the /systems/<system_id>/status
    endpoint

    :param list import_ids: Filtered list of SSPs
    :return: None
    """
    status_map = {
        "Risk Assessment Completed": "riskAssessmentDateCompleted",
        "Risk Assessment Next Due Date": "riskAssessmentNextDueDate",
        "Risk Assessment Expiration Date": "riskAssessmentExpirationDate",
        "SSP Completed": "systemSecurityPlanDateCompleted",
        "SSP Next Due Date": "systemSecurityPlanNextDueDate",
        "CM Completed": "configurationManagementDateCompleted",
        "CM Next Due Date": "configurationManagementNextDueDate",
    }

    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    updated_ssps = []
    field_values = []
    if len(ssps) == 0:
        return

    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP contingency data...",
    ):
        ssp = ssps[index]
        csam_id = ssp_map.get(ssp)
        if not csam_id:
            logger.error(f"Could not find CSAM ID for SSP id: {ssp}")
            continue
        else:
            updated_ssps.append(ssp)

        field_values.extend(get_additional_status(ssp=ssp, csam_id=csam_id, status_map=status_map))

    # Save the Custom Fields
    if len(field_values) > 0:
        field_values = fix_form_field_value(field_values)
        FormFieldValue.save_custom_fields(field_values)

    logger.info(f"Updated {len(updated_ssps)} Security Plans with contingency data")


def get_additional_status(ssp: int, csam_id: int, status_map: dict) -> List:
    status_field_map = FormFieldValue.check_custom_fields(status_map.keys(), "securityplans", "Status and Archive")

    field_values = []
    result = retrieve_from_csam(
        csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/status",
    )

    if not result:
        logger.error(f"Could not retrieve status details for CSAM ID {csam_id}. RegScale SSP id: {ssp}")
        return []

    field_values.extend(
        build_form_values(ssp=ssp, result=result, custom_map=status_field_map, custom_fields=status_map)
    )

    return field_values
