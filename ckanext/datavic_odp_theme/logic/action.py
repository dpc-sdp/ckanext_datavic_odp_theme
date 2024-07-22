from __future__ import annotations

from typing import Any

from sqlalchemy import or_

import ckan.lib.plugins as lib_plugins
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.types import Action, Context, DataDict
from ckan.types.logic import ActionResult
from ckan.logic import validate
from ckan.model import ResourceView
from ckanext.datavic_odp_theme.logic import scheme

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

    resources_errors = errors.get("resources", [])

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


@tk.side_effect_free
def datavic_list_incomplete_resources(context, data_dict):
    """Retrieves a list of resources that are missing at least one required field."""
    try:
        pkg_type = data_dict.get("type", "dataset")
        resource_schema = tk.h.scheming_get_dataset_schema(pkg_type)[
            "resource_fields"
        ]
    except TypeError:
        raise tk.ValidationError(f"No schema for {pkg_type} package type")

    required_fields = [
        field["field_name"]
        for field in resource_schema
        if tk.h.scheming_field_required(field)
    ]

    missing_conditions = []
    for field in required_fields:
        model_attr = getattr(model.Resource, field)
        missing_conditions.append(or_(model_attr == None, model_attr == ""))

    q = (
        model.Session.query(model.Resource)
        .join(model.Package)
        .filter(model.Package.state == "active")
        .filter(model.Resource.state == "active")
        .filter(or_(*missing_conditions))
    )

    if data_dict.get("by_package", False):
        grouped_resources = {}
        for resource in q:
            missing_fields = [
                field
                for field in required_fields
                if not getattr(resource, field)
            ]
            resource_dict = {
                "id": resource.id,
                "missing_fields": missing_fields,
            }

            grouped_resources.setdefault(resource.package_id, []).append(
                resource_dict
            )

        results = [
            {"package_id": package_id, "resources": resources}
            for package_id, resources in grouped_resources.items()
        ]
        num_packages = len(grouped_resources)
    else:
        results = []
        package_ids = set()
        for resource in q:
            package_ids.add(resource.package_id)
            results.append({
                "id": resource.id,
                "missing_fields": [
                    field
                    for field in required_fields
                    if not getattr(resource, field)
                ],
            })
        num_packages = len(package_ids)

    return {
        "num_resources": q.count(),
        "num_packages": num_packages,
        "results": results,
    }


@validate(scheme.datatables_view_prioritize)
def datavic_datatables_view_prioritize(
        context: Context, data_dict: DataDict
) -> ActionResult:
    """Check if the datatables view is prioritized over the recline view.
    If not, swap their order.
    """
    tk.check_access("vic_datatables_view_prioritize", context, data_dict)

    resource_id = data_dict["resource_id"]
    res_views = sorted(
        model.Session.query(ResourceView)
        .filter(ResourceView.resource_id == resource_id)
        .all(),
        key=lambda x: x.order,
    )
    datatables_views = _filter_views(res_views, "datatables_view")
    recline_views = _filter_views(res_views, "recline_view")

    if not (
        datatables_views
        and recline_views
        and datatables_views[0].order > recline_views[0].order
    ):
        return {"updated": False}

    datatables_views[0].order, recline_views[0].order = (
        recline_views[0].order,
        datatables_views[0].order,
    )
    order = [view.id for view in sorted(res_views, key=lambda x: x.order)]
    tk.get_action("resource_view_reorder")(
        {"ignore_auth": True}, {"id": resource_id, "order": order}
    )
    return {"updated": True}


@tk.chained_action
def resource_view_create(next_, context, data_dict):
    result = next_(context, data_dict)
    if data_dict["view_type"] == "datatables_view":
        tk.get_action("datavic_datatables_view_prioritize")(
            {"ignore_auth": True}, {"resource_id": data_dict["resource_id"]}
        )
    return result


def _filter_views(
    res_views: list[ResourceView], view_type: str
) -> list[ResourceView]:
    """Return a list of views with the given view type."""
    return [view for view in res_views if view.view_type == view_type]
