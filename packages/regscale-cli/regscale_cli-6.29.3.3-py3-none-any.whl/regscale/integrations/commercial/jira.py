#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jira integration for RegScale CLI"""

# Standard python imports
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union, Literal
from urllib.parse import urljoin

if TYPE_CHECKING:
    from regscale.core.app.application import Application

import click
from jira import JIRA
from jira import Issue as jiraIssue
from jira import JIRAError
from rich.progress import Progress

from regscale.core.app.utils.parser_utils import safe_datetime_str
from regscale.core.app.api import Api
from regscale.core.app.logz import create_logger
from regscale.core.app.utils.app_utils import (
    check_file_path,
    check_license,
    compute_hashes_in_directory,
    convert_datetime_to_regscale_string,
    create_progress_object,
    error_and_exit,
    get_current_datetime,
    save_data_to,
)
from regscale.core.app.utils.regscale_utils import verify_provided_module
from regscale.models import regscale_id, regscale_module
from regscale.models.regscale_models.file import File
from regscale.models.regscale_models.issue import Issue
from regscale.models.regscale_models.task import Task
from regscale.integrations.variables import ScannerVariables

job_progress = create_progress_object()
logger = create_logger()
update_issues: list[Any] = []
new_regscale_issues: list[Any] = []
updated_regscale_issues: list[Any] = []
update_counter: list[int] = []


####################################################################################################
#
# PROCESS ISSUES TO JIRA
# JIRA CLI Python Docs: https://jira.readthedocs.io/examples.html#issues
# JIRA API Docs: https://developer.atlassian.com/server/jira/platform/jira-rest-api-examples/
#
####################################################################################################


# Create group to handle Jira integration
@click.group()
def jira():
    """Sync issues between Jira and RegScale."""


@jira.command()  # type: ignore[misc]
@regscale_id()
@regscale_module()
@click.option(
    "--jira_project",
    type=click.STRING,
    help="RegScale will sync the issues for the record to the Jira project.",
    prompt="Enter the name of the project in Jira",
    required=True,
)
@click.option(
    "--jira_issue_type",
    type=click.STRING,
    help="Enter the Jira issue type to use when creating new issues from RegScale. (CASE SENSITIVE)",
    prompt="Enter the Jira issue type",
    required=True,
)
@click.option(
    "--sync_attachments",
    type=click.BOOL,
    help=(
        "Whether RegScale will sync the attachments for the issue "
        "in the provided Jira project and vice versa. Defaults to True."
    ),
    required=False,
    default=True,
)
@click.option(
    "--token_auth",
    "-t",
    is_flag=True,
    help="Use token authentication for Jira API instead of basic auth, defaults to False.",
)
@click.option(
    "--jql",
    type=click.STRING,
    help="Custom JQL query for filtering Jira issues.",
    required=False,
)
@click.option(
    "--poams",
    "-p",
    is_flag=True,
    help="Whether to create/update the incoming issues from Jira as POAMs in RegScale.",
)
def issues(
    regscale_id: int,
    regscale_module: str,
    jira_project: str,
    jira_issue_type: str,
    sync_attachments: bool = True,
    token_auth: bool = False,
    jql: Optional[str] = None,
    poams: bool = False,
):
    """Sync issues from Jira into RegScale."""
    sync_regscale_and_jira(
        parent_id=regscale_id,
        parent_module=regscale_module,
        jira_project=jira_project,
        jira_issue_type=jira_issue_type,
        sync_attachments=sync_attachments,
        token_auth=token_auth,
        jql=jql,
        use_poams=poams,
    )


@jira.command()  # type: ignore[misc]
@regscale_id()
@regscale_module()
@click.option(
    "--jira_project",
    type=click.STRING,
    help="RegScale will sync the issues for the record to the Jira project.",
    prompt="Enter the name of the project in Jira",
    required=True,
)
@click.option(
    "--sync_attachments",
    type=click.BOOL,
    help=(
        "Whether RegScale will sync the attachments for the issue "
        "in the provided Jira project and vice versa. Defaults to True."
    ),
    required=False,
    default=True,
)
@click.option(
    "--token_auth",
    "-t",
    is_flag=True,
    help="Use token authentication for Jira API instead of basic auth, defaults to False.",
)
@click.option(
    "--jql",
    type=click.STRING,
    help="Custom JQL query for filtering Jira tasks.",
    required=False,
)
def tasks(
    regscale_id: int,
    regscale_module: str,
    jira_project: str,
    sync_attachments: bool = True,
    token_auth: bool = False,
    jql: Optional[str] = None,
):
    """Sync tasks from Jira into RegScale."""
    sync_regscale_and_jira(
        parent_id=regscale_id,
        parent_module=regscale_module,
        jira_project=jira_project,
        jira_issue_type="Task",
        sync_attachments=sync_attachments,
        sync_tasks_only=True,
        token_auth=token_auth,
        jql=jql,
    )


def get_regscale_data_and_attachments(
    parent_id: int, parent_module: str, sync_attachments: bool = True, sync_tasks_only: bool = False
) -> Tuple[list[Union[Issue, Task]], dict[int, list[File]]]:
    """
    Get the RegScale data and attachments for the given parent ID and module

    :param int parent_id: The ID of the parent
    :param str parent_module: The module of the parent
    :param bool sync_attachments: Whether to sync attachments
    :param bool sync_tasks_only: Whether to sync tasks only
    :return: Tuple of RegScale issues, RegScale attachments
    :rtype: Tuple[list[Union[Issue, Task]], dict[int, list[File]]]
    """
    regscale_attachments: dict[int, list[File]] = {}
    regscale_issues: list[Union[Issue, Task]]

    if sync_tasks_only and sync_attachments:
        regscale_issues, regscale_attachments = Task.get_objects_and_attachments_by_parent(
            parent_id=parent_id,
            parent_module=parent_module,
        )
    elif sync_tasks_only and not sync_attachments:
        regscale_issues = Task.get_all_by_parent(parent_id, parent_module)
    elif sync_attachments:
        regscale_issues, regscale_attachments = Issue.get_objects_and_attachments_by_parent(
            parent_id=parent_id,
            parent_module=parent_module,
        )
    else:
        regscale_issues = Issue.get_all_by_parent(parent_id, parent_module)
    return regscale_issues, regscale_attachments


