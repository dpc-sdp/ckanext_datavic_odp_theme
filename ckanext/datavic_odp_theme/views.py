from __future__ import annotations

import json
import base64
from typing import Any

from flask import Blueprint, jsonify

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
import ckan.views.group as group

from ckanext.datavic_odp_theme import config as conf, const

PERCENTAGE_OF_CHANCE = 0.5

vic_odp = Blueprint("vic_odp", __name__)
tk = toolkit

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


def dtv_config(encoded: str, embedded: bool):
    try:
        ids: list[str] = json.loads(base64.urlsafe_b64decode(encoded))
    except ValueError:
        return toolkit.abort(409)

    base_url: str = conf.get_base_url()
    catalog: list[dict[str, Any]] = []
    pkg_cache: dict[str, Any] = {}

    for id_ in ids:
        try:
            resource = toolkit.get_action("resource_show")({}, {"id": id_})
            if resource["package_id"] not in pkg_cache:
                pkg_cache[resource["package_id"]] = toolkit.get_action("package_show")(
                    {}, {"id": resource["package_id"]}
                )

        except (toolkit.NotAuthorized, toolkit.ObjectNotFound):
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

    base_map = toolkit.request.args.get("__dtv_base_map", conf.get_default_base_map())

    config = {
        "baseMaps": {"defaultBaseMapId": base_map, "previewBaseMapId": base_map},
        "catalog": catalog,
        "workbench": [item["id"] for item in catalog],
        "initialCamera": {
            "focusWorkbenchItems": true
        },
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

vic_odp.add_url_rule('/dtv_config/<encoded>/config.json', view_func=dtv_config, defaults={"embedded": False})
vic_odp.add_url_rule('/dtv_config/<encoded>/embedded/config.json', view_func=dtv_config, defaults={"embedded": True})

vic_odp.add_url_rule(
    "/organization/activity/<id>/<int:offset>", view_func=vic_organization_activity
)

def get_blueprints():
    return [vic_odp]
