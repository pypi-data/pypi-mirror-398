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
CONTINUITY_AND_IR = "Continuity and Incident Response"


def import_csam_contingency(import_ids: Optional[List[int]] = None):
    """
    Update the Targets, Contingency, & IR of the SSPs
    This requires a call to the /systems/<system_id>/continuityresponse
    endpoint

    :param list import_ids: Filtered list of SSPs
    :return: None
    """
    # Continuity & IR Fields
    # Goes to "Continuity and Incident Response" Tab
    # /CSAM/api/v1/systems/<system_id>/continuityresponse
    targets_map = {
        "MTD": "maximumTolerableDowntime",
        "RTO": "recoveryTimeObjective",
        "RPO": "recoveryPointObjective",
    }

    continuity_map = {
        "BIA Completed": "businessImpactAnalysisDateCompleted",
        "BIA Next Due Date": "businessImpactAnalysisNextDueDate",
        "CP Completed": "contingencyPlanDateCompleted",
        "CP Next Due Date": "contingencyPlanNextDueDate",
        "CP Training Completed": "contingencyPlanTrainingDateCompleted",
        "CP Training Next Due Date": "contingencyPlanTrainingNextDueDate",
        "CP Test Next Due Date": "contingencyPlanTestNextDueDate",
        "IRP Completed": "incidentResponsePlanDateCompleted",
        "IRP Next Due Date": "incidentResponsePlanNextDueDate",
        "IRP Training Completed": "incidentResponsePlanTrainingDateCompleted",
        "IRP Training Next Due Date": "incidentResponsePlanTrainingNextDueDate",
        "IRP Test Next Due Date": "incidentResponsePlanTestNextDueDate",
    }

    # /CSAM/api/v1/systems/<system_id>/continuitytest
    # testItem == "Contingency Plan (CP)""
    cp_test_map = {
        "CP Test Type": "testType",
        "CP Date Tested": "dateTested",
        "CP Test Outcome": "outcome",
        "CP RPO Achieved": "recoveryPointObjectiveAchieved",
        "CP RTO Achieved": "recoveryTimeObjectiveAchieved",
    }
    irp_test_map = {
        "IRP Test Type": "testType",
        "IRP Date Tested": "dateTested",
        "IRP Test Outcome": "outcome",
        "IRP RPO Achieved": "recoveryPointObjectiveAchieved",
        "IRP RTO Achieved": "recoveryTimeObjectiveAchieved",
    }

    # /CSAM/api/v1/systems/{system_id}/additionalstatus
    # name == "Contingency Plan Review" or "Document Review Aproval"
    cp_status_map = {
        "CPR Completed": "dateCompleted",
        "CPR Next Due Date": "nextDueDate",
        "CPR Expiration Date": "expirationDate",
    }
    dr_status_map = {
        "Doc Review Completed": "dateCompleted",
        "Doc Review Next Due Date": "nextDueDate",
        "Doc Review Expiration Date": "expirationDate",
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

        field_values.extend(
            get_continuity_response_fields(
                ssp=ssp, csam_id=csam_id, targets_map=targets_map, continuity_map=continuity_map
            )
        )

        field_values.extend(
            get_continuity_test_fields(ssp=ssp, csam_id=csam_id, cp_test_map=cp_test_map, irp_test_map=irp_test_map)
        )

        field_values.extend(
            get_additional_status_fields(
                ssp=ssp, csam_id=csam_id, cp_status_map=cp_status_map, dr_status_map=dr_status_map
            )
        )

    # Save the Custom Fields
    if len(field_values) > 0:
        field_values = fix_form_field_value(field_values)
        FormFieldValue.save_custom_fields(field_values)

    logger.info(f"Updated {len(updated_ssps)} Security Plans with contingency data")


def get_continuity_response_fields(ssp: int, csam_id: int, targets_map: dict, continuity_map: dict) -> List:
    targets_field_map = FormFieldValue.check_custom_fields(
        targets_map.keys(), "securityplans", "Recovery Targets and Outcomes"
    )
    continuity_field_map = FormFieldValue.check_custom_fields(
        continuity_map.keys(), "securityplans", "Continuity and Incident Response"
    )

    field_values = []
    result = retrieve_from_csam(
        csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/continuityresponse",
    )

    if not result:
        logger.error(f"Could not retrieve continuityresponse details for CSAM ID {csam_id}. RegScale SSP id: {ssp}")
        return []

    response_data = result[0]

    field_values.extend(
        build_form_values(ssp=ssp, result=response_data, custom_map=targets_field_map, custom_fields=targets_map)
    )
    field_values.extend(
        build_form_values(ssp=ssp, result=response_data, custom_map=continuity_field_map, custom_fields=continuity_map)
    )

    return field_values


def get_continuity_test_fields(ssp: int, csam_id: int, cp_test_map: dict, irp_test_map: dict) -> List:
    cp_fields_map = FormFieldValue.check_custom_fields(cp_test_map.keys(), "securityplans", CONTINUITY_TESTS)
    irp_fields_map = FormFieldValue.check_custom_fields(irp_test_map.keys(), "securityplans", CONTINUITY_TESTS)

    # Get the data from continuitytest
    results = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/continuitytest")

    if not results:
        logger.error(f"Could not retrieve continuitytest details for CSAM ID {csam_id}. RegScale SSP id: {ssp}")
        return []

    field_values = []
    for result in results:
        test_item = result.get("testItem")

        # Process Contingency Plan (CP) fields
        if test_item == "Contingency Plan (CP)":
            field_values.extend(
                build_form_values(ssp=ssp, result=result, custom_map=cp_fields_map, custom_fields=cp_test_map)
            )

        # Process Incident Response Plan (IRP) fields
        elif test_item == "Incident Response Plan (IRP)":
            field_values.extend(
                build_form_values(ssp=ssp, result=result, custom_map=irp_fields_map, custom_fields=irp_test_map)
            )

    return field_values


def get_additional_status_fields(ssp: int, csam_id: int, cp_status_map: dict, dr_status_map: dict) -> List:
    cp_fields_map = FormFieldValue.check_custom_fields(cp_status_map.keys(), "securityplans", CONTINUITY_AND_IR)
    dr_fields_map = FormFieldValue.check_custom_fields(dr_status_map.keys(), "securityplans", CONTINUITY_AND_IR)

    # Get the data from continuitytest
    results = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/additionalstatus")

    if not results:
        logger.error(f"Could not retrieve continuitytest details for CSAM ID {csam_id}. RegScale SSP id: {ssp}")
        return []

    field_values = []
    for result in results:
        test_item = result.get("name")

        # Process Contingency Plan (CP) fields
        if test_item == "Contingency Plan Review":
            field_values.extend(
                build_form_values(ssp=ssp, result=result, custom_map=cp_fields_map, custom_fields=cp_status_map)
            )

        # Process Doc Review fields
        elif test_item == "Document Review Approval":
            field_values.extend(
                build_form_values(ssp=ssp, result=result, custom_map=dr_fields_map, custom_fields=dr_status_map)
            )

    return field_values
