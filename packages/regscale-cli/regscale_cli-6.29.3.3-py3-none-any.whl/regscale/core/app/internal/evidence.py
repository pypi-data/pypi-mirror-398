#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates evidence gathering into RegScale CLI"""


# standard python imports
import fnmatch
import itertools
import json
import os
import shutil
import zipfile
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Tuple

import click  # type: ignore
import pdfplumber  # type: ignore
from docx import Document  # type: ignore
from rich.progress import Progress, TaskID

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import check_file_path, create_progress_object, error_and_exit
from regscale.models.app_models.click import regscale_ssp_id
from regscale.models.regscale_models import Assessment, File, Project, SecurityPlan, Evidence, Component
from regscale.models.regscale_models.control_implementation import ControlImplementation

logger = getLogger("regscale")


@click.group()
def evidence():
    """Welcome to the RegScale Evidence Collection Automation CLI!"""


@evidence.command()
def start():
    """Starts the evidence collection automation process."""
    run_evidence_collection()


@evidence.command(name="build_package")
@regscale_ssp_id()
@click.option(
    "--path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, path_type=Path),
    help="Provide the desired path for creation of evidence files.",
    default=os.path.join(os.getcwd(), "evidence"),
    required=True,
)
def build_package(regscale_ssp_id: int, path: Path):
    """
    This function will build a directory of evidence with the provided RegScale SSP Id
    and RegScale Module and produce a zip file for extraction and use.
    """
    package_builder(ssp_id=regscale_ssp_id, path=path)


def run_evidence_collection():
    """
    This function will start the evidence collection automation process
    """
    import pymupdf  # type: ignore

    app = Application()
    api = Api()
    config = app.config

    logger.info("Starting evidence collection process")

    check_file_path("./static")
    progress = create_progress_object()
    with progress:
        task1 = progress.add_task("[white]Initializing evidence collection...", total=4)
        # call function to define variable for use outside of function
        evidence_folder, dir_name, new_cwd = set_directory_variables(
            task=task1, evidence_folder=config["evidenceFolder"], progress=progress
        )

        # call function to define variable for use outside of function
        required_docs, document_list = parse_required_docs(
            evidence_folder=evidence_folder, task=task1, progress=progress
        )

        # call function to define variable for use outside of function
        times = get_doc_timestamps(evidence_folder=new_cwd, directory=dir_name, task=task1, progress=progress)

        # call function to define variable for use outside of function
        texts = set_required_texts(evidence_folder=evidence_folder, task=task1, progress=progress)

        # call function to define variable for use outside of function
        folders = find_required_files_in_folder(evidence_folder=new_cwd, task=task1, progress=progress)

        task2 = progress.add_task("[white]Analyzing documents and content...", total=6)

        # call function to define variable for use outside of function
        sig_results = signature_assessment_results(
            directory=folders, r_docs=required_docs, task=task2, progress=progress
        )

        # call function to define variable for use outside of function
        doc_results = document_assessment_results(
            directory=folders, documents=document_list, task=task2, progress=progress
        )

        # call function to define variable for use outside of function
        file_texts = parse_required_text_from_files(evidence_folder=new_cwd, task=task2, progress=progress)

        # call function to define variable for use outside of function
        search_results = text_string_search(f_texts=file_texts, req_texts=texts, task=task2, progress=progress)

        # call function to define variable for use outside of function
        text_results = text_assessment_results(searches=search_results, r_texts=texts, task=task2, progress=progress)

        task3 = progress.add_task("[white]Processing assessment data...", total=4)

        # call function to define variable for use outside of function
        data = gather_test_project_data(api=api, evidence_folder=evidence_folder, task=task3, progress=progress)

        # call function to define variable to use outside of function
        time_results = assess_doc_timestamps(timestamps=times, documents=required_docs, task=task3, progress=progress)

        # call function to define variable to use outside of function
        report = assessments_report(
            docres=doc_results,
            textres=text_results,
            timeres=time_results,
            sigres=sig_results,
            task=task3,
            progress=progress,
        )

        # call function to define variable to use outside of function
        results = build_assessment_dataframe(assessments=report, task=task3, progress=progress)

        # call function to define variable for use outside of function
        score_data = build_score_data(assessments=results, task=task3, progress=progress)

        # call function to define variable for use outside of function
        html_output = build_html_table(assessments=report, task=task3, progress=progress)

        # call function to create child assessment via POST request
        create_child_assessments(
            api=api, project_data=data, output=html_output, score_data=score_data, task=task3, progress=progress
        )

        # Display collected files summary
        display_collected_files(folders, evidence_folder)


def display_collected_files(folders: list[dict], evidence_folder: str) -> None:
    """
    Display a summary of collected files to the user

    :param list[dict] folders: List of files found in evidence folder
    :param str evidence_folder: Path to evidence folder
    :rtype: None
    """
    if not folders:
        logger.info("No files were collected from the evidence folder.")
        return

    logger.info("=" * 60)
    logger.info("EVIDENCE COLLECTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Evidence folder: {evidence_folder}")
    logger.info(f"Total files collected: {len(folders)}")
    logger.info("")

    # Group files by program/folder
    programs = {}
    for file_info in folders:
        program = file_info.get("program", "unknown")
        filename = file_info.get("file", "unknown")
        if program not in programs:
            programs[program] = []
        programs[program].append(filename)

    # Display files by program
    for program, files in programs.items():
        logger.info(f"Program: {program}")
        logger.info("-" * 40)
        for file in sorted(files):
            logger.info(f"  • {file}")
        logger.info("")

    logger.info("=" * 60)