def sync_regscale_and_jira(
    parent_id: int,
    parent_module: str,
    jira_project: str,
    jira_issue_type: str,
    sync_attachments: bool = True,
    sync_tasks_only: bool = False,
    token_auth: bool = False,
    jql: Optional[str] = None,
    use_poams: Optional[bool] = False,
) -> None:
    """
    Sync issues, bidirectionally, from Jira into RegScale as issues

    :param int parent_id: ID # from RegScale to associate issues with
    :param str parent_module: RegScale module to associate issues with
    :param str jira_project: Name of the project in Jira
    :param str jira_issue_type: Type of issues to sync from Jira
    :param bool sync_attachments: Whether to sync attachments in RegScale & Jira, defaults to True
    :param bool sync_tasks_only: Whether to sync only tasks from Jira, defaults to False
    :param bool token_auth: Use token authentication for Jira API, defaults to False
    :param Optional[str] jql: Custom JQL query for filtering Jira issues/tasks, defaults to None
    :param Optional[bool] use_poams: Whether to mark the incoming issues as POAMs in RegScale, defaults to False
    :rtype: None
    """
    app = check_license()
    api = Api()
    config = app.config

    # Load custom fields configuration from init.yaml
    if custom_fields := config.get("jiraCustomFields", {}):
        logger.info("Custom field mappings loaded from config: %s", custom_fields)
    else:
        logger.debug("No custom field mappings found in configuration")

    # see if provided RegScale Module is an accepted option
    verify_provided_module(parent_module)

    # create Jira client
    jira_client = create_jira_client(config, token_auth)

    # Use custom JQL if provided, otherwise build default JQL
    if jql:
        jql_str = jql
    else:
        jql_str = (
            f"project = '{jira_project}' AND issueType = '{jira_issue_type}'"
            if sync_tasks_only
            else f"project = '{jira_project}'"
        )
    regscale_objects, regscale_attachments = get_regscale_data_and_attachments(
        parent_id=parent_id,
        parent_module=parent_module,
        sync_attachments=sync_attachments,
        sync_tasks_only=sync_tasks_only,
    )

    output_str = "task" if sync_tasks_only else "issue"

    # write regscale data to a json file
    check_file_path("artifacts")
    file_name = f"existingRegScale{output_str}s.json"
    file_path = Path("./artifacts") / file_name
    save_data_to(
        file=file_path,
        data=[issue.dict() for issue in regscale_objects],
        output_log=False,
    )
    logger.info(
        "Saved RegScale %s(s) for %s #%i, see %s",
        output_str,
        parent_module,
        parent_id,
        str(file_path.absolute()),
    )

    jira_objects = fetch_jira_objects(
        jira_client=jira_client,
        jira_project=jira_project,
        jql_str=jql_str,
        jira_issue_type=jira_issue_type,
        sync_tasks_only=sync_tasks_only,
    )

    if regscale_objects:
        # sync RegScale issues to Jira
        if regscale_objects_to_update := sync_regscale_to_jira(
            regscale_objects=regscale_objects,
            jira_client=jira_client,
            jira_project=jira_project,
            jira_issue_type=jira_issue_type,
            api=api,
            sync_attachments=sync_attachments,
            attachments=regscale_attachments,
            custom_fields=custom_fields,
        ):
            for regscale_object in regscale_objects_to_update:
                regscale_object.save(bulk=True)
            if isinstance(regscale_objects[0], Issue):
                Issue.bulk_save()
            elif isinstance(regscale_objects[0], Task):
                Task.bulk_save()
    else:
        logger.info("No %s(s) need to be updated in RegScale.", output_str)

    if jira_objects:
        return sync_regscale_objects_to_jira(
            jira_objects, regscale_objects, sync_attachments, app, parent_id, parent_module, sync_tasks_only, use_poams
        )
    logger.info("No %s need to be analyzed from Jira.", output_str)


def sync_regscale_objects_to_jira(
    jira_issues: list[jiraIssue],
    regscale_objects: list[Union[Issue, Task]],
    sync_attachments: bool,
    app: "Application",
    parent_id: int,
    parent_module: str,
    sync_tasks_only: bool,
    use_poams: Optional[bool] = False,
):
    """
    Sync issues from Jira to RegScale

    :param list[jiraIssue] jira_issues: List of Jira issues to sync to RegScale
    :param list[Union[Issue, Task]] regscale_objects: List of RegScale issues or tasks to compare to Jira issues
    :param bool sync_attachments: Sync attachments from Jira to RegScale, defaults to True
    :param Application app: RegScale CLI application object
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :param bool sync_tasks_only: Whether to sync only tasks from Jira
    :param bool use_poams: Whether to create/update the incoming issues as POAMs in RegScale, defaults to False
    """
    issues_closed: list[str] = []
    with job_progress:
        type_str = "task" if sync_tasks_only else "issue"
        creating_issues = job_progress.add_task(
            f"[#f8b737]Comparing {len(jira_issues)} Jira {type_str}(s)"
            f" and {len(regscale_objects)} RegScale {type_str}(s)...",
            total=len(jira_issues),
        )
        jira_client = create_jira_client(app.config)
        if sync_tasks_only:
            tasks_inserted, tasks_updated, tasks_closed = create_and_update_regscale_tasks(
                jira_issues=jira_issues,
                existing_tasks=regscale_objects,  # type: ignore[arg-type]
                jira_client=jira_client,
                parent_id=parent_id,
                parent_module=parent_module,
                progress=job_progress,
                progress_task=creating_issues,
            )
        else:
            app.thread_manager.submit_tasks_from_list(
                create_and_update_regscale_issues,
                jira_issues,
                regscale_objects,
                use_poams,
                sync_attachments,
                jira_client,
                app,
                parent_id,
                parent_module,
                creating_issues,
                job_progress,
            )
            app.thread_manager.execute_and_verify(timeout=ScannerVariables.timeout)
        logger.info(
            "Analyzed %i Jira %s(s), created %i %s(s), updated %i %s(s), and closed %i %s(s) in RegScale.",
            len(jira_issues),
            type_str,
            len(new_regscale_issues) if not sync_tasks_only else tasks_inserted,
            type_str,
            len(updated_regscale_issues) if not sync_tasks_only else tasks_updated,
            type_str,
            len(issues_closed) if not sync_tasks_only else tasks_closed,
            type_str,
        )


def create_jira_client(
    config: dict,
    token_auth: bool = False,
) -> JIRA:
    """
    Create a Jira client to use for interacting with Jira

    :param dict config: RegScale CLI application config
    :param bool token_auth: Use token authentication for Jira API, defaults to False
    :return: JIRA Client
    :rtype: JIRA
    """
    url = config["jiraUrl"]
    token = config["jiraApiToken"]
    jira_user = config["jiraUserName"]
    if token_auth:
        return JIRA(token_auth=token, options={"server": url, "verify": ScannerVariables.sslVerify})

    # set the JIRA Url
    return JIRA(basic_auth=(jira_user, token), options={"server": url})


def convert_task_status(name: str) -> str:
    """
    Convert the task status from Jira to RegScale

    :param str name: Name of the task status in Jira
    :return: Name of the task status in RegScale
    :rtype: str
    """
    jira_regscale_map = {
        "to do": "Backlog",
        "in progress": "Open",
        "done": "Closed",
        "closed": "Closed",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
    }
    return jira_regscale_map.get(name.lower(), "Open")


