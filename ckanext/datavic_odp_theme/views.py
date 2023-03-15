from __future__ import annotations

import json
import base64
import random
from typing import Any

from flask import Blueprint, jsonify

import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckan.views.dataset as dataset
import ckan.views.group as group

from ckanext.datavic_odp_theme import config as conf, const


vic_odp = Blueprint("vic_odp", __name__)


def vic_groups_list(id):
    return h.redirect_to("dataset.read", id=id)


def vic_organization_activity(id: str, offset: int = 0):
    """Redirect to 403 if unauthorized
    :param id: organization name or id
    :param offset: offset
    :returns: redirect to 403 if not allowed view activity streams
    """
    try:
        return group.activity(
            id, offset=offset, group_type="organization", is_organization=True
        )
    except tk.NotAuthorized:
        tk.abort(const.FORBIDDEN_ACCESS, tk._("Unauthorized Access"))


def redirect_read(id: str):
    """
    redirect randomly if no_preview not provided
    """
    try:
        pkg_dict = tk.get_action("package_show")({}, {"id": id})
    except tk.ObjectNotFound:
        return dataset.read("dataset", id)

    should_redirect = int(random.random() < const.PERCENTAGE_OF_CHANCE)
    has_dtv_resources = tk.h.get_digital_twin_resources(id)
    has_nominated_view = pkg_dict.get("nominated_view_resource") not in ["", None]

    no_preview = tk.request.params.get("no_preview")

    if has_dtv_resources or has_nominated_view:
        if no_preview is None and should_redirect:
            return tk.h.redirect_to(f"/dataset/{id}?no_preview={should_redirect}")

    return dataset.read("dataset", id)


def dtv_config(encoded: str, embedded: bool):
    try:
        ids: list[str] = json.loads(base64.urlsafe_b64decode(encoded))
    except ValueError:
        return tk.abort(409)

    base_url: str = conf.get_base_url()
    catalog: list[dict[str, Any]] = []
    pkg_cache: dict[str, Any] = {}

    for id_ in ids:
        try:
            resource = tk.get_action("resource_show")({}, {"id": id_})
            if resource["package_id"] not in pkg_cache:
                pkg_cache[resource["package_id"]] = tk.get_action("package_show")(
                    {}, {"id": resource["package_id"]}
                )

        except (tk.NotAuthorized, tk.ObjectNotFound):
            continue

        pkg = pkg_cache[resource["package_id"]]
        catalog.append(
            {
                "id": f"data-vic-embed-{id_}",
                "name": "{}: {}".format(pkg["title"], resource["name"] or "Unnamed"),
                "type": "ckan-item",
                "url": base_url,
                "resourceId": id_,
            }
        )

    base_map = tk.request.args.get("__dtv_base_map", conf.get_default_base_map())

    config = {
        "baseMaps": {"defaultBaseMapId": base_map, "previewBaseMapId": base_map},
        "catalog": catalog,
        "workbench": [item["id"] for item in catalog],
    }

    if embedded:
        config.update(
            {
                "elements": {
                    "map-navigation": {"disabled": embedded},
                    "menu-bar": {"disabled": embedded},
                    "bottom-dock": {"disabled": embedded},
                    "map-data-count": {"disabled": embedded},
                    "show-workbench": {"disabled": embedded},
                }
            }
        )
    return jsonify(config)


vic_odp.add_url_rule("/dataset/groups/<id>", view_func=vic_groups_list)
vic_odp.add_url_rule(
    "/dtv_config/<encoded>/config.json",
    view_func=dtv_config,
    defaults={"embedded": False},
)
vic_odp.add_url_rule(
    "/dtv_config/<encoded>/embedded/config.json",
    view_func=dtv_config,
    defaults={"embedded": True},
)
vic_odp.add_url_rule(
    "/organization/activity/<id>/<int:offset>", view_func=vic_organization_activity
)


def get_blueprints():
    # Check feature preview is enabled or not
    # If enabled add the redirect view for read pkg
    if conf.get_preview_redirect():
        vic_odp.add_url_rule("/dataset/<id>", view_func=redirect_read)

    return [vic_odp]