def package_builder(ssp_id: int, path: Path):
    """Function to build a directory of evidence and produce a zip file for extraction and use

    :param int ssp_id: RegScale System Security Plan ID
    :param Path path: directory for file location
    :return None
    """
    app = Application()
    api = Api()
    with create_progress_object() as progress:
        task = progress.add_task("[white]Building and zipping evidence folder for audit...", total=8)
        try:
            # Obtaining MEGA Api for given Organizer Record.
            ssp = SecurityPlan.fetch_mega_api_data(ssp_id)
            module_folder_name = f'{ssp["securityPlan"]["id"]}_{ssp["securityPlan"]["systemName"]}'
            folder_contents_name = f'{ssp["securityPlan"]["id"]}_Evidence_Folder_Contents'

            module_folder = path / module_folder_name
            os.makedirs(module_folder.absolute(), exist_ok=True)

            progress.update(task, advance=1)

            # Checking MEGA Api for Attachments at SSP level
            process_ssp_attachments(
                ssp=ssp,
                path=path,
                folder_contents_name=folder_contents_name,
                module_folder_name=module_folder_name,
                api=api,
            )

            progress.update(task, advance=1)

            # Process evidence lockers at SSP level
            process_ssp_evidence_lockers(
                ssp_id=ssp_id,
                path=path,
                module_folder=module_folder,
                api=api,
            )

            progress.update(task, advance=1)

            # Checking MEGA Api for Attachments at Control level
            process_control_attachments(
                ssp=ssp,
                path=path,
                progress=progress,
                module_folder_name=module_folder_name,
                module_folder=module_folder,
                api=api,
                task=task,
            )

            progress.update(task, advance=1)

            # Process components and their evidence
            process_components_evidence(
                ssp_id=ssp_id,
                path=path,
                module_folder=module_folder,
                api=api,
            )

            progress.update(task, advance=1)

            # Creating zip file and removing temporary Evidence Folder
            new_path = Path("./evidence.zip")
            zip_folder(path, new_path)
            remove_directory(module_folder)
            os.remove(path / f"{folder_contents_name}.json")
            shutil.move(new_path, path / "evidence.zip")
            progress.update(task, advance=1)
            app.logger.info("An evidence zipfile has been created and is ready for use!")
        except Exception as ex:
            app.logger.info("No SSP or Evidence exists for given Organizer Record.\n%s", ex)

        progress.update(task, advance=1)
        app.logger.info("Evidence zipfile located. Thank you!")


def process_ssp_attachments(ssp: dict, path: Path, folder_contents_name: str, module_folder_name: str, api: Api):
    """
    Process SSP attachments and download them to the evidence folder

    :param dict ssp: RegScale System Security Plan with mega API data
    :param Path path: directory for file location
    :param str folder_contents_name: name of the folder contents file
    :param str module_folder_name: name of the module folder
    :param Api api: RegScale CLI API object
    """
    if attachments := ssp.get("attachments"):
        outter_attachments = [
            {
                "fileName": i["trustedDisplayName"],
                "storedName": i["trustedStorageName"],
                "parentId": i["parentId"],
                "parentModule": i["parentModule"],
                "fileHash": i.get("fileHash") or i.get("shaHash"),
                "fileSize": i["size"],
                "dateCreated": i["dateCreated"],
            }
            for i in attachments
        ]

        json_data = json.dumps(outter_attachments, indent=4, separators=(", ", ": "))
        with open(f"{path}/{folder_contents_name}.json", "w", newline="\n") as next_output:
            next_output.write(json_data)

        # Adding any Attachments at SSP level to corresponding folder
        for f in outter_attachments:
            file = File.download_file_from_regscale_to_memory(
                api=api,
                record_id=f["parentId"],
                module=f["parentModule"],
                stored_name=f["storedName"],
                file_hash=f["fileHash"],
            )
            with open(f"{path}/{module_folder_name}/{f['fileName']}", "wb") as att:
                att.write(file)

    else:
        api.logger.info("No Evidence at SSP level for SSP. Checking for Evidence at Control level.")


def process_control_attachments(
    ssp: dict, path: Path, progress: Progress, module_folder_name: str, module_folder: Path, api: Api, task: TaskID
) -> None:
    """
    Process Control attachments and download them to the evidence folder

    :param dict ssp: RegScale System Security Plan with mega API data
    :param Path path: directory for file location
    :param Progress progress: Progress object
    :param str module_folder_name: name of the module folder
    :param Path module_folder: path to module folder
    :param Api api: RegScale CLI API object
    :param TaskID task: The task to update on the job_progress
    :rtype: None
    """
    if controls := ssp["normalizedControls"]:
        control_attachments = []
        for i in controls:
            name = i["control"]["item3"]["controlId"]

            for p in i["attachments"]:
                if not p:
                    continue
                file_name = p["trustedDisplayName"]
                stored_name = p["trustedStorageName"]
                parent_id = p["parentId"]
                parent_module = p["parentModule"]
                file_hash = p["fileHash"]
                sha_hash = p["shaHash"]
                file_size = p["size"]
                date_created = p["dateCreated"]

                control_attachments.append(
                    {
                        "controlId": name,
                        "fileName": file_name,
                        "storedName": stored_name,
                        "parentId": parent_id,
                        "parentModule": parent_module,
                        "fileHash": file_hash,
                        "shaHash": sha_hash,
                        "fileSize": file_size,
                        "dateCreated": date_created,
                    }
                )

        progress.update(task, advance=1)

        # Creating folders for Controls with Attachments
        control_folders = []
        for name in control_attachments:
            control_folders.append(name["controlId"])
            control_folders = list(set(control_folders))
        for i in control_folders:
            os.makedirs(module_folder / str(i), exist_ok=True)

        # Adding any Attachments at Control level to corresponding folder
        _download_control_attachments(control_attachments, api, path, module_folder_name)

        # Process evidence lockers for controls
        _process_control_evidence_lockers(control_attachments, api, path, module_folder_name)

        progress.update(task, advance=1)

    else:
        api.logger.info("No Control level Evidence for SSP.")


def _download_control_attachments(
    control_attachments: list[dict], api: Api, path: Path, module_folder_name: str
) -> None:
    """
    Download Control attachments to the evidence folder

    :param list[dict] control_attachments: List of control attachments
    :param Api api: RegScale CLI API object
    :param Path path: directory for file location
    :param str module_folder_name: name of the module folder
    :rtype: None
    """
    for f in control_attachments:
        file = File.download_file_from_regscale_to_memory(
            api=api,
            record_id=f["parentId"],
            module=f["parentModule"],
            stored_name=f["storedName"],
            file_hash=f["fileHash"],
        )

        with open(
            f"{path}/{module_folder_name}/{f['controlId']}/{f['fileName']}",
            "wb",
        ) as output:
            output.write(file)
        with open(
            f"{path}/{module_folder_name}/{f['controlId']}/{f['controlId']}_Evidence_Folder_Contents.json",
            "a",
        ) as file_drop:
            json.dump(f, file_drop, indent=4, separators=(", ", ": "))


def _get_control_folder_name(control_attachments: list[dict], control_id: int) -> str | None:
    """
    Get the control folder name for a given control ID

    :param list[dict] control_attachments: List of control attachments
    :param int control_id: Control ID to find folder name for
    :return: Control folder name or None
    :rtype: str | None
    """
    for f in control_attachments:
        if f["parentId"] == control_id:
            return f["controlId"]
    return None


