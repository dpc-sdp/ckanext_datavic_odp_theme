from __future__ import annotations
from typing import Any

import ckan.authz as authz
import ckan.plugins.toolkit as tk


@tk.chained_auth_function
@tk.auth_allow_anonymous_access
def vic_activity_list(context, data_dict):
    """
    :param id: the id or name of the object (e.g. package id)
    :type id: string
    :param object_type: The type of the object (e.g. 'package', 'organization',
                        'group', 'user')
    :type object_type: string
    :param include_data: include the data field, containing a full object dict
        (otherwise the data field is only returned with the object's title)
    :type include_data: boolean
    """
    if data_dict["object_type"] not in ("package", "organization", "group", "user"):
        return {"success": False, "msg": "object_type not recognized"}
    if data_dict.get("include_data") and not authz.check_config_permission(
        "public_activity_stream_detail"
    ):
        # The 'data' field of the activity is restricted to users who are
        # allowed to edit the object
        show_or_update = "update"
    else:
        # the activity for an object (i.e. the activity metadata) can be viewed
        # if the user can see the object
        show_or_update = "show"
    action_on_which_to_base_auth = "{}_{}".format(
        data_dict["object_type"], show_or_update
    )  # e.g. 'package_update'

    # DataVIC modification
    if (
        data_dict["object_type"] in ["package", "organization"]
        and not authz.auth_is_loggedin_user()
    ):
        return {"success": False}

    return authz.is_authorized(
        action_on_which_to_base_auth, context, {"id": data_dict["id"]}
    )


@tk.chained_auth_function
def vic_package_activity_list(context, data_dict):
    data_dict["object_type"] = "package"
    return vic_activity_list(context, data_dict)

@tk.chained_auth_function
def vic_organization_activity_list(
    context: dict[str, Any], group_dict: dict[str, str]
) -> dict[bool, bool]:
    group_dict["object_type"] = "organization"
    return vic_activity_list(context, group_dict)
