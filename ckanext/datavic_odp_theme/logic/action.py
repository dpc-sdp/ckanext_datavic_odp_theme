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
def user_update(next_, context, data_dict):
    """Lock email to the stored value for non-sysadmins (including reset-key)."""
    # Sysadmins may set email from the request; leave data_dict unchanged.
    if tk.current_user.is_authenticated and tk.current_user.sysadmin:
        return next_(context, data_dict)

    # Target user missing: defer to core (e.g. NotFound).
    user_obj = model.User.get(data_dict.get("id"))
    if user_obj is None:
        return next_(context, data_dict)

    # Ignore submitted email, keep the address already on the user row.
    data_dict["email"] = user_obj.email

    return next_(context, data_dict)


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
    except tk.ValidationError as e:
        _show_errors_in_sibling_resources(context, data_dict, e, "update")


@tk.chained_action
def resource_create(
    next_: Action, context: Context, data_dict: DataDict
) -> ActionResult.ResourceCreate:
    try:
        result = next_(context, data_dict)
        return result
    except tk.ValidationError as e:
        _show_errors_in_sibling_resources(context, data_dict, e, "create")


@tk.chained_action
def resource_delete(
    next_: Action, context: Context, data_dict: DataDict
) -> ActionResult.ResourceDelete:
    try:
        result = next_(context, data_dict)
        return result
    except tk.ValidationError as e:
        _show_errors_in_sibling_resources(context, data_dict, e, "delete")


def _show_errors_in_sibling_resources(
    context: Context,
    data_dict: DataDict,
    original_error: tk.ValidationError,
    action: str,
) -> Any:
    """Raise the original resource errors plus any package-level sibling errors."""
    validation_context = tk.fresh_context(context)
    validation_context["ignore_auth"] = True
    validation_context["for_update"] = True

    resource_id = data_dict.get("id")
    package_id = data_dict.get("package_id")
    if not package_id and resource_id:
        resource = model.Resource.get(resource_id)
        package_id = resource.package_id if resource else None

    if not package_id:
        raise original_error

    pkg_dict = tk.get_action("package_show")(
        validation_context,
        {"id": package_id},
    )
    # Strip non-JSON-serializable upload artefacts; scheming's extras_valid_json
    # validator calls json.dumps on resource fields and chokes on FileStorage,
    # which masks the real ValidationError (e.g. ClamAV) with a 500.
    resource_for_validation = {
        k: v for k, v in data_dict.items() if k not in ("upload", "clear_upload")
    }

    current_resource_index = None
    if action == "create":
        pkg_dict.setdefault("resources", []).append(resource_for_validation)
        current_resource_index = len(pkg_dict["resources"]) - 1
    elif action == "update":
        for i, resource in enumerate(pkg_dict.get("resources", [])):
            if resource["id"] == resource_id:
                pkg_dict["resources"][i] = resource_for_validation
                current_resource_index = i
                break
    elif action == "delete":
        pkg_dict["resources"] = [
            resource
            for resource in pkg_dict.get("resources", [])
            if resource["id"] != resource_id
        ]

    package_plugin = lib_plugins.lookup_package_plugin(pkg_dict["type"])

    _, package_errors = lib_plugins.plugin_validate(
        package_plugin,
        validation_context,
        pkg_dict,
        validation_context.get("schema") or package_plugin.update_package_schema(),
        "package_update",
    )

    errors = dict(original_error.error_dict)
    for field, field_errors in package_errors.items():
        if field != "resources" and field not in errors:
            errors[field] = field_errors

    resources_errors = package_errors.get("resources", [])

    for i, resource_error in enumerate(resources_errors):
        if not resource_error or i == current_resource_index:
            continue
        resource_name = pkg_dict["resources"][i].get("name") or pkg_dict["resources"][i].get("id")
        errors.update(
            {
                f"Field '{field}' in the resource '{resource_name}'": error
                for field, error in resource_error.items()
            }
        )
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
        missing_conditions.append(or_(model_attr.is_(None), model_attr == ""))

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
