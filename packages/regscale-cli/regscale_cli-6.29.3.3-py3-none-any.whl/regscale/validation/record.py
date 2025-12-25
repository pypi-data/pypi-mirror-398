#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich Logging"""


# standard python imports
from typing import Optional

from regscale.core.app.api import Api

from regscale.core.utils.graphql import GraphQLQuery
from regscale.models.regscale_models.modules import Modules


def validate_regscale_object(parent_id: int, parent_module: str) -> bool:
    """
    Query regscale to confirm the object in question exists.

    :param int parent_id: The RegScale id to query
    :param str parent_module: The RegScale module to query
    :return: Whether the object exists or not
    :rtype: bool
    """
    import inflect  # Optimize import performance

    api = Api()
    query = GraphQLQuery()
    query.start_query()
    result = False
    mods = Modules()
    p = inflect.engine()
    for (
        key,
        val,
    ) in mods.dict().items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
        if val.lower() == parent_module.lower():
            mod_lookup = p.plural(key)
    query.add_query(
        entity=mod_lookup,
        items=[
            "id",
        ],
        where={"id": {"eq": parent_id}},
    )
    query.end_query()

    dat = api.graph(query=query.build())
    if mod_lookup.lower() in [k.lower() for k in dat.keys()] and dat[list(dat.keys())[0]]["totalCount"] > 0:
        result = True
    return result


def validate_component_or_ssp(ssp_id: Optional[int], component_id: Optional[int]) -> None:
    """
    Validate that either an SSP or component exists in RegScale.

    :param Optional[int] ssp_id: The RegScale SSP ID
    :param Optional[int] component_id: The RegScale component ID
    :rtype: None
    """
    from regscale.core.app.utils.app_utils import error_and_exit

    if not ssp_id and not component_id:
        error_and_exit("Please provide a RegScale SSP ID or component ID.")
    if ssp_id and component_id:
        error_and_exit("Please provide either a RegScale SSP ID or component ID, but not both.")
    record_id = ssp_id or component_id
    record_module = "securityplans" if ssp_id else "components"
    if not validate_regscale_object(record_id, record_module):
        error_and_exit(f"RegScale {record_module} ID #{record_id} does not exist.")
