from __future__ import annotations
from typing import Any

import ckan.authz as authz
import ckan.model as model
import ckan.plugins.toolkit as tk


@tk.chained_auth_function
# Same as core ``activity_list``: allow the chain to run for anonymous users so
# public group (and delegated show) checks can still apply; package/org anon is denied below.
@tk.auth_allow_anonymous_access
def vic_activity_list(next_auth, context, data_dict):
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
        and authz.auth_is_anon_user(context)
    ):
        return {"success": False}

    # Organisation activity: only org admins may view (anonymous already denied for org above).
    if data_dict["object_type"] == "organization":
        return {
            "success": authz.has_user_permission_for_group_or_org(
                data_dict["id"], tk.current_user.name, "admin"
            )
        }

    return authz.is_authorized(
        action_on_which_to_base_auth, context, {"id": data_dict["id"]}
    )


@tk.chained_auth_function
def vic_user_activity_list(next_auth, context, data_dict):
    """Restrict user activity streams: self, or org admins for subject's orgs.

    Anonymous requests are turned away in ``authz.is_authorized`` (no
    ``auth_allow_anonymous_access`` on this function). Sysadmins are not
    handled here: ``authz.is_authorized`` returns success for them before this
    chained auth runs (unless the action uses ``auth_sysadmins_check``, which
    ``user_activity_list`` does not).
    """

    user = model.User.get(data_dict.get("id"))
    # Unknown user id or name: deny (matches action layer behaviour).
    if not user:
        return {"success": False}

    # Users may always view their own activity stream.
    if tk.current_user.id == user.id:
        return {"success": True}

    # Org admins may view activity for users who belong to an org they administer.
    for org in user.get_groups(group_type="organization"):
        if authz.has_user_permission_for_group_or_org(
            org.id, tk.current_user.name, "admin"
        ):
            return {"success": True}

    # No remaining rule applies (e.g. user is not admin of any org the subject is in).
    return {"success": False}


@tk.chained_auth_function
def vic_package_activity_list(next_auth, context, data_dict):
    data_dict["object_type"] = "package"
    return vic_activity_list(next_auth, context, data_dict)


@tk.chained_auth_function
def vic_organization_activity_list(
    next_auth, context: dict[str, Any], group_dict: dict[str, str]
) -> dict[bool, bool]:
    group_dict["object_type"] = "organization"
    return vic_activity_list(next_auth, context, group_dict)


def vic_datatables_view_prioritize(context, data_dict):
    return {"success": False}