def create_regscale_task_from_jira(config: dict, jira_issue: jiraIssue, parent_id: int, parent_module: str) -> Task:
    """
    Function to create a Task object from a Jira issue

    :param dict config: Application config
    :param jiraIssue jira_issue: Jira issue to create a Task object from
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :return: RegScale Task object
    :rtype: Task
    """
    description = jira_issue.fields.description
    due_date = map_jira_due_date(jira_issue, config)
    status = convert_task_status(jira_issue.fields.status.name)
    status_change_date = (
        convert_datetime_to_regscale_string(
            datetime.strptime(jira_issue.fields.statuscategorychangedate or "", "%Y-%m-%dT%H:%M:%S.%f%z")
        )
        if jira_issue.fields.statuscategorychangedate
        else None
    )
    title = jira_issue.fields.summary
    date_closed = None
    percent_complete = None
    if status == "Closed":
        date_closed = status_change_date
        percent_complete = 100

    task = Task(
        title=title,
        status=status,
        description=description,
        dueDate=due_date,
        parentId=parent_id,
        parentModule=parent_module,
        dateClosed=date_closed,
        percentComplete=percent_complete,
        otherIdentifier=jira_issue.key,
        extra_data={"jiraIssue": jira_issue},  # type: ignore
    )

    # Apply custom field mappings from Jira to RegScale
    custom_fields = config.get("jiraCustomFields", {})
    if custom_fields:
        apply_custom_fields_to_regscale_object(task, custom_fields, jira_issue)

    return task


def check_and_close_tasks(existing_tasks: list[Task], all_jira_titles: set[str]) -> list[Task]:
    """
    Function to check and close tasks that are not in Jira

    :param list[Task] existing_tasks: List of existing tasks in RegScale
    :param set[str] all_jira_titles: Set of all Jira task titles
    :return: List of tasks to close
    :rtype: list[Task]
    """
    close_tasks = []
    for task in existing_tasks:
        if task.title not in all_jira_titles and task.status != "Closed":
            task.status = "Closed"
            task.percentComplete = 100
            task.dateClosed = get_current_datetime()
            close_tasks.append(task)
    return close_tasks


def process_tasks_for_sync(
    config: dict,
    jira_issues: list[jiraIssue],
    existing_tasks: list[Task],
    parent_id: int,
    parent_module: str,
    progress: Progress,
    progress_task: Any,
) -> tuple[list[Task], list[Task], list[Task]]:
    """
    Function to create lists of Tasks that need to be created, updated, and closed in RegScale from Jira

    :param dict config: Application config
    :param list[jiraIssue] jira_issues: List of Jira issues to create or update in RegScale
    :param list[Task] existing_tasks: List of existing tasks in RegScale
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :param Progress progress: Job progress object to use for updating the progress bar
    :param Any progress_task: Task object to update the progress bar
    :return: A tuple of lists of Tasks to create, update, and close
    :rtype: tuple[list[Task], list[Task], list[Task]]
    """
    closed_statuses = ["Closed", "Cancelled"]
    insert_tasks = []
    update_tasks = []
    close_tasks = []

    # Create a map of existing tasks by their Jira key for easier lookup
    # Only include tasks that have an otherIdentifier
    existing_task_map = {
        task.otherIdentifier: task
        for task in existing_tasks
        if hasattr(task, "otherIdentifier") and task.otherIdentifier
    }

    for jira_issue in jira_issues:
        # Create a RegScale task from the Jira issue
        jira_task = create_regscale_task_from_jira(config, jira_issue, parent_id, parent_module)

        # Check if we have a matching task in RegScale
        if existing_task := existing_task_map.get(jira_issue.key):
            # Apply custom field mappings from Jira to RegScale for existing tasks
            if custom_fields := config.get("jiraCustomFields", {}):
                apply_custom_fields_to_regscale_object(existing_task, custom_fields, jira_issue)

            # Check if task is closed in Jira and needs to be closed in regscale
            if jira_task.status in closed_statuses and existing_task.status not in closed_statuses:
                existing_task.status = "Closed"
                existing_task.percentComplete = 100
                existing_task.dateClosed = safe_datetime_str(jira_issue.fields.statuscategorychangedate)
                close_tasks.append(existing_task)

            # Check if update needed
            elif (
                jira_task.title != existing_task.title
                or jira_task.description != existing_task.description
                or jira_task.status != existing_task.status
                or (jira_task.dueDate != existing_task.dueDate and jira_issue.fields.duedate)
            ):
                jira_task.id = existing_task.id  # Preserve the RegScale ID
                update_tasks.append(jira_task)
        else:
            # Task only exists in Jira - needs to be created in RegScale
            insert_tasks.append(jira_task)

        progress.update(progress_task, advance=1)

    return insert_tasks, update_tasks, close_tasks


def create_and_update_regscale_tasks(
    jira_issues: list[jiraIssue],
    existing_tasks: list[Task],
    jira_client: JIRA,
    parent_id: int,
    parent_module: str,
    progress: Progress,
    progress_task: Any,
) -> tuple[int, int, int]:
    """
    Function to create or update Tasks in RegScale from Jira

    :param list[jiraIssue] jira_issues: List of Jira issues to create or update in RegScale
    :param list[Task] existing_tasks: List of existing tasks in RegScale
    :param JIRA jira_client: Jira client to use for the request
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :param Progress progress: Job progress object to use for updating the progress bar
    :param Any progress_task: Task object to update the progress bar
    :return: A tuple of counts
    :rtype: tuple[int, int, int]
    """
    from regscale.core.app.api import Api
    from regscale.models.integration_models.jira_task_sync import TaskSync

    api = Api()
    insert_tasks, update_tasks, close_tasks = process_tasks_for_sync(
        config=api.app.config,
        jira_issues=jira_issues,
        existing_tasks=existing_tasks,
        parent_id=parent_id,
        parent_module=parent_module,
        progress=progress,
        progress_task=progress_task,
    )

    task_sync_operations: list[TaskSync] = []
    if insert_tasks:
        task_sync_operations.append(TaskSync(insert_tasks, "create"))
    if update_tasks:
        task_sync_operations.append(TaskSync(update_tasks, "update"))
    if close_tasks:
        task_sync_operations.append(TaskSync(close_tasks, "close"))
    with progress:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for task_sync_operation in task_sync_operations:
                progress_task = progress.add_task(
                    task_sync_operation.progress_message, total=len(task_sync_operation.tasks)
                )
                task_futures = {
                    executor.submit(
                        task_and_attachments_sync, operation=task_sync_operation.operation, task=task, jira_client=jira_client, api=api  # type: ignore
                    )
                    for task in task_sync_operation.tasks
                }
                for _ in as_completed(task_futures):
                    progress.update(progress_task, advance=1)
    return len(insert_tasks), len(update_tasks), len(close_tasks)


