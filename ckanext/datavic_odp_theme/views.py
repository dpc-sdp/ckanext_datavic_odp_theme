from __future__ import annotations

import json
import base64
import random

from flask import Blueprint, jsonify

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit
import ckan.views.dataset as dataset
from ckan.common import request

vic_odp = Blueprint('vic_odp', __name__)

CONFIG_BASE_MAP = "ckanext.datavicmain.dtv.base_map_id"
DEFAULT_BASE_MAP = "basemap-vic-topographic"

NotFound = toolkit.ObjectNotFound
PERCENTAGE_OF_CHANCE = 0.5

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
        tk.abort(FORBIDDEN_ACCESS, tk._("Unauthorized Access"))


def redirect_read(id:str):
    """
    redirect randomly if no_preview not provided
    """
    try:
        pkg_dict = tk.get_action("package_show")({}, {"id": id})
    except (NotFound):
        return dataset.read("dataset", id)

    should_redirect = int(random.random() < PERCENTAGE_OF_CHANCE)
    has_dtv_resources = toolkit.h.get_digital_twin_resources(id)
    has_nominated_view = pkg_dict.get("nominated_view_resource") not in ["", None]

    no_preview = request.params.get("no_preview")

<<<<<<< HEAD
    if pkg_dict.get("nominated_view_resource") not in ["", None]:

        if no_preview is None and preview_enabled:
            return tk.h.redirect_to(
                f"/dataset/{id}?no_preview={preview_enabled}")
=======
    if has_dtv_resources or has_nominated_view:
        if no_preview is None and should_redirect:
            return toolkit.h.redirect_to(
                f"/dataset/{id}?no_preview={should_redirect}")
>>>>>>> origin/SXDEDPCXZIC-105_DATAVIC-499

    return dataset.read("dataset", id)


<<<<<<< HEAD
vic_odp.add_url_rule(u"/dataset/groups/<id>", view_func=vic_groups_list)
vic_odp.add_url_rule(
    "/organization/activity/<id>/<int:offset>", view_func=vic_organization_activity
)
=======
def dtv_config(encoded: str, embedded: bool):
    try:
        ids: list[str] = json.loads(base64.urlsafe_b64decode(encoded))
    except ValueError:
        return toolkit.abort(409)
    base_url: str = (
        toolkit.config.get("ckanext.datavicmain.odp.public_url")
        or toolkit.config["ckan.site_url"]
    )

    catalog = []
    pkg_cache = {}

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
        catalog.append({
            "id": f"data-vic-embed-{id_}",
            "name": "{}: {}".format(
                pkg["title"],
                resource["name"] or "Unnamed"
            ),
            "type": "ckan-item",
            "url": base_url,
            "resourceId": id_
        })

    base_map = toolkit.config.get(
        CONFIG_BASE_MAP, DEFAULT_BASE_MAP
    )
    base_map = toolkit.request.args.get("__dtv_base_map", base_map)

    config = {
        "baseMaps": {
            "defaultBaseMapId": base_map,
            "previewBaseMapId": base_map
        },
        "catalog": catalog,
        "workbench": [item["id"] for item in catalog],
    }

    if embedded:
        config.update({"elements": {
            "map-navigation": {
                "disabled": embedded
            },
            "menu-bar": {
                "disabled": embedded
            },
            "bottom-dock": {
                "disabled": embedded
            },
            "map-data-count": {
                "disabled": embedded
            },
            "show-workbench": {
                "disabled": embedded
            }
        }})
    return jsonify(config)


vic_odp.add_url_rule("/dataset/groups/<id>", view_func=vic_groups_list)
vic_odp.add_url_rule( u'/dataset/groups/<id>', view_func=vic_groups_list)
vic_odp.add_url_rule('/dtv_config/<encoded>/config.json', view_func=dtv_config, defaults={"embedded": False})
vic_odp.add_url_rule('/dtv_config/<encoded>/embedded/config.json', view_func=dtv_config, defaults={"embedded": True})
>>>>>>> origin/SXDEDPCXZIC-105_DATAVIC-499
