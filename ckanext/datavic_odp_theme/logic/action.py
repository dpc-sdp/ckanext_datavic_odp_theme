from __future__ import annotations

import ckan.plugins.toolkit as tk

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