def task_and_attachments_sync(
    operation: Literal["create", "update", "close"], task: Task, jira_client: JIRA, api: Api
) -> None:
    """
    Function to create, update and close tasks as well as attachments between RegScale and Jira

    :param Literal["create", "update", "close"] operation: Operation to perform on the tasks
    :param Task task: Task to perform the operation on
    :param JIRA jira_client: Jira client to use for the request
    :param Api api: API object to use for the request
    :rtype: None
    """
    task_to_sync = None
    if operation == "create":
        task_to_sync = task.create()
    elif operation in ["update", "close"]:
        task_to_sync = task.save()
    if task_to_sync:
        compare_files_for_dupes_and_upload(
            jira_issue=task.extra_data["jiraIssue"],
            regscale_object=task_to_sync,
            jira_client=jira_client,
            api=api,
        )


def _create_new_regscale_issue(
    jira_issue: jiraIssue, app: "Application", parent_id: int, parent_module: str, is_poam: Optional[bool] = False
) -> Optional[Issue]:
    """
    Create a new RegScale issue from a Jira issue

    :param jiraIssue jira_issue: The Jira issue to create from
    :param Application app: RegScale application object
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :param bool is_poam: Whether to create the issue as a POAM in RegScale, defaults to False
    :return: The created RegScale issue or None if creation failed
    :rtype: Optional[Issue]
    """
    issue = map_jira_to_regscale_issue(
        jira_issue=jira_issue,
        config=app.config,
        parent_id=parent_id,
        parent_module=parent_module,
        is_poam=is_poam,
    )

    if regscale_issue := issue.create():
        logger.debug(
            "Created issue #%i-%s in RegScale.",
            regscale_issue.id,
            regscale_issue.title,
        )
        return regscale_issue
    else:
        logger.warning("Unable to create issue in RegScale.\nIssue: %s", issue.dict())
        return None


def _apply_custom_fields_and_update_issue(regscale_issue: Issue, app: "Application", jira_issue: jiraIssue) -> None:
    """
    Apply custom field mappings and update a RegScale issue

    :param Issue regscale_issue: The RegScale issue to update
    :param Application app: RegScale application object
    :param jiraIssue jira_issue: The Jira issue to get data from
    :rtype: None
    """
    if custom_fields := app.config.get("jiraCustomFields", {}):
        apply_custom_fields_to_regscale_object(regscale_issue, custom_fields, jira_issue)
    updated_regscale_issues.append(regscale_issue.save())


def create_and_update_regscale_issues(jira_issue: jiraIssue, *args, **_) -> None:
    """
    Function to create or update issues in RegScale from Jira

    :param jiraIssue jira_issue: Jira issue to create or update in RegScale
    :param args: Additional arguments
    :rtype: None
    """
    # set up local variables from the passed args Tuple
    (regscale_issues, use_poams, add_attachments, jira_client, app, parent_id, parent_module, task, progress) = args
    # find which records should be executed by the current thread

    regscale_issue: Optional[Issue] = next((issue for issue in regscale_issues if issue.jiraId == jira_issue.key), None)
    if regscale_issue:
        regscale_issue.isPoam = use_poams

    # Process the Jira issue based on its status and existing RegScale issue
    if jira_issue.fields.status.name.lower() == "done" and regscale_issue:
        regscale_issue.status = "Closed"
        regscale_issue.dateCompleted = get_current_datetime()
        _apply_custom_fields_and_update_issue(regscale_issue, app, jira_issue)
    elif regscale_issue:
        _apply_custom_fields_and_update_issue(regscale_issue, app, jira_issue)
    else:
        regscale_issue = _create_new_regscale_issue(jira_issue, app, parent_id, parent_module, use_poams)
        if regscale_issue:
            new_regscale_issues.append(regscale_issue)

    # Handle attachments if needed
    if add_attachments and regscale_issue and jira_issue.fields.attachment:
        compare_files_for_dupes_and_upload(
            jira_issue=jira_issue,
            regscale_object=regscale_issue,
            jira_client=jira_client,
            api=Api(),
        )

    # update progress bar
    progress.update(task, advance=1)


def sync_regscale_to_jira(
    regscale_objects: list[Union[Issue, Task]],
    jira_client: JIRA,
    jira_project: str,
    jira_issue_type: str,
    sync_attachments: bool = True,
    attachments: Optional[dict] = None,
    api: Optional[Api] = None,
    custom_fields: Optional[dict] = None,
) -> list[Union[Issue, Task]]:
    """
    Sync issues or tasks from RegScale to Jira

    :param list[Union[Issue, Task]] regscale_objects: list of RegScale issues or tasks to sync to Jira
    :param JIRA jira_client: Jira client to use for issue creation in Jira
    :param str jira_project: Jira Project to create the issues in
    :param str jira_issue_type: Type of issue to create in Jira
    :param bool sync_attachments: Sync attachments from RegScale to Jira, defaults to True
    :param Optional[dict] attachments: Dict of attachments to sync from RegScale to Jira, defaults to None
    :param Optional[Api] api: API object to download attachments, defaults to None
    :param Optional[dict] custom_fields: Custom field mappings from Jira custom fields to RegScale issue fields, defaults to None
    :return: list of RegScale issues or tasks that need to be updated
    :rtype: list[Union[Issue, Task]]
    """
    new_issue_counter = 0
    regscale_objects_to_update = []
    with job_progress:
        output_str = "issue" if jira_issue_type.lower() != "task" else "task"
        # create task to create Jira issues
        creating_issues = job_progress.add_task(
            f"[#f8b737]Verifying {len(regscale_objects)} RegScale {output_str}(s) exist in Jira...",
            total=len(regscale_objects),
        )
        for regscale_object in regscale_objects:
            if (
                isinstance(regscale_object, Issue) and (not regscale_object.jiraId or regscale_object.jiraId == "")
            ) or (
                isinstance(regscale_object, Task)
                and (not regscale_object.otherIdentifier or regscale_object.otherIdentifier == "")
            ):
                new_issue = create_issue_in_jira(
                    regscale_object=regscale_object,
                    jira_client=jira_client,
                    jira_project=jira_project,
                    issue_type=jira_issue_type,
                    add_attachments=sync_attachments,
                    attachments=attachments,
                    api=api,
                    custom_fields=custom_fields,
                )
                # log progress
                new_issue_counter += 1
                # get the Jira ID
                jira_id = new_issue.key
                # update the RegScale issue for the Jira link
                if isinstance(regscale_object, Issue):
                    regscale_object.jiraId = jira_id
                elif isinstance(regscale_object, Task):
                    regscale_object.otherIdentifier = jira_id
                # add the issue to the update_issues global list
                regscale_objects_to_update.append(regscale_object)
            job_progress.update(creating_issues, advance=1)
    # output the final result
    logger.info("%i new %s(s) opened in Jira.", new_issue_counter, output_str)
    return regscale_objects_to_update


