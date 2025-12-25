#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
import os
from pathlib import Path
from typing import List, Optional
from rich.progress import track
from regscale.core.app.application import Application
from regscale.core.app.api import Api
from regscale.models.regscale_models.file import File
from regscale.models.regscale_models.form_field_value import FormFieldValue
from regscale.utils.b64conversion import encode_file_to_base64
from regscale.integrations.public.csam.csam_common import (
    retrieve_from_csam,
    retrieve_ssps_custom_form_map,
    CSAM_FIELD_NAME,
    SSP_BASIC_TAB,
)

logger = logging.getLogger("regscale")


def import_csam_artifacts(import_ids: Optional[List[int]] = None):
    """
    Import the Points of Contact from CSAM
    Into RegScale
    """

    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    ssps = import_ids if import_ids else list(ssp_map.keys())

    app = Application()
    artifact_types = app.config.get("csamArtifactTypes", None)
    if len(artifact_types) == 0:
        logger.info("No artifacts types configured to be imported")
        return

    if len(ssps) == 0:
        return

    # Get tags
    tags = File.get_existing_tags_dict()

    all_artifacts = []
    for index in track(
        range(len(ssps)),
        description=f"Importing {len(ssps)} SSP artifacts...",
    ):
        artifacts = []
        ssp = ssps[index]
        system_id = ssp_map.get(ssp)

        # For each plan, build a list of artifactIds
        # Start with appendices
        results = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/artifacts")

        artifacts = process_artifacts(results=results, ssp=ssp, types=artifact_types)
        all_artifacts.extend(artifacts)

    # Download the artifacts
    for artifact in all_artifacts:
        artifact["local_file"] = retrieve_artifacts(artifact=artifact)

    # Upload the artifacts
    api = Api()
    for item in all_artifacts:
        # Find the tag:
        tag = item.get("artifactDescription")
        tag = tag.lower()
        tag = tag.replace(" ", "-")
        if tag not in tags:
            logger.warning(
                f"For filename: {item.get('file_name')}, tag: {tag} not in RegScale.  Add tag and then add tag to file upload."
            )
            tag = ""

        File.upload_file_to_regscale(
            file_name=item.get("file_name").name,
            parent_id=item.get("regscale_id"),
            parent_module="securityplans",
            api=api,
            file_data=encode_file_to_base64(item.get("local_file")),
            tags=tag,
        )


def process_artifacts(results: list, ssp: int, types: list) -> list:
    """
    Parse the list of artifacts and return a list of
    artifact ids matching the artifact types
    selected

    :param results: list of artifacts from CSAM
    :param ssp: RegScale SSP Id
    :param types: list of artifact types to import
    :return: list of artifactIds
    """
    artifacts = []
    # Check if the artifact type is in the list
    # Check if the artifactId set
    for result in results:
        if result.get("artifactType") in types and result.get("artifactId"):
            artifacts.append(
                {
                    "regscale_id": ssp,
                    "artifact_description": result.get("artifactDescription"),
                    "artifact_id": result.get("artifactId"),
                    "file_name": result.get("filename"),
                }
            )

    return artifacts


def retrieve_artifacts(artifact: dict) -> Path:
    """
    Retrieve file from CSAM

    :param artifact: dict with the filename, artifact id, and securityplan Id
    :return: file Path
    """

    file_data = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/artifacts/{artifact.get('artifact_id')}")

    if file_data is None:
        logger.warning(f"No data received for {artifact.get('artifact_id')}")
        return Path(None)

    file_path = f"artifacts{os.sep}{artifact.get('file_name')}"
    with open(file_path, "wb") as f:
        f.write(file_data)

    return Path(file_path)
