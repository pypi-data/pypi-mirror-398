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
    fix_form_field_value,
    CSAM_FIELD_NAME,
    SSP_BASIC_TAB,
)

logger = logging.getLogger("regscale")


def import_csam_pocs(import_ids: Optional[List[int]] = None):
    """
    Import the Points of Contact from CSAM
    Into RegScale
    """
    custom_fields_pocs_list = [
        "Certifying Official",
        "Alternate Information System Security Manager",
        "Alternate Information System Security Officer",
        "Co Authorizing Official",
        "Chief Information Security Officer",
        "Senior Information Systems Security Officer",
        "Technical Lead",
    ]
    # Check Custom Fields exist
    custom_fields_pocs_map = FormFieldValue.check_custom_fields(
        custom_fields_pocs_list, "securityplans", "Points of Contact"
    )

    # Get a list of users and create a map to id
    users = User.get_list()
    user_map = {user.get("email").lower(): user.get("id") for user in users}

    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    updated_ssps = []
    custom_fields = []
    if len(ssps) == 0:
        return
    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP Points of Contact...",
    ):
        ssp = ssps[index]
        system_id = ssp_map.get(ssp)
        if not system_id:
            logger.error(f"Could not find CSAM ID for SSP id: {ssp}")
            continue
        else:
            updated_ssps.append(ssp)

        results = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/systempointsofcontact")
        if len(results) == 0:
            logger.error(f"Could not retrieve PoCs for CSAM ID {system_id}. RegScale SSP id: {ssp}")
            continue

        custom_field = _process_pocs(
            results=results, user_map=user_map, custom_fields_map=custom_fields_pocs_map, regscale_id=ssp
        )

        custom_fields.extend(custom_field)

    if len(custom_fields) > 0:
        custom_fields = fix_form_field_value(custom_fields)
        FormFieldValue.save_custom_fields(custom_fields)


def _process_pocs(results: list, user_map: dict, custom_fields_map: dict, regscale_id: int) -> list:
    ssp_obj = SecurityPlan.get_object(object_id=regscale_id)
    custom_fields = []

    for result in results:
        email = result.get("email")
        if not email:
            continue
        user = user_map.get(email.lower())
        if not user:
            continue

        if result.get("position") == "Authorizing Official":
            ssp_obj.planAuthorizingOfficialId = user
            ssp_obj.save()
        elif result.get("position") == "Information System Owner":
            ssp_obj.systemOwnerId = user
            ssp_obj.save()
        elif result.get("position") == "Information System Security Manager":
            ssp_obj.systemSecurityManagerId = user
            ssp_obj.save()
        elif result.get("position") == "Senior Information Security Officer":
            ssp_obj.planInformationSystemSecurityOfficerId = user
            ssp_obj.save()
        else:
            if not custom_fields_map.get(result.get("position")):
                continue
            custom_fields.append(
                {
                    "record_id": regscale_id,
                    "record_module": "securityplans",
                    "form_field_id": custom_fields_map[result.get("position")],
                    "field_value": user,
                }
            )
    return custom_fields