def _download_control_evidence_items(
    evidence_items: list[dict], control_folder_name: str, path: Path, module_folder_name: str, api: Api
) -> None:
    """
    Download evidence items for a control

    :param list[dict] evidence_items: List of evidence items
    :param str control_folder_name: Name of the control folder
    :param Path path: Base path for downloads
    :param str module_folder_name: Module folder name
    :param Api api: API object
    :rtype: None
    """
    logger.info(f"Found {len(evidence_items)} evidence items for control {control_folder_name}")

    for evidence_item in evidence_items:
        file_name = evidence_item.get("trustedDisplayName", f"evidence_{evidence_item.get('id', 'unknown')}")
        output_path = f"{path}/{module_folder_name}/{control_folder_name}/{file_name}"

        if download_evidence_file(api, evidence_item, output_path):
            logger.info(f"Downloaded evidence file: {file_name}")
        else:
            logger.warning(f"Failed to download evidence file: {file_name}")


def _process_control_evidence_lockers(
    control_attachments: list[dict], api: Api, path: Path, module_folder_name: str
) -> None:
    """
    Process evidence lockers for controls

    :param list[dict] control_attachments: List of control attachments
    :param Api api: RegScale CLI API object
    :param Path path: directory for file location
    :param str module_folder_name: name of the module folder
    :rtype: None
    """
    # Get unique control IDs
    control_ids = list({f["parentId"] for f in control_attachments})

    for control_id in control_ids:
        try:
            # Get evidence from evidence lockers for this control
            evidence_items = get_evidence_by_control(api, control_id)

            if evidence_items:
                # Find the control ID for folder naming
                control_folder_name = _get_control_folder_name(control_attachments, control_id)

                if control_folder_name:
                    _download_control_evidence_items(evidence_items, control_folder_name, path, module_folder_name, api)
        except Exception as e:
            logger.warning(f"Failed to process evidence lockers for control {control_id}: {e}")


def get_evidence_by_control(api: Api, control_id: int) -> list[dict]:
    """
    Get evidence for a specific control

    :param Api api: RegScale CLI API object (kept for backward compatibility)
    :param int control_id: Control ID
    :return: List of evidence items
    :rtype: list[dict]
    """
    # Suppress unused parameter warning for backward compatibility
    _ = api

    try:
        # Use Evidence model method instead of direct API call
        evidence_items = Evidence.get_all_by_parent(parent_id=control_id, parent_module="controls")
        # Convert to dict format for compatibility
        return [evidence.dict() for evidence in evidence_items]
    except Exception as e:
        logger.warning(f"Failed to get evidence for control {control_id}: {e}")
        return []


def get_evidence_by_security_plan(api: Api, ssp_id: int) -> list[dict]:
    """
    Get evidence for a specific security plan

    :param Api api: RegScale CLI API object (kept for backward compatibility)
    :param int ssp_id: Security Plan ID
    :return: List of evidence items
    :rtype: list[dict]
    """
    # Suppress unused parameter warning for backward compatibility
    _ = api

    try:
        # Use Evidence model method instead of direct API call
        evidence_items = Evidence.get_all_by_parent(parent_id=ssp_id, parent_module="securityplans")
        # Convert to dict format for compatibility
        return [evidence.dict() for evidence in evidence_items]
    except Exception as e:
        logger.warning(f"Failed to get evidence for security plan {ssp_id}: {e}")
        return []


def get_components_by_ssp(api: Api, ssp_id: int) -> list[dict]:
    """
    Get components for a specific security plan

    :param Api api: RegScale CLI API object (kept for backward compatibility)
    :param int ssp_id: Security Plan ID
    :return: List of active components
    :rtype: list[dict]
    """
    # Suppress unused parameter warning for backward compatibility
    _ = api

    try:
        # Use Component model method instead of direct API call
        components = Component.get_all_by_parent(parent_id=ssp_id, parent_module="securityplans")
        # Filter for active components only and convert to dict format
        return [comp.dict() for comp in components if comp.status == "Active"]
    except Exception as e:
        logger.warning(f"Failed to get components for security plan {ssp_id}: {e}")
        return []


def get_controls_by_parent(api: Api, parent_id: int, parent_module: str) -> list[dict]:
    """
    Get controls for a specific parent (SSP or Component)

    :param Api api: RegScale CLI API object (kept for backward compatibility)
    :param int parent_id: Parent ID
    :param str parent_module: Parent module (securityplans or components)
    :return: List of controls
    :rtype: list[dict]
    """
    # Suppress unused parameter warning for backward compatibility
    _ = api

    try:
        # Use ControlImplementation model method instead of direct API call
        controls = ControlImplementation.get_all_by_parent(parent_id=parent_id, parent_module=parent_module)
        # Convert to dict format for compatibility
        return [control.dict() for control in controls]
    except Exception as e:
        logger.warning(f"Failed to get controls for parent {parent_id} in module {parent_module}: {e}")
        return []


def download_evidence_file(api: Api, evidence_item: dict, output_path: str) -> bool:
    """
    Download an evidence file

    :param Api api: RegScale CLI API object
    :param dict evidence_item: Evidence item data
    :param str output_path: Path to save the file
    :return: True if successful, False otherwise
    :rtype: bool
    """
    try:
        file_data = File.download_file_from_regscale_to_memory(
            api=api,
            record_id=evidence_item["parentId"],
            module=evidence_item["parentModule"],
            stored_name=evidence_item["trustedStorageName"],
            file_hash=evidence_item.get("fileHash") or evidence_item.get("shaHash"),
        )

        if file_data is None:
            logger.warning(f"No data received for evidence file {evidence_item.get('trustedDisplayName', 'unknown')}")
            return False

        with open(output_path, "wb") as f:
            f.write(file_data)
        return True
    except Exception as e:
        logger.warning(f"Failed to download evidence file {evidence_item.get('trustedDisplayName', 'unknown')}: {e}")
        return False


def process_ssp_evidence_lockers(ssp_id: int, path: Path, module_folder: Path, api: Api) -> None:
    """
    Process evidence lockers at SSP level

    :param int ssp_id: Security Plan ID
    :param Path path: directory for file location
    :param str module_folder_name: name of the module folder
    :param Path module_folder: path to module folder
    :param Api api: RegScale CLI API object
    :rtype: None
    """
    try:
        # Get evidence from evidence lockers for the SSP
        evidence_items = get_evidence_by_security_plan(api, ssp_id)

        if evidence_items:
            logger.info(f"Found {len(evidence_items)} evidence items from evidence lockers for SSP {ssp_id}")

            for evidence_item in evidence_items:
                file_name = evidence_item.get("trustedDisplayName", f"evidence_{evidence_item.get('id', 'unknown')}")
                output_path = module_folder / file_name

                if download_evidence_file(api, evidence_item, str(output_path)):
                    logger.info(f"Downloaded evidence file: {file_name}")
                else:
                    logger.warning(f"Failed to download evidence file: {file_name}")
        else:
            logger.info("No evidence found in evidence lockers for SSP")

    except Exception as e:
        logger.warning(f"Error processing SSP evidence lockers: {e}")