def fetch_jira_objects(
    jira_client: JIRA,
    jira_project: str,
    jira_issue_type: str,
    jql_str: Optional[str] = None,
    sync_tasks_only: bool = False,
) -> list[jiraIssue]:
    """
    Fetch all issues from Jira for the provided project using the enhanced search API.

    :param JIRA jira_client: Jira client to use for the request
    :param str jira_project: Name of the project in Jira
    :param str jira_issue_type: Type of issue to fetch from Jira
    :param str jql_str: JQL string to use for the request, default None
    :param bool sync_tasks_only: Whether to sync only tasks from Jira, defaults to False
    :return: List of Jira issues
    :rtype: list[jiraIssue]
    """
    if sync_tasks_only:
        if not validate_issue_type(jira_client, jira_issue_type):
            logger.warning(
                "Skipping sync - issue type '%s' not available in this Jira project. No %s(s) will be synced.",
                jira_issue_type,
                "task",
            )
            return []
        output_str = "task"
    else:
        output_str = "issue"
    logger.info("Fetching %s(s) from Jira...", output_str.lower())

    # Try new API first: /rest/api/3/search/jql
    try:
        max_results = 100  # 100 is the max allowed by Jira
        jira_issues = []
        logger.debug("Attempting to use /rest/api/3/search/jql API (new Jira API endpoint)")

        # Use the new API endpoint directly via _session
        jql_query = jql_str or f"project = '{jira_project}'"
        url = f"{jira_client._options['server']}/rest/api/3/search/jql"
        params: dict[str, str | int] = {"jql": jql_query, "maxResults": max_results, "fields": "*all"}

        response = jira_client._session.get(url, params=params)  # type: ignore[arg-type]
        response.raise_for_status()
        data = response.json()

        # Convert response to Jira Issue objects
        for issue_data in data.get("issues", []):
            issue = jira_client.issue(issue_data["key"])
            jira_issues.append(issue)

        logger.info("%i Jira %s(s) retrieved.", len(jira_issues), output_str.lower())

        # Handle pagination with nextPageToken
        while "nextPageToken" in data and data["nextPageToken"]:
            params["nextPageToken"] = data["nextPageToken"]
            response = jira_client._session.get(url, params=params)  # type: ignore[arg-type]
            response.raise_for_status()
            data = response.json()

            for issue_data in data.get("issues", []):
                issue = jira_client.issue(issue_data["key"])
                jira_issues.append(issue)

            logger.info("%i Jira %s(s) retrieved (total).", len(jira_issues), output_str.lower())

        # Save artifacts file and log final result if we have issues
        if jira_issues:
            save_jira_issues(jira_issues, jira_project, jira_issue_type)
        logger.info("%i %s(s) retrieved from Jira using new search API.", len(jira_issues), output_str.lower())
        return jira_issues
    except Exception as e:
        # Catch any errors with new API and fall back to deprecated
        logger.warning("New search API failed: %s", str(e))
        logger.warning(
            "DEPRECATION NOTICE: Falling back to deprecated search API. "
            "This API will be removed by Atlassian on August 1, 2025."
        )

    try:
        return deprecated_fetch_jira_objects(
            jira_client=jira_client,
            jira_project=jira_project,
            jira_issue_type=jira_issue_type,
            jql_str=jql_str,
            output_str=output_str,
        )
    except JIRAError as e:
        error_and_exit(f"Unable to fetch issues from Jira: {e}")


def deprecated_fetch_jira_objects(
    jira_client: JIRA, jira_project: str, jira_issue_type: str, jql_str: Optional[str] = None, output_str: str = "issue"
) -> list[jiraIssue]:
    """
    Fetch all issues from Jira for the provided project using the old API method, used as a fallback method.

    WARNING: This method uses deprecated Jira search APIs that will be removed by Atlassian on August 1, 2025.

    :param JIRA jira_client: Jira client to use for the request
    :param str jira_project: Name of the project in Jira
    :param str jira_issue_type: Type of issue to fetch from Jira
    :param str jql_str: JQL string to use for the request, default None
    :param str output_str: String to use for logging, either "issue" or "task"
    :return: List of Jira issues
    :rtype: list[jiraIssue]
    """
    start_pointer = 0
    page_size = 100
    jira_objects: list[Any] = []
    logger.info("Fetching %s(s) from Jira using deprecated search API...", output_str.lower())
    logger.debug("Using search_issues method (deprecated - will be removed Aug 1, 2025)")
    # get all issues for the Jira project
    while True:
        start = start_pointer * page_size
        jira_issues_response = jira_client.search_issues(
            jql_str=jql_str or "",
            startAt=start,
            maxResults=page_size,
        )
        # Check if we've retrieved all issues
        total = (
            getattr(jira_issues_response, "total", len(jira_issues_response))
            if hasattr(jira_issues_response, "total")
            else len(jira_issues_response)
        )
        if len(jira_objects) == total:
            break
        start_pointer += 1
        # append new records to jira_issues
        jira_objects.extend(jira_issues_response)
        logger.info(
            "%i/%i Jira %s(s) retrieved.",
            len(jira_objects),
            total,
            output_str.lower(),
        )
    if jira_objects:
        save_jira_issues(jira_objects, jira_project, jira_issue_type)
    logger.info("%i %s(s) retrieved from Jira.", len(jira_objects), output_str.lower())
    return jira_objects


def save_jira_issues(jira_issues: list[jiraIssue], jira_project: str, jira_issue_type: str) -> None:
    """
    Save Jira issues to a JSON file in the artifacts directory

    :param list[jiraIssue] jira_issues: List of Jira issues to save
    :param str jira_project: Name of the project in Jira
    :param str jira_issue_type: Type of issue to fetch from Jira
    :rtype: None
    """
    check_file_path("artifacts")
    file_name = f"{jira_project.lower()}_existingJira{jira_issue_type}.json"
    file_path = Path(f"./artifacts/{file_name}")
    save_data_to(
        file=file_path,
        data=[issue.raw for issue in jira_issues],
        output_log=False,
    )
    logger.info(
        "Saved %i Jira %s(s), see %s",
        len(jira_issues),
        jira_issue_type.lower(),
        str(file_path.absolute()),
    )


def map_jira_to_regscale_issue(
    jira_issue: jiraIssue, config: dict, parent_id: int, parent_module: str, is_poam: Optional[bool] = False
) -> Issue:
    """
    Map Jira issues to RegScale issues

    :param jiraIssue jira_issue: Jira issue to map to issue in RegScale
    :param dict config: Application config
    :param int parent_id: Parent record ID in RegScale
    :param str parent_module: Parent record module in RegScale
    :param bool is_poam: Whether to create the issue as a POAM in RegScale
    :return: Issue object of the newly created issue in RegScale
    :rtype: Issue
    """
    due_date = map_jira_due_date(jira_issue, config)
    issue = Issue(
        title=jira_issue.fields.summary,
        severityLevel=Issue.assign_severity(jira_issue.fields.priority.name),
        issueOwnerId=config["userId"],
        dueDate=due_date,
        description=(
            f"Description {jira_issue.fields.description}"
            f"\nStatus: {jira_issue.fields.status.name}"
            f"\nDue Date: {due_date}"
        ),
        status=("Closed" if jira_issue.fields.status.name.lower() == "done" else config["issues"]["jira"]["status"]),
        jiraId=jira_issue.key,
        identification="Jira Sync",
        sourceReport="Jira",
        parentId=parent_id,
        parentModule=parent_module,
        dateCreated=get_current_datetime(),
        dateCompleted=(get_current_datetime() if jira_issue.fields.status.name.lower() == "done" else None),
        isPoam=is_poam,
    )

    # Apply custom field mappings from Jira to RegScale
    custom_fields = config.get("jiraCustomFields", {})
    if custom_fields:
        apply_custom_fields_to_regscale_object(issue, custom_fields, jira_issue)

    return issue


