#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Control Objective Model"""
from collections import defaultdict
from typing import Any, Optional

from pydantic import ConfigDict, Field

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.models.regscale_models.regscale_model import RegScaleModel


class ControlObjective(RegScaleModel):
    """RegScale Control Objective"""

    _module_slug = "controlObjectives"
    _unique_fields = [
        ["securityControlId", "name"],
    ]

    id: int = 0
    uuid: Optional[str] = None
    name: str
    description: str
    otherId: str = ""  # API does not return if None
    archived: Optional[bool] = False
    securityControlId: int
    parentObjectiveId: Optional[int] = None
    dateCreated: Optional[str] = Field(default_factory=get_current_datetime)
    dateLastUpdated: Optional[str] = Field(default_factory=get_current_datetime)
    objectiveType: Optional[str] = "objective"

    @staticmethod
    def _get_additional_endpoints() -> ConfigDict:
        """
        Get additional endpoints for the ControlObjective

        :return: Additional endpoints for the ControlObjective
        :rtype: ConfigDict
        """
        return ConfigDict(
            get_all_by_parent="/api/{model_slug}/getByControl/{intParentID}",
            insert="/api/{model_slug}",
            get_by_catalog="/api/{model_slug}/getByCatalog/{catalogId}",
            get_by_catalogue="/api/{model_slug}/getByCatalogue/{catalogId}",
            # Note: This is identical to get_by_catalog, might be redundant
            get_by_control="/api/{model_slug}/getByControl/{controlId}",
            batch_create="/api/{model_slug}/batchCreate",
        )  # type: ignore

    @classmethod
    def get_by_catalog(cls, catalog_id: int) -> list["ControlObjective"]:
        """
        Get a list of objects by catalog.

        :param int catalog_id: The ID of the catalog
        :return: A list of objects
        :rtype: list["ControlObjective"]
        """
        endpoint = cls.get_endpoint("get_by_catalog").format(catalogId=catalog_id)
        return cls._handle_list_response(cls._get_api_handler().get(endpoint))

    @classmethod
    def get_by_catalogue(cls, catalog_id: int) -> list["ControlObjective"]:
        """
        Get a list of objects by catalogue.

        :param int catalog_id: The ID of the catalogue
        :return: A list of objects
        :rtype: list["ControlObjective"]
        """

        return cls.get_by_catalog(cls, catalog_id)

    @classmethod
    def get_by_control(cls, control_id: int) -> list["ControlObjective"]:
        """
        Get a list of objects by control.

        :param int control_id: The ID of the control
        :return: A list of objects
        :rtype: list["ControlObjective"]
        """
        endpoint = cls.get_endpoint("get_by_control").format(controlId=control_id)
        return cls._handle_list_response(cls._get_api_handler().get(endpoint))

    @staticmethod
    def from_dict(obj: Any) -> "ControlObjective":
        """
        Create ControlObjective object from dict

        :param Any obj: Dictionary
        :return: ControlObjective class from provided dict
        :rtype: ControlObjective
        """
        _securityControlId = int(obj.get("securityControlId", 0))
        _id = int(obj.get("id", 0))
        _uuid = str(obj.get("uuid"))
        _name = str(obj.get("name"))
        _description = str(obj.get("description"))
        _otherId = str(obj.get("otherId"))
        _objectiveType = str(obj.get("objectiveType"))
        _archived = False
        return ControlObjective(
            _securityControlId,
            _id,
            _uuid,
            _name,
            _description,
            _otherId,
            _objectiveType,
            _archived,
        )

    @classmethod
    def fetch_control_objectives_by_other_id(
        cls, parent_id: int, other_id_contains: str, skip: int = 0, take: int = 50
    ) -> list["ControlObjective"]:
        """
        Fetch control objectives by other ID.

        :param int parent_id: The ID of the parent
        :param str other_id_contains: The other ID to search for
        :param int skip: Number of items to skip
        :param int take: Number of items to take
        :return: A list of control objectives
        :rtype: list["ControlObjective"]
        """

        query = f"""
            query GetControlImplementations() {{
                controlImplementations(
                    skip: {skip}, take: {take}, where: {{
                        parentId: {{eq: {parent_id}}},
                        control: {{
                            controlObjectives: {{
                                some: {{
                                    otherId: {{
                                        contains: "{other_id_contains}"
                                    }}
                                }}
                            }}
                        }}
                    }}
                ) {{
                items {{
                    id
                    control {{
                        id,
                        controlObjectives {{
                            id
                            uuid
                            name
                            description
                            otherId
                            archived
                            securityControlId
                            dateCreated
                            dateLastUpdated
                            objectiveType
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                }}
                totalCount
                }}
            }}
        """

        response = cls._get_api_handler().graph(query)
        control_objectives: list["ControlObjective"] = []
        if "controlImplementations" in response:
            # Extract controlObjectives from each control in the controlImplementations
            for item in response["controlImplementations"]["items"]:
                for objective in item["control"]["controlObjectives"]:
                    if (
                        other_id_contains in objective["otherId"]
                    ):  # API_PROBLEM: Hack to fix broken API returning too many results
                        if control_objective := cls(**objective):
                            control_objectives.append(control_objective)
        return control_objectives

    @classmethod
    def fetch_control_objectives_by_name(
        cls, parent_id: int, name_contains: str, skip: int = 0, take: int = 50
    ) -> list["ControlObjective"]:
        """
        Fetch control objectives by other ID.

        :param int parent_id: The ID of the parent
        :param str name_contains: The name to search for
        :param int skip: Number of items to skip
        :param int take: Number of items to take
        :return: A list of control objectives
        :rtype: list["ControlObjective"]
        """

        query = f"""
            query GetControlImplementations() {{
                controlImplementations(
                    skip: {skip}, take: {take}, where: {{
                        parentId: {{eq: {parent_id}}},
                        control: {{
                            controlObjectives: {{
                                some: {{
                                    name: {{
                                        contains: "{name_contains}"
                                    }}
                                }}
                            }}
                        }}
                    }}
                ) {{
                items {{
                    id
                    control {{
                        id,
                        controlObjectives {{
                            id
                            uuid
                            name
                            description
                            otherId
                            archived
                            securityControlId
                            dateCreated
                            dateLastUpdated
                            objectiveType
                        }}
                    }}
                }}
                pageInfo {{
                    hasNextPage
                }}
                totalCount
                }}
            }}
        """

        response = cls._get_api_handler().graph(query)
        control_objectives: list["ControlObjective"] = []
        if "controlImplementations" in response:
            # Extract controlObjectives from each control in the controlImplementations
            for item in response["controlImplementations"]["items"]:
                for objective in item["control"]["controlObjectives"]:
                    if name_contains in objective["name"]:  # TODO: Hack to fix broken API returning too many results
                        control_objectives.append(cls(**objective))
        return control_objectives