def _download_files_for_parent(
    parent_id: int, parent_module: str, output_folder: Path, api: Api, module_name: str = None
) -> None:
    """
    Generalized function to download files for any parent module

    :param int parent_id: Parent ID (component, control, etc.)
    :param str parent_module: Parent module name (components, controls, etc.)
    :param Path output_folder: Path to output folder
    :param Api api: API object
    :param str module_name: Human-readable module name for logging (optional)
    :rtype: None
    """
    if module_name is None:
        module_name = parent_module

    try:
        # Use File model method instead of direct API call
        files_data = File.get_files_for_parent_from_regscale(api=api, parent_id=parent_id, parent_module=parent_module)

        for file_item in files_data:
            file_name = file_item.trustedDisplayName or f"file_{file_item.id}"
            output_path = output_folder / file_name

            try:
                file_data = File.download_file_from_regscale_to_memory(
                    api=api,
                    record_id=file_item.id,
                    module=parent_module,
                    stored_name=file_item.trustedStorageName,
                    file_hash=file_item.fileHash or file_item.shaHash,
                )

                if file_data is None:
                    logger.warning(f"No data received for {module_name} file {file_name}")
                    continue

                with open(output_path, "wb") as f:
                    f.write(file_data)
                logger.info(f"Downloaded {module_name} file: {file_name}")
            except Exception as e:
                logger.warning(f"Failed to download {module_name} file {file_name}: {e}")
    except Exception as e:
        logger.warning(f"Failed to get {module_name} files for {parent_module} {parent_id}: {e}")


def _download_component_files(component_id: int, component_folder: Path, api: Api) -> None:
    """
    Download files directly attached to a component

    :param int component_id: Component ID
    :param Path component_folder: Path to component folder
    :param Api api: API object
    :rtype: None
    """
    _download_files_for_parent(
        parent_id=component_id,
        parent_module="components",
        output_folder=component_folder,
        api=api,
        module_name="component",
    )


def _download_control_files(control_id: int, control_folder: Path, api: Api) -> None:
    """
    Download files for a control

    :param int control_id: Control ID
    :param Path control_folder: Path to control folder
    :param Api api: API object
    :rtype: None
    """
    _download_files_for_parent(
        parent_id=control_id, parent_module="controls", output_folder=control_folder, api=api, module_name="control"
    )


def _download_control_evidence(control_id: int, control_folder: Path, api: Api) -> None:
    """
    Download evidence from evidence lockers for a control

    :param int control_id: Control ID
    :param Path control_folder: Path to control folder
    :param Api api: API object
    :rtype: None
    """
    evidence_items = get_evidence_by_control(api, control_id)

    if evidence_items:
        logger.info(f"Found {len(evidence_items)} evidence items for control {control_folder.name}")

        for evidence_item in evidence_items:
            file_name = evidence_item.get("trustedDisplayName", f"evidence_{evidence_item.get('id', 'unknown')}")
            output_path = control_folder / file_name

            if download_evidence_file(api, evidence_item, str(output_path)):
                logger.info(f"Downloaded evidence file: {file_name}")
            else:
                logger.warning(f"Failed to download evidence file: {file_name}")


def _process_component_controls(component_id: int, component_folder: Path, api: Api) -> None:
    """
    Process controls for a component

    :param int component_id: Component ID
    :param Path component_folder: Path to component folder
    :param Api api: API object
    :rtype: None
    """
    controls = get_controls_by_parent(api, component_id, "components")

    if controls:
        logger.info(f"Found {len(controls)} controls for component {component_folder.name}")

        for control in controls:
            control_id = control.get("id")
            control_name = control.get("controlId", f"Control_{control_id}")

            # Create control folder within component folder
            control_folder = component_folder / control_name
            os.makedirs(control_folder, exist_ok=True)

            # Download control files and evidence
            _download_control_files(control_id, control_folder, api)
            _download_control_evidence(control_id, control_folder, api)


def process_components_evidence(ssp_id: int, path: Path, module_folder: Path, api: Api) -> None:
    """
    Process components and their evidence

    :param int ssp_id: Security Plan ID
    :param Path path: directory for file location
    :param Path module_folder: path to module folder
    :param Api api: RegScale CLI API object
    :rtype: None
    """
    try:
        # Get components for the SSP
        components = get_components_by_ssp(api, ssp_id)

        if not components:
            logger.info("No active components found for SSP")
            return

        logger.info(f"Found {len(components)} active components for SSP {ssp_id}")

        for component in components:
            component_id = component.get("id")
            component_title = component.get("title", f"Component_{component_id}")

            # Create component folder
            component_folder = module_folder / component_title
            os.makedirs(component_folder, exist_ok=True)

            # Download component files
            _download_component_files(component_id, component_folder, api)

            # Process component controls
            _process_component_controls(component_id, component_folder, api)

    except Exception as e:
        logger.warning(f"Error processing components evidence: {e}")


def remove_directory(directory_path: Path) -> None:
    """
    This function removes a given directory even if files stored there

    :param Path directory_path: file path of directory to remove
    :rtype: None
    """
    shutil.rmtree(directory_path.absolute())
    logger.info("Temporary Evidence directory removed successfully!")


def zip_folder(folder_path: Path, zip_path: Path) -> None:
    """
    This function zips up files and folders in a given folder or directory path.

    :param Path folder_path: file path of evidence folder
    :param Path zip_path: file path for zip location of evidence folder
    :rtype: None
    """
    # Create a ZIP file object in write mode
    with zipfile.ZipFile(zip_path.absolute(), "w", zipfile.ZIP_DEFLATED) as zipf:
        # Iterate over all the files and subfolders in the given folder
        for root, dirs, files in os.walk(folder_path.absolute()):
            for file in files:
                # Get the absolute path of the current file
                file_path = os.path.join(root, file)
                # Get the relative path of the current file within the folder
                relative_path = os.path.relpath(file_path, folder_path.absolute())  # type: ignore
                # Add the file to the ZIP archive using its relative path
                zipf.write(file_path, relative_path)  # type: ignore

    logger.info("Folder zipped successfully!")


def remove(list_to_review: list) -> list:
    """
    Remove items that start with "."

    :param list list_to_review: list of items to review
    :return: copied list with items removed
    :rtype: list
    """
    copy_list = list_to_review.copy()
    # loop through folder/file list
    for item in list_to_review:
        # if the folder or file starts with '.'
        if item.startswith("."):
            # remove the item from the list
            copy_list.remove(item)
    return copy_list