def map_jira_due_date(jira_issue: Optional[jiraIssue], config: dict) -> str:
    """
    Parses the provided jira_issue for a due date and returns it as a string

    :param Optional[jiraIssue] jira_issue: Jira issue to parse for a due date
    :param dict config: Application config
    :return: Due date as a string
    :rtype: str
    """
    due_date_str: str
    if jira_issue and jira_issue.fields.duedate:
        due_date_str = jira_issue.fields.duedate
    elif jira_issue and jira_issue.fields.priority:
        due_date_dt = datetime.now() + timedelta(days=config["issues"]["jira"][jira_issue.fields.priority.name.lower()])
        due_date_str = convert_datetime_to_regscale_string(due_date_dt)
    else:
        due_date_dt = datetime.now() + timedelta(days=config["issues"]["jira"]["medium"])
        due_date_str = convert_datetime_to_regscale_string(due_date_dt)
    return due_date_str


def _generate_jira_comment(regscale_object: Union[Issue, Task]) -> str:
    """
    Generate a Jira comment from a RegScale issue and it's populated fields

    :param Union[Issue, Task] regscale_object: RegScale issue or task to generate a Jira comment from
    :return: Jira comment
    :rtype: str
    """
    exclude_fields = [
        "createdById",
        "lastUpdatedById",
        "issueOwnerId",
        "assignedToId",
        "uuid",
    ] + regscale_object._exclude_graphql_fields
    comment = ""
    for field_name, field_value in regscale_object.__dict__.items():
        if field_value and field_name not in exclude_fields:
            comment += f"**{field_name}:** {field_value}\n"
    return comment


def create_issue_in_jira(
    regscale_object: Union[Issue, Task],
    jira_client: JIRA,
    jira_project: str,
    issue_type: str,
    add_attachments: Optional[bool] = True,
    attachments: Optional[dict] = None,
    api: Optional[Api] = None,
    custom_fields: Optional[dict] = None,
) -> jiraIssue:
    """
    Create a new issue in Jira

    :param Union[Issue, Task] regscale_object: RegScale issue or task object
    :param JIRA jira_client: Jira client to use for issue creation in Jira
    :param str jira_project: Project name in Jira to create the issue in
    :param str issue_type: The type of issue to create in Jira
    :param Optional[bool] add_attachments: Whether to add attachments to new issue, defaults to true
    :param Optional[dict] attachments: Dictionary containing attachments, defaults to None
    :param Optional[Api] api: API object to download attachments, defaults to None
    :param Optional[dict] custom_fields: Custom field mappings from Jira custom fields to RegScale issue fields, defaults to None
    :return: Newly created issue in Jira
    :rtype: jiraIssue
    """
    if not api:
        api = Api()
    try:
        regscale_object_url = f"RegScale {regscale_object.get_module_string().title()} #{regscale_object.id}: {urljoin(api.config['domain'], f'/form/{regscale_object.get_module_string()}/{regscale_object.id}')}\n\n"
        logger.debug("Creating Jira issue: %s", regscale_object.title)
        new_issue = jira_client.create_issue(
            project=jira_project,
            summary=regscale_object.title,
            description=regscale_object_url + (regscale_object.description or ""),
            issuetype=issue_type,
        )
        logger.debug("Jira issue created: %s", new_issue.key)

        # Apply custom field mappings if provided
        if custom_fields:
            apply_custom_fields_to_jira_issue(new_issue, custom_fields, regscale_object)

        # add a comment to the new Jira issue
        logger.debug("Adding comment to Jira issue: %s", new_issue.key)
        _ = jira_client.add_comment(
            issue=new_issue,
            body=regscale_object_url + _generate_jira_comment(regscale_object),
        )
        logger.debug("Comment added to Jira issue: %s", new_issue.key)
    except JIRAError as ex:
        error_and_exit(f"Unable to create Jira issue.\nError: {ex}")
    # add the attachments to the new Jira issue
    if add_attachments and attachments:
        compare_files_for_dupes_and_upload(
            jira_issue=new_issue,
            regscale_object=regscale_object,
            jira_client=jira_client,
            api=api,
        )
    return new_issue


def compare_files_for_dupes_and_upload(
    jira_issue: jiraIssue, regscale_object: Union[Issue, Task], jira_client: JIRA, api: Api
) -> None:
    """
    Compare files for duplicates and upload them to Jira and RegScale

    :param jiraIssue jira_issue: Jira issue to upload the attachments to
    :param Union[Issue, Task] regscale_object: RegScale issue or task to upload the attachments from
    :param JIRA jira_client: Jira client to use for uploading the attachments
    :param Api api: Api object to use for interacting with RegScale
    :rtype: None
    :return: None
    """
    jira_uploaded_attachments: list[str] = []
    regscale_uploaded_attachments: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        jira_dir, regscale_dir = download_regscale_attachments_to_directory(
            directory=temp_dir,
            jira_issue=jira_issue,
            regscale_object=regscale_object,
            api=api,
        )
        jira_attachment_hashes = compute_hashes_in_directory(jira_dir)
        regscale_attachment_hashes = compute_hashes_in_directory(regscale_dir)

        upload_files_to_jira(
            jira_attachment_hashes,
            regscale_attachment_hashes,
            jira_issue,
            regscale_object,
            jira_client,
            jira_uploaded_attachments,
        )
        upload_files_to_regscale(
            jira_attachment_hashes, regscale_attachment_hashes, regscale_object, api, regscale_uploaded_attachments
        )

    log_upload_results(regscale_uploaded_attachments, jira_uploaded_attachments, regscale_object, jira_issue)