def _process_objective_ccis(objective: ControlObjective, ccis_to_control_ids: dict[str, set[int]]) -> None:
    """
    Process CCI IDs from a control objective.

    :param ControlObjective objective: The control objective to process
    :param dict ccis_to_control_ids: Dictionary to update with CCI mappings
    :return: None
    """
    if not objective.otherId:
        return

    cci_ids = objective.otherId.split(",")
    for cci_id in cci_ids:
        cci_id = cci_id.strip()
        if cci_id and cci_id.startswith("CCI-"):
            ccis_to_control_ids[cci_id].add(objective.securityControlId)


def _fetch_cci_objectives_batch(parent_id: int, skip: int, take: int) -> list[ControlObjective]:
    """
    Fetch a batch of CCI objectives.

    :param int parent_id: The parent ID
    :param int skip: Number of items to skip
    :param int take: Number of items to take
    :return: List of control objectives
    :rtype: list[ControlObjective]
    """
    return ControlObjective.fetch_control_objectives_by_other_id(
        parent_id=parent_id, other_id_contains="CCI-", skip=skip, take=take
    )


def map_ccis_to_control_ids(parent_id: int) -> dict:
    """
    Map CCI IDs to control IDs with pagination support.

    :param int parent_id: The parent ID to fetch objectives for
    :return: Dictionary mapping CCI IDs to sets of control IDs
    :rtype: dict
    """
    import logging

    logger = logging.getLogger("regscale")
    ccis_to_control_ids: dict[str, set[int]] = defaultdict(set)

    try:
        skip = 0
        take = 50  # Use 50 as RegScale API limit
        total_fetched = 0
        max_iterations = 100  # Increase safety limit since batch size is smaller

        for _ in range(max_iterations):
            objectives = _fetch_cci_objectives_batch(parent_id, skip, take)
            if not objectives:
                break

            # Process each objective
            for objective in objectives:
                _process_objective_ccis(objective, ccis_to_control_ids)

            total_fetched += len(objectives)

            # Check if we've reached the end
            if len(objectives) < take:
                break

            skip += take
        else:
            logger.warning(f"Reached max iterations ({max_iterations}). Total fetched: {total_fetched}")

    except Exception as e:
        logger.debug(f"Error fetching CCI to control map: {e}")
        return {}

    if ccis_to_control_ids:
        logger.debug(f"Mapped {len(ccis_to_control_ids)} unique CCIs to controls")

    return ccis_to_control_ids