def delta(time: datetime) -> int:
    """
    Calculates the days between provided datetime object and the datetime function was called

    :param datetime time:
    :return: # of days difference between provided date and datetime function was called
    :rtype: int
    """
    # find time difference between dates
    diff = datetime.now() - time
    # return the difference in integer days
    return diff.days


def calc_score(number: int, score_data: Tuple[list[int], list[int], list[int]]) -> int:
    """
    calculate score

    :param int number: Index in list
    :param Tuple[list[int], list[int], list[int]] score_data: List of scores
    :return: Test score
    :rtype: int
    """
    # bring in score lists
    true_scores = score_data[0]
    total_scores = score_data[2]
    # set score values
    true_score = true_scores[number]
    total_score = total_scores[number]
    # calculate test score for this result and check for zero division
    return int((true_score / total_score) * 100) if int(total_score) != 0 else 0


def find_signatures(file: str) -> int:
    """
    Determine if the file is digitally signed

    :param str file: file path
    :return: # of signatures found
    :rtype: int
    """
    import pymupdf

    number = 0
    # if the file is a pdf document
    if file.endswith(".pdf"):
        try:
            # open the document
            doc = pymupdf.open(file)
        except pymupdf.FileNotFoundError:
            # set sig flag equal to 0
            number = 0
            logger.warning("no such file %s .", file)
        else:
            # determine if document is digitally signed
            number = doc.get_sigflags()
        # if the sig flag is equal to 3
        if number == 3:
            logger.info("%s has signature fields and has been digitally signed.", file)
        # if the sig flag is equal to 1
        elif number == 1:
            logger.info("%s has signature fields, but has not been digitally signed.", file)
        # if the sig flag is equal to -1
        elif number == -1:
            logger.info("%s has no signature fields to hold a digital signature.", file)
    # if the file is a docx document
    if not file.endswith(".pdf"):
        # set sig flag equal to 0
        number = 0
        logger.warning("%s is not a pdf document.", file)

    # return variable for use outside of local scope
    return number


def set_directory_variables(task: TaskID, evidence_folder: str, progress: Progress) -> Tuple[str, str, str]:
    """
    Set evidence folder directory variables

    :param TaskID task: The task to update on the job_progress
    :param str evidence_folder: File path to evidence folder
    :param Progress progress: Progress object
    :return: Tuple[evidence folder path, directory name, new working directory]
    :rtype: Tuple[str, str, str]
    """
    # set evidence folder variable to init.yaml value
    # if evidence folder does not exist then create it so tests will pass
    check_file_path(evidence_folder)

    # if evidence folder does not exist or if it is empty then error out
    evidence_items = os.listdir(evidence_folder)

    if evidence_folder is None or len(evidence_items) == 0:
        error_and_exit("The directory set to evidenceFolder cannot be found or is empty.")
    else:
        # otherwise change directory to the evidence folder
        os.chdir(evidence_folder)
    progress.update(task, advance=1)

    # include RegScale projects folder or use current directory if no subdirs
    subdirs = [filename for filename in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(), filename))]

    if subdirs:
        # Prefer 'project' directory if it exists, otherwise use the first one
        if "project" in subdirs:
            dir_name = "project"
        else:
            dir_name = subdirs[0]
        new_cwd = os.getcwd() + os.sep + dir_name
    else:
        dir_name = "evidence"
        new_cwd = os.getcwd()
    progress.update(task, advance=1)
    # return variables for use outside local scope
    return evidence_folder, dir_name, new_cwd


def parse_required_docs(evidence_folder: str, task: TaskID, progress: Progress) -> Tuple[list[dict], set[str]]:
    """
    build a list of the required documents from config.json

    :param str evidence_folder:
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Tuple[required_docs, document_list]
    :rtype: Tuple[list[dict], set[str]]
    """
    # create an empty list to hold a list of all document requirements for the assessment
    required_docs = []
    progress.update(task, advance=1)
    # create an empty list to hold a list of all required documents
    document_list = set()
    progress.update(task, advance=1)
    # open app//evidence//config.json file and read contents
    config_file = f"{evidence_folder}{os.sep}config.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as json_file:
            # load json object into a readable dictionary
            rules = json.load(json_file)
            progress.update(task, advance=1)
            # loop through required document dicts
            for i in range(len(rules.get("required-documents", []))):
                # add to a list of dictionaries for parsing
                required_docs.append(
                    {
                        "file-name": rules["required-documents"][i].get("file-name"),
                        "last-updated-by": rules["required-documents"][i].get("last-updated-by"),
                        "signatures-required": rules["required-documents"][i].get("signatures-required"),
                        "signature-count": rules["required-documents"][i].get("signature-count"),
                    }
                )
                # update contents of list if it does not already exist
                document_list.add(rules["required-documents"][i].get("file-name"))
    else:
        # No config file, use default requirements for any files found
        progress.update(task, advance=1)
        # Get all files in evidence folder and subfolders
        for root, dirs, files in os.walk(evidence_folder):
            for file in files:
                if not file.startswith(".") and file.lower().endswith((".pdf", ".docx", ".doc", ".txt")):
                    required_docs.append(
                        {
                            "file-name": file,
                            "last-updated-by": 365,
                            "signatures-required": False,
                            "signature-count": 0,
                        }
                    )
                    document_list.add(file)
    progress.update(task, advance=1)
    # return variables for use outside of local scope
    return required_docs, document_list


def get_doc_timestamps(evidence_folder: str, directory: str, task: TaskID, progress: Progress) -> list[dict]:
    """
    Get each file's last modified time

    :param str evidence_folder: File path to evidence folder
    :param str directory: File path to directory
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: list of dictionaries
    :rtype: list[dict]
    """
    # create empty list to hold file modified times
    modified_times: list[dict] = []
    progress.update(task, advance=1)
    # get list of folders in parent folder
    folders_list = os.listdir(evidence_folder)
    progress.update(task, advance=1)
    # remove any child folders that start with '.'
    new_folders = remove(list_to_review=folders_list)
    progress.update(task, advance=1)

    # Check if there are subdirectories
    subdirs = [f for f in new_folders if os.path.isdir(os.path.join(evidence_folder, f))]

    if subdirs:
        # loop through directory listing
        for folder in subdirs:
            # get list of files in each folder
            filelist = os.listdir(os.path.join(evidence_folder, folder))
            # remove any files that start with '.'
            filelist = remove(filelist)
            # loop through list of files in each folder
            modified_times.extend(
                {
                    "program": folder,
                    "file": filename,
                    "last-modified": os.path.getmtime(os.path.join(directory, folder, filename)),
                }
                for filename in filelist
            )
    else:
        # No subdirectories, process files directly in evidence folder
        files = [f for f in new_folders if os.path.isfile(os.path.join(evidence_folder, f))]
        files = remove(files)
        modified_times.extend(
            {
                "program": "evidence",
                "file": filename,
                "last-modified": os.path.getmtime(os.path.join(evidence_folder, filename)),
            }
            for filename in files
        )
    progress.update(task, advance=1)
    # loop through the list of timestamps
    for i, time_data in enumerate(modified_times):
        # update the last-modified value to be the count of days
        modified_times[i].update({"last-modified": delta(time=datetime.fromtimestamp(time_data["last-modified"]))})
    progress.update(task, advance=1)
    # return variable for use outside local scope
    return modified_times