def upload_files_to_jira(
    jira_attachment_hashes: dict,
    regscale_attachment_hashes: dict,
    jira_issue: jiraIssue,
    regscale_object: Union[Issue, Task],
    jira_client: JIRA,
    jira_uploaded_attachments: list,
) -> None:
    """
    Upload files to Jira

    :param dict jira_attachment_hashes: Dictionary of Jira attachment hashes
    :param dict regscale_attachment_hashes: Dictionary of RegScale attachment hashes
    :param jiraIssue jira_issue: Jira issue to upload the attachments to
    :param Union[Issue, Task] regscale_object: RegScale issue or task to upload the attachments from
    :param JIRA jira_client: Jira client to use for uploading the attachments
    :param list jira_uploaded_attachments: List of Jira attachments that were uploaded
    :rtype: None
    :return: None
    """
    for file_hash, file in regscale_attachment_hashes.items():
        if file_hash not in jira_attachment_hashes:
            try:
                with open(file, "rb") as in_file:
                    jira_client.add_attachment(
                        issue=jira_issue.id,
                        attachment=BytesIO(in_file.read()),  # type: ignore
                        filename=(
                            f"RegScale_{regscale_object.get_module_string().title()}_{regscale_object.id}_"
                            f"{Path(file).name}"
                        ),
                    )
                    jira_uploaded_attachments.append(file)
            except JIRAError as ex:
                logger.error(
                    "Unable to upload %s to Jira issue %s.\nError: %s",
                    Path(file).name,
                    jira_issue.key,
                    ex,
                )
            except TypeError as ex:
                logger.error(
                    "Unable to upload %s to Jira issue %s.\nError: %s",
                    Path(file).name,
                    jira_issue.key,
                    ex,
                )


def upload_files_to_regscale(
    jira_attachment_hashes: dict,
    regscale_attachment_hashes: dict,
    regscale_object: Union[Issue, Task],
    api: Api,
    regscale_uploaded_attachments: list,
) -> None:
    """
    Upload files to RegScale

    :param dict jira_attachment_hashes: Dictionary of Jira attachment hashes
    :param dict regscale_attachment_hashes: Dictionary of RegScale attachment hashes
    :param Union[Issue, Task] regscale_object: RegScale issue or task to upload the attachments to
    :param Api api: Api object to use for interacting with RegScale
    :param list regscale_uploaded_attachments: List of RegScale attachments that were uploaded
    :rtype: None
    :return: None
    """
    for file_hash, file in jira_attachment_hashes.items():
        if file_hash not in regscale_attachment_hashes:
            with open(file, "rb") as in_file:
                if File.upload_file_to_regscale(
                    file_name=f"Jira_attachment_{Path(file).name}",
                    parent_id=regscale_object.id,
                    parent_module=regscale_object.get_module_string(),
                    api=api,
                    file_data=in_file.read(),
                ):
                    regscale_uploaded_attachments.append(file)
                    logger.debug(
                        "Uploaded %s to RegScale %s #%i.",
                        Path(file).name,
                        regscale_object.get_module_string().title(),
                        regscale_object.id,
                    )
                else:
                    logger.warning(
                        "Unable to upload %s to RegScale %s #%i.",
                        Path(file).name,
                        regscale_object.get_module_string().title(),
                        regscale_object.id,
                    )


def log_upload_results(
    regscale_uploaded_attachments: list,
    jira_uploaded_attachments: list,
    regscale_object: Union[Issue, Task],
    jira_issue: jiraIssue,
) -> None:
    """
    Log the results of the upload process

    :param list regscale_uploaded_attachments: List of RegScale attachments that were uploaded
    :param list jira_uploaded_attachments: List of Jira attachments that were uploaded
    :param Union[Issue, Task] regscale_object: RegScale issue or task that the attachments were uploaded to
    :param jiraIssue jira_issue: Jira issue that the attachments were uploaded to
    :rtype: None
    :return: None
    """
    if regscale_uploaded_attachments and jira_uploaded_attachments:
        logger.info(
            "%i file(s) uploaded to RegScale %s #%i and %i file(s) uploaded to Jira %s %s.",
            len(regscale_uploaded_attachments),
            regscale_object.get_module_string().title(),
            regscale_object.id,
            len(jira_uploaded_attachments),
            jira_issue.fields.issuetype.name,
            jira_issue.key,
        )
    elif jira_uploaded_attachments:
        logger.info(
            "%i file(s) uploaded to Jira %s %s.",
            len(jira_uploaded_attachments),
            jira_issue.fields.issuetype.name,
            jira_issue.key,
        )
    elif regscale_uploaded_attachments:
        logger.info(
            "%i file(s) uploaded to RegScale %s #%i.",
            len(regscale_uploaded_attachments),
            regscale_object.get_module_string().title(),
            regscale_object.id,
        )


def validate_issue_type(jira_client: JIRA, issue_type: str) -> bool:
    """
    Validate the provided issue type in Jira

    :param JIRA jira_client: Jira client to use for the request
    :param str issue_type: Issue type to validate
    :rtype: bool
    :return: True if the issue type is valid, False otherwise
    """
    issue_types = jira_client.issue_types()
    for issue in issue_types:
        if issue.name == issue_type:
            return True
    available_types = ", ".join({iss.name for iss in issue_types})
    logger.warning(
        "Issue type '%s' not found in this Jira project. Available types: %s",
        issue_type,
        available_types,
    )
    return False


def download_regscale_attachments_to_directory(
    directory: str,
    jira_issue: jiraIssue,
    regscale_object: Union[Issue, Task],
    api: Api,
) -> tuple[str, str]:
    """
    Function to download attachments from Jira and RegScale issues to a directory

    :param str directory: Directory to store the files in
    :param jiraIssue jira_issue: Jira issue to download the attachments for
    :param Union[Issue, Task] regscale_object: RegScale issue or task to download the attachments for
    :param Api api: Api object to use for interacting with RegScale
    :return: Tuple of strings containing the Jira and RegScale directories
    :rtype: tuple[str, str]
    """
    # determine which attachments need to be uploaded to prevent duplicates by checking hashes
    jira_dir = os.path.join(directory, "jira")
    check_file_path(jira_dir, False)
    # download all attachments from Jira to the jira directory in temp_dir
    for jira_attachment in jira_issue.fields.attachment:
        with open(os.path.join(jira_dir, jira_attachment.filename), "wb") as file:
            file.write(jira_attachment.get())
    # get the regscale issue attachments
    regscale_issue_attachments = File.get_files_for_parent_from_regscale(
        api=api,
        parent_id=regscale_object.id,
        parent_module=regscale_object.get_module_string(),
    )
    # create a directory for the regscale attachments
    regscale_dir = os.path.join(directory, "regscale")
    check_file_path(regscale_dir, False)
    # download regscale attachments to the directory
    for regscale_attachment in regscale_issue_attachments:
        file_hash = regscale_attachment.fileHash if regscale_attachment.fileHash else regscale_attachment.shaHash
        if file_hash:
            with open(os.path.join(regscale_dir, regscale_attachment.trustedDisplayName), "wb") as file:
                file.write(
                    File.download_file_from_regscale_to_memory(
                        api=api,
                        record_id=regscale_object.id,
                        module=regscale_object.get_module_string(),
                        stored_name=regscale_attachment.trustedStorageName,
                        file_hash=file_hash,
                    )
                )
    return jira_dir, regscale_dir


