from __future__ import annotations

from typing import Any

import ckan.lib.plugins as lib_plugins
import ckan.plugins.toolkit as tk
from ckan.types import Action, Context, DataDict
from ckan.types.logic import ActionResult

from ckanext.datavic_odp_theme import jobs


@tk.chained_action
def organization_update(next_, context, data_dict):
    result = next_(context, data_dict)
    tk.enqueue_job(jobs.reindex_organization, [result["id"]])
    return result


@tk.chained_action
def package_update(next_, context, data_dict):
    pkg_dict_before = tk.get_action("package_show")(
        {"ignore_auth": True}, {"id": data_dict["id"]}
    )
    pkg_dict_after = next_(context, data_dict)
    _datastore_delete(
        list(
            {res["id"] for res in pkg_dict_before.get("resources", [])}
            - {res["id"] for res in pkg_dict_after.get("resources", [])}
        )
    )
    return pkg_dict_after


@tk.chained_action
def package_delete(next_, context, data_dict):
    result = next_(context, data_dict)
    try:
        pkg_dict = tk.get_action("package_show")({"ignore_auth": True}, data_dict)
    except tk.ObjectNotFound:
        return result
    _datastore_delete([res["id"] for res in pkg_dict.get("resources", [])])
    return result


def _datastore_delete(resource_ids: list[str]):
    for res_id in resource_ids:
        try:
            tk.get_action("datastore_delete")(
                {"ignore_auth": True}, {"resource_id": res_id, "force": True}
            )
        except tk.ObjectNotFound:
            continue


@tk.chained_action
def resource_update(
    next_: Action, context: Context, data_dict: DataDict
) -> ActionResult.ResourceUpdate:
    try:
        result = next_(context, data_dict)
        return result
    except tk.ValidationError:
        _show_errors_in_sibling_resources(context, data_dict)


@tk.chained_action
def resource_create(
    next_: Action, context: Context, data_dict: DataDict
) -> ActionResult.ResourceCreate:
    try:
        result = next_(context, data_dict)
        return result
    except tk.ValidationError:
        _show_errors_in_sibling_resources(context, data_dict)


def _show_errors_in_sibling_resources(context: Context, data_dict: DataDict) -> Any:
    """Retrieves and raises validation errors for resources within the same package."""
    pkg_dict = tk.get_action("package_show")(context, {"id": data_dict["package_id"]})

    package_plugin = lib_plugins.lookup_package_plugin(pkg_dict["type"])

    _, errors = lib_plugins.plugin_validate(
        package_plugin,
        context,
        pkg_dict,
        context.get("schema") or package_plugin.update_package_schema(),
        "package_update",
    )

    resources_errors = errors["resources"]
    del errors["resources"]

    for i, resource_error in enumerate(resources_errors):
        if not resource_error:
            continue
        errors.update(
            {
                f"Field '{field}' in the resource '{pkg_dict['resources'][i]['name']}'": (
                    error
                )
                for field, error in resource_error.items()
            }
        )
    if errors:
        raise tk.ValidationError(errors)