def set_required_texts(evidence_folder: str, task: TaskID, progress: Progress) -> set[str]:
    """
    parse config.json file and build a list of the required texts for the assessment

    :param str evidence_folder: File path to evidence folder
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Required text
    :rtype: set[str]
    """
    # create an empty set to hold all unique required texts for the assessment
    required_text = set()
    progress.update(task, advance=1)
    # open app//evidence//config.json file and read contents
    config_file = f"{evidence_folder}{os.sep}config.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as json_file:
            # load json object into a readable dictionary
            rules = json.load(json_file)
            progress.update(task, advance=1)
            # create iterator to traverse dictionary
            for i in range(len(rules.get("rules-engine", []))):
                # pull out required text to look for from config
                for items in rules["rules-engine"][i].get("text-to-find", []):
                    # exclude duplicate text to search from required text
                    required_text.add(items)
    else:
        # No config file, use default text requirements
        progress.update(task, advance=1)
        required_text = {"security policy", "risk assessment", "compliance", "control", "audit"}
    # return variable for use outside of local scope
    return required_text


def find_required_files_in_folder(evidence_folder: str, task: TaskID, progress: Progress) -> list[dict]:
    """
    Pull out required files from each directory for parsing

    :param str evidence_folder: File path to evidence folder
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of directories
    :rtype: list[dict]
    """
    # create empty list to hold list of files in directory
    dir_list: list[dict] = []
    progress.update(task, advance=1)
    # build a list of all folders to iterate through
    folder_list = os.listdir(evidence_folder)
    progress.update(task, advance=1)
    # remove any folders starting with '.' from list
    new_folders_list = remove(folder_list)
    progress.update(task, advance=1)

    # Check if there are subdirectories
    subdirs = [f for f in new_folders_list if os.path.isdir(os.path.join(evidence_folder, f))]

    if subdirs:
        for folder in subdirs:
            # build a list of all files contained in sub-directories
            filelist = os.listdir(evidence_folder + os.sep + folder)
            # remove folders and file names that start with a .
            filelist = remove(filelist)
            dir_list.extend({"program": folder, "file": filename} for filename in filelist)
    else:
        # No subdirectories, process files directly in evidence folder
        files = [f for f in new_folders_list if os.path.isfile(os.path.join(evidence_folder, f))]
        files = remove(files)
        dir_list.extend({"program": "evidence", "file": filename} for filename in files)
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return dir_list


def _create_signature_result(program: str, filename: str, test_name: str, result: bool) -> dict:
    """Helper function to create signature assessment result"""
    return {
        "program": program,
        "file": filename,
        "test": test_name,
        "result": result,
    }


def _assess_signature_requirement(doc_file: dict, required: dict) -> list[dict]:
    """Helper function to assess signature requirements for a document"""
    results = []

    if required["signatures-required"] is True:
        sig_result = find_signatures(doc_file["file"])
        test_name = "signature-required"
        result = sig_result == 3
        results.append(_create_signature_result(doc_file["program"], doc_file["file"], test_name, result))
    elif required["signatures-required"] is False:
        test_name = "signature-required (not required)"
        results.append(_create_signature_result(doc_file["program"], doc_file["file"], test_name, True))

    return results


def signature_assessment_results(
    directory: list[dict], r_docs: list[dict], task: TaskID, progress: Progress
) -> list[dict]:
    """
    Compares signature config parameter against signature detection

    :param list[dict] directory: List of directories
    :param list[dict] r_docs: List of documents
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Assessment of signatures
    :rtype: list[dict]
    """
    sig_assessments: list[dict] = []
    progress.update(task, advance=1)

    for doc_file in directory:
        for required in r_docs:
            if doc_file["file"] == required["file-name"]:
                sig_assessments.extend(_assess_signature_requirement(doc_file, required))

    progress.update(task, advance=1)
    return sig_assessments


def document_assessment_results(
    directory: list[dict], documents: set[str], task: TaskID, progress: Progress
) -> list[dict]:
    """
    Test if required documents are present in each directory

    :param list[dict] directory: List of directories
    :param set[str] documents: List of documents
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of assessments of provided documents in the provided directory
    :rtype: list[dict]
    """
    # create empty list to hold assessment results
    doc_assessments: list[dict] = []
    progress.update(task, advance=1)
    # loop through list of found documents in each sub-folder
    for doc_file in directory:
        # if the file in the sub-folder is in the required documents list
        if doc_file["file"] in documents:
            # append a true result for each file in each program
            doc_assessments.append(
                {
                    "program": doc_file["program"],
                    "file": doc_file["file"],
                    "test": "required-documents",
                    "result": True,
                }
            )
        else:
            # append a false result for each file in each program
            doc_assessments.append(
                {
                    "program": doc_file["program"],
                    "file": doc_file["file"],
                    "test": "required-documents",
                    "result": False,
                }
            )
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return doc_assessments


def _extract_docx_text(file_path: str) -> list[str]:
    """Helper function to extract text from DOCX files"""
    document = Document(file_path)
    return [para.text for para in document.paragraphs]


def _extract_pdf_text(file_path: str) -> list[str]:
    """Helper function to extract text from PDF files"""
    output_text_list: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:  # Only append non-None text
                output_text_list.append(text)
    return output_text_list


def _process_file_for_text(filename: str, file_path: str, program: str) -> dict | None:
    """Helper function to process a single file and extract text"""
    if filename.endswith(".docx"):
        text = _extract_docx_text(file_path)
    elif filename.endswith(".pdf"):
        text = _extract_pdf_text(file_path)
    else:
        return None

    return {"program": program, "file": filename, "text": text}