def apply_custom_fields_to_jira_issue(
    jira_issue: jiraIssue, custom_fields: dict, regscale_object: Union[Issue, Task]
) -> None:
    """
    Apply custom field mappings to a Jira issue based on RegScale object attributes (RegScale -> Jira)

    :param jiraIssue jira_issue: Jira issue to apply custom fields to
    :param dict custom_fields: Dictionary mapping Jira custom field names to RegScale attribute names
    :param Union[Issue, Task] regscale_object: RegScale object to get attribute values from
    :rtype: None
    """
    if not custom_fields:
        return

    try:
        # Convert RegScale object to dictionary for easier attribute access
        if hasattr(regscale_object, "model_dump"):
            regscale_dict = regscale_object.model_dump()
        elif hasattr(regscale_object, "dict"):
            regscale_dict = regscale_object.dict()
        else:
            regscale_dict = regscale_object.__dict__

        # Build custom fields dictionary for Jira update
        jira_custom_fields = {}

        for jira_field_name, regscale_field_name in custom_fields.items():
            try:
                # Get the value from RegScale object
                field_value = regscale_dict.get(regscale_field_name)

                if field_value is not None:
                    jira_custom_fields[jira_field_name] = field_value
                    logger.debug(
                        "Mapped custom field %s (RegScale: %s) = %s for Jira issue %s",
                        jira_field_name,
                        regscale_field_name,
                        field_value,
                        jira_issue.key,
                    )
                else:
                    logger.debug(
                        "Custom field %s (RegScale: %s) has no value, skipping for Jira issue %s",
                        jira_field_name,
                        regscale_field_name,
                        jira_issue.key,
                    )
            except Exception as e:
                logger.warning(
                    "Unable to set custom field %s (RegScale: %s) for Jira issue %s: %s",
                    jira_field_name,
                    regscale_field_name,
                    jira_issue.key,
                    str(e),
                )

        # Update the Jira issue with custom fields if any were found
        if jira_custom_fields:
            jira_issue.update(fields=jira_custom_fields)
            logger.info(
                "Applied %d custom fields to Jira issue %s: %s",
                len(jira_custom_fields),
                jira_issue.key,
                list(jira_custom_fields.keys()),
            )
        else:
            logger.debug("No custom field values found for Jira issue %s", jira_issue.key)

    except Exception as e:
        logger.warning(
            "Error applying custom fields to Jira issue %s: %s",
            jira_issue.key,
            str(e),
        )


def _get_jira_field_value(jira_issue: jiraIssue, jira_field_name: str) -> Optional[Any]:
    """
    Get a custom field value from a Jira issue

    :param jiraIssue jira_issue: The Jira issue to get the field value from
    :param str jira_field_name: The name of the field to retrieve
    :return: The field value or None if not found
    :rtype: Optional[Any]
    """
    # Try to access the custom field from the Jira issue
    if hasattr(jira_issue.fields, jira_field_name):
        return getattr(jira_issue.fields, jira_field_name)

    # Try accessing through raw fields (for custom fields)
    if hasattr(jira_issue.fields, "raw") and jira_field_name in jira_issue.fields.raw:
        return jira_issue.fields.raw[jira_field_name]

    return None


def _set_regscale_field_value(
    regscale_object: Union[Issue, Task],
    regscale_field_name: str,
    jira_field_value: Any,
    jira_field_name: str,
    jira_issue: jiraIssue,
) -> bool:
    """
    Set a field value on a RegScale object

    :param Union[Issue, Task] regscale_object: The RegScale object to set the field on
    :param str regscale_field_name: The name of the field to set
    :param Any jira_field_value: The value to set
    :param str jira_field_name: The Jira field name for logging
    :param jiraIssue jira_issue: The Jira issue for logging
    :return: True if the field was set successfully, False otherwise
    :rtype: bool
    """
    if hasattr(regscale_object, regscale_field_name):
        setattr(regscale_object, regscale_field_name, jira_field_value)
        logger.debug(
            "Mapped custom field %s (Jira: %s) = %s for RegScale %s #%s from Jira issue %s",
            regscale_field_name,
            jira_field_name,
            jira_field_value,
            regscale_object.get_module_string().title(),
            regscale_object.id,
            jira_issue.key,
        )
        return True
    else:
        logger.debug(
            "RegScale object does not have field %s, skipping custom field %s from Jira issue %s",
            regscale_field_name,
            jira_field_name,
            jira_issue.key,
        )
        return False


def _process_single_custom_field(
    jira_field_name: str, regscale_field_name: str, regscale_object: Union[Issue, Task], jira_issue: jiraIssue
) -> bool:
    """
    Process a single custom field mapping from Jira to RegScale

    :param str jira_field_name: The Jira field name
    :param str regscale_field_name: The RegScale field name
    :param Union[Issue, Task] regscale_object: The RegScale object to update
    :param jiraIssue jira_issue: The Jira issue to get data from
    :return: True if the field was processed successfully, False otherwise
    :rtype: bool
    """
    try:
        jira_field_value = _get_jira_field_value(jira_issue, jira_field_name)

        if jira_field_value is not None:
            return _set_regscale_field_value(
                regscale_object, regscale_field_name, jira_field_value, jira_field_name, jira_issue
            )
        else:
            logger.debug(
                "Custom field %s has no value in Jira issue %s, skipping",
                jira_field_name,
                jira_issue.key,
            )
            return False
    except Exception as e:
        logger.warning(
            "Unable to set custom field %s (Jira: %s) for RegScale %s #%s: %s",
            regscale_field_name,
            jira_field_name,
            regscale_object.get_module_string().title(),
            regscale_object.id,
            str(e),
        )
        return False


def apply_custom_fields_to_regscale_object(
    regscale_object: Union[Issue, Task], custom_fields: dict, jira_issue: jiraIssue
) -> None:
    """
    Apply custom field mappings to a RegScale object based on Jira issue custom fields (Jira -> RegScale)

    :param Union[Issue, Task] regscale_object: RegScale object to apply custom fields to
    :param dict custom_fields: Dictionary mapping Jira custom field names to RegScale attribute names
    :param jiraIssue jira_issue: Jira issue to get custom field values from
    :rtype: None
    """
    if not custom_fields:
        return

    try:
        fields_updated = False

        for jira_field_name, regscale_field_name in custom_fields.items():
            if _process_single_custom_field(jira_field_name, regscale_field_name, regscale_object, jira_issue):
                fields_updated = True

        if fields_updated:
            logger.info(
                "Applied custom fields from Jira issue %s to RegScale %s #%s",
                jira_issue.key,
                regscale_object.get_module_string().title(),
                regscale_object.id,
            )

    except Exception as e:
        logger.warning(
            "Error applying custom fields from Jira issue %s to RegScale %s #%s: %s",
            jira_issue.key,
            regscale_object.get_module_string().title(),
            regscale_object.id,
            str(e),
        )