def _process_files_in_folder(folder_path: str, program: str) -> list[dict]:
    """Helper function to process all files in a specific folder"""
    results = []
    file_list = os.listdir(folder_path)
    file_list = remove(file_list)

    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        result = _process_file_for_text(filename, file_path, program)
        if result:
            results.append(result)

    return results


def parse_required_text_from_files(evidence_folder: str, task: TaskID, progress: Progress) -> list[dict]:
    """
    Parse text from docx/pdf file and hold strings representing required text to test

    :param str evidence_folder: File path to the evidence folder
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Results of text found for the files
    :rtype: list[dict]
    """
    full_text: list[dict] = []
    progress.update(task, advance=1)

    folder_list = os.listdir(evidence_folder)
    progress.update(task, advance=1)
    removed_folders_list = remove(folder_list)
    progress.update(task, advance=1)

    # Check if there are subdirectories
    subdirs = [f for f in removed_folders_list if os.path.isdir(os.path.join(evidence_folder, f))]

    if subdirs:
        for folder in subdirs:
            folder_path = os.path.join(evidence_folder, folder)
            full_text.extend(_process_files_in_folder(folder_path, folder))
    else:
        # No subdirectories, process files directly in evidence folder
        full_text.extend(_process_files_in_folder(evidence_folder, "evidence"))

    progress.update(task, advance=1)
    return full_text


def text_string_search(f_texts: list[dict], req_texts: set[str], task: TaskID, progress: Progress) -> list[dict]:
    """
    Search for required texts in document paragraphs

    :param list[dict] f_texts: List of documents
    :param set[str] req_texts: Required text
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Results of searched text in documents
    :rtype: list[dict]
    """
    # create empty list to hold assessment results
    search_list: list[dict] = []
    progress.update(task, advance=1)
    # iterate through each sentence in the required texts
    for parsed_file, line in itertools.product(f_texts, req_texts):
        # if the required text appears in the parsed paragraph
        if any(line in text for text in parsed_file["text"]):
            # then create a "True" entry in the empty list
            search_list.append(
                {
                    "program": parsed_file["program"],
                    "file": parsed_file["file"],
                    "text": line,
                    "result": True,
                }
            )
        else:
            # else create a "False" entry in the empty list
            search_list.append(
                {
                    "program": parsed_file["program"],
                    "file": parsed_file["file"],
                    "text": line,
                    "result": False,
                }
            )
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return search_list


def text_assessment_results(searches: list[dict], r_texts: set[str], task: TaskID, progress: Progress) -> list[dict]:
    """
    Test if required text is present in required files and return test assessment

    :param list[dict] searches: List of results
    :param set[str] r_texts: Required text
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of results
    :rtype: list[dict]
    """
    # create empty list to hold assessment results
    text_results: list[dict] = []
    progress.update(task, advance=1)
    # loop through text string search results
    for result, line in itertools.product(searches, r_texts):
        # if the text matches the required text
        if result["text"] == line and result["result"] is True:
            text_info = result["text"]
            # condense results into 1 per file
            text_results.append(
                {
                    "program": result["program"],
                    "file": result["file"],
                    "test": f"required-text ({text_info})",
                    "result": result["result"],
                }
            )
    # return variable for use outside of local scope
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return text_results


def gather_test_project_data(api: Api, evidence_folder: str, task: TaskID, progress: Progress) -> list[dict]:
    """
    Gather information from evidence test projects created in RegScale to catch data

    :param Api api: API object
    :param str evidence_folder: File path to evidence folder
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of results
    :rtype: list[dict]
    """
    # create empty list to hold project test data from GET API call
    test_data: list[dict] = []
    progress.update(task, advance=1)
    # test project information created in RegScale UI
    list_file = evidence_folder + os.sep + "list.json"
    if os.path.exists(list_file):
        with open(list_file, "r", encoding="utf-8") as json_file:
            # load json object into a readable dictionary
            lists = json.load(json_file)
            # loop through projects in the list.json
            test_data.extend(
                {
                    "id": lists["parser-list"][i].get("id"),
                    "program": lists["parser-list"][i].get("folder-name"),
                }
                for i in range(len(lists.get("parser-list", [])))
            )
    else:
        # No list.json, skip project data - evidence collection can work without it
        test_data = []
    progress.update(task, advance=1)
    # create empty list to hold json response data for each project
    test_info: list[dict] = []
    # iterate through test projects and make sequential GET API calls
    for item in test_data:
        # make a GET request for each project
        if project := Project.get_object(item["id"]):
            api.logger.info("Project data retrieval was successful.")
            # save the json response data
            test_info.append(
                {
                    "id": project.id,
                    "title": project.title,
                    "uuid": project.uuid,
                    "projectmanagerid": project.projectmanagerid,
                    "parentid": project.parentId,
                    "parentmodule": project.parentModule,
                    "program": project.program,
                }
            )
        else:
            api.logger.warning(f"Project data retrieval was unsuccessful for ID {item['id']}, skipping this project.")
    progress.update(task, advance=1)
    # return variables for use outside of local scope
    return test_info


def assess_doc_timestamps(
    timestamps: list[dict], documents: list[dict], task: TaskID, progress: Progress
) -> list[dict]:
    """
    Test file modification times

    :param list[dict] timestamps: list of modified timestamps
    :param list[dict] documents: list of documents
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of documents sorted by modified date
    :rtype: list[dict]
    """
    # create empty list to store test results
    assessed_timestamps = []
    progress.update(task, advance=1)
    # loop through timestamps
    for items in timestamps:
        # loop through required documents
        for doc_items in documents:
            # if file names match between the list of dicts
            if fnmatch.fnmatch(items["file"], doc_items["file-name"]):
                # if the required modification time is less than the last modified days
                if items["last-modified"] < doc_items["last-updated-by"]:
                    # append true result to the list of dicts
                    assessed_timestamps.append(
                        {
                            "program": items["program"],
                            "file": items["file"],
                            "test": "last-updated-by",
                            "result": True,
                        }
                    )
                else:
                    # append false results to the list of dicts
                    assessed_timestamps.append(
                        {
                            "program": items["program"],
                            "file": items["file"],
                            "test": "last-updated-by",
                            "result": False,
                        }
                    )
    progress.update(task, advance=1)
    # return variables for use outside of local scope
    return assessed_timestamps


def assessments_report(
    docres: list[dict],
    textres: list[dict],
    timeres: list[dict],
    sigres: list[dict],
    task: TaskID,
    progress: Progress,
) -> list[dict]:
    """
    Function that builds the assessment report for all results

    :param list[dict] docres: List of document results
    :param list[dict] textres: List of text results
    :param list[dict] timeres: List of time results
    :param list[dict] sigres: List of signature results
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of assessment report for all results
    :rtype: list[dict]
    """
    progress.update(task, advance=1)
    # combine all results into one master list
    return docres + textres + timeres + sigres


def build_assessment_dataframe(assessments: list[dict], task: TaskID, progress: Progress) -> list[dict]:
    """
    Build dataframe for assessment results

    :param list[dict] assessments: List of results
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of results containing panda's data frames
    :rtype: list[dict]
    """
    # build out dataframe for score calculations
    import pandas as pd  # Optimize import performance

    result_df = pd.DataFrame(assessments)
    progress.update(task, advance=1)

    # Check if dataframe is empty
    if result_df.empty:
        return []

    # fill in NaN cells
    result_df = result_df.fillna(" ")
    progress.update(task, advance=1)
    # loop through the program column and split based on values
    dfs = [d for _, d in result_df.groupby("program")]
    # create an empty list to store dataframe results
    result_list: list[dict] = []
    progress.update(task, advance=1)
    # loop through dataframes
    for dfr in dfs:
        # pull out unique value counts for true
        true_counts = dfr["result"].value_counts()
        true_counts = dict(true_counts)
        # pull out unique value counts for false
        false_counts = dfr["result"].value_counts()
        false_counts = dict(false_counts)
        # create ints to hold count values
        pass_count: int
        fail_count: int
        pass_count = 0
        fail_count = 0
        # loop through true_counts list
        for i in true_counts:
            # if value is true
            if i is True:
                # set equal to pass value
                pass_count = true_counts[i]
            if i is False:
                # set equal to fail value
                fail_count = false_counts[i]
        # output results to list of results
        result_list.append(
            {
                "program": dfr["program"].iloc[0],
                "true": max(pass_count, 0),
                "false": max(fail_count, 0),
                "total": len(dfr),
            }
        )
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return result_list


def build_score_data(
    assessments: list[dict], task: TaskID, progress: Progress
) -> Tuple[list[int], list[int], list[int]]:
    """
    Build assessment score lists

    :param list[dict] assessments: list of assessments to build scores
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: Tuple[list of integers of true list, list of integers of false list, list of integers of total list]
    :rtype: Tuple[list[int], list[int], list[int]]
    """
    # create empty lists to hold true/false counts
    true_list: list[int] = []
    progress.update(task, advance=1)
    false_list: list[int] = []
    progress.update(task, advance=1)
    total_list: list[int] = []
    progress.update(task, advance=1)
    # loop through assessment report data
    for item in assessments:
        # append true/false/total values to lists
        true_list.append(item["true"])
        false_list.append(item["false"])
        total_list.append(item["total"])
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return true_list, false_list, total_list


def build_html_table(assessments: list[dict], task: TaskID, progress: Progress) -> list[dict]:
    """
    This wil be a dictionary to html table conversion

    :param list[dict] assessments: List of file assessments
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :return: List of assessments with HTML formatted data tables
    :rtype: list[dict]
    """
    import pandas as pd  # Optimize import performance

    output_list: list[dict] = []

    # Check if assessments is empty
    if not assessments:
        progress.update(task, advance=4)  # Skip all remaining progress updates
        return output_list

    # create a dataframe of a list of dicts
    table_df = pd.DataFrame(data=assessments)
    progress.update(task, advance=1)

    # Check if dataframe is empty or missing required columns
    if table_df.empty or "program" not in table_df.columns:
        progress.update(task, advance=3)  # Skip remaining progress updates
        return output_list

    # fill in N/A cells with blank string
    table_df = table_df.fillna(" ")
    progress.update(task, advance=1)
    # split dataframe into list of dataframes
    dfs = [d for _, d in table_df.groupby("program")]
    progress.update(task, advance=1)
    # loop through dataframes
    for table_df in dfs:
        # output dataframe to an HTML table
        output = table_df.to_html()
        progress.update(task, advance=1)
        # replace false values with inline styling conditional to red colors for False values
        output = output.replace("<td>False</td>", '<td style="color:red;">False</td>')
        progress.update(task, advance=1)
        # replace true values with inline styling conditional to green colors for True values
        output = output.replace("<td>True</td>", '<td style="color:green;">True</td>')
        progress.update(task, advance=1)
        # build list of outputs to loop through for API POST calls
        output_list.append({"program": table_df["program"].iloc[0], "html": output})
    progress.update(task, advance=1)
    # return variable for use outside of local scope
    return output_list


def create_child_assessments(
    api: Api,
    project_data: list[dict],
    output: list[dict],
    score_data: Tuple[list[int], list[int], list[int]],
    task: TaskID,
    progress: Progress,
) -> None:
    """
    Create assessments based on results of text parsing tests into RegScale via API

    :param Api api: API object
    :param list[dict] project_data: list of results to part and upload to RegScale
    :param list[dict] output: HTML output of the results
    :param Tuple[list[int], list[int], list[int]] score_data: list of scores
    :param TaskID task: The task to update on the job_progress
    :param Progress progress: Progress object
    :rtype: None
    """
    # set completion datetime to required format
    completion_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    progress.update(task, advance=1)

    # Check if we have project data to work with
    if not project_data:
        progress.update(task, advance=1)
        return

    # loop through test projects and make an API call for each
    for i, project in enumerate(project_data):
        # call score calculation function
        test_score = calc_score(i, score_data)
        # if file name matches html output table program name
        if project_data[i]["program"] == output[i]["program"]:
            # build assessment data
            assessment_data = Assessment(
                status="Complete",
                leadAssessorId=api.config["userId"],
                title="Evidence Collection Automation Assessment",
                assessmentType="Inspection",
                projectId=project["id"],
                parentId=project["id"],
                parentModule="projects",
                assessmentReport=output[i]["html"],
                assessmentPlan="Review automated results of evidence collection tests",
                createdById=api.config["userId"],
                lastUpdatedById=api.config["userId"],
                complianceScore=test_score,
                plannedFinish=completion_date,
                plannedStart=completion_date,
                actualFinish=completion_date,
            )
            # if all tests passed above score update POST call information
            if test_score >= api.config["passScore"]:
                # update assessment data API body information
                assessment_data.assessmentResult = "Pass"
            # if all tests failed below score update POST call information
            elif test_score <= api.config["failScore"]:
                # update assessment data API body information
                assessment_data.assessmentResult = "Fail"
                # if some tests passed in between score update POST call information
            else:
                # update assessment data API body information
                assessment_data.assessmentResult = "Partial Pass"
            if assessment_data.create():
                api.logger.info("Child assessment creation was successful.")
            else:
                api.logger.warning("Child assessment creation was not successful.")
    progress.update(task, advance=1)
