from __future__ import annotations

import logging
import json
import base64
from typing import Any, Optional

from sqlalchemy import func

import ckan.plugins.toolkit as toolkit
import ckan.model as model

from ckanext.toolbelt.decorators import Collector

from ckanext.datavic_odp_theme import config as conf, const


log = logging.getLogger(__name__)
helper, get_helpers = Collector().split()


@helper
def organization_list():
    org_list = toolkit.get_action("organization_list")({}, {})
    organizations = []
    for org in org_list:
        org_dict = toolkit.get_action("organization_show")({}, {"id": org})
        organizations.append(org_dict)

    return organizations


@helper
def group_list():
    return toolkit.get_action("group_list")({}, {"all_fields": True})


@helper
def format_list() -> list[str]:
    """Return a list of all available resources on portal"""

    query = (
        model.Session.query(model.Resource.format)
        .filter(model.Resource.state == model.State.ACTIVE)
        .group_by(model.Resource.format)
        .order_by(func.lower(model.Resource.format))
    )

    formats = [
        resource.format.upper().split('.')[-1] for resource in query if resource.format
    ]
    unique_formats = set(formats)

    return sorted(list(unique_formats))


@helper
def hotjar_tracking_enabled() -> bool:
    return conf.hotjar_tracking_enabled()


@helper
def monsido_tracking_enabled() -> bool:
    return conf.monsido_tracking_enabled()


@helper
def get_hotjar_hsid() -> Optional[str]:
    return conf.get_hotjar_hsid()


@helper
def get_hotjar_hjsv() -> Optional[str]:
    return conf.get_hotjar_hjsv()


@helper
def get_monsido_domain_token() -> Optional[str]:
    return conf.get_monsido_domain_token()


@helper
def get_parent_site_url() -> str:
    return conf.get_parent_site_url()


@helper
def get_package_release_date(pkg_dict: dict[str, Any]) -> str:
    """Get release_date from resource or use metadata_created as a default"""
    dates: list[str] = [pkg_dict["metadata_created"]]

    for resource in pkg_dict["resources"]:
        if resource.get("release_date") and resource["release_date"] != "1970-01-01":
            dates.append(resource["release_date"])

    return sorted(dates)[0].split("T")[0]


@helper
def featured_resource_preview(package: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Return a featured resource preview
        - It takes only CSV resources with an existing preview
        - Only resources uploaded to datastore
        - Only not historical resources
    """

    featured_preview = None

    resource_groups: list[list[dict[str, Any]]] = toolkit.h.group_resources_by_temporal_range(
        package.get("resources", [])
    )

    resources = resource_groups[0] if resource_groups else []

    for resource in resources:
        if resource.get("format", "").lower() != "csv":
            continue

        if not resource.get("datastore_active"):
            continue

        try:
            resource_views = toolkit.get_action("resource_view_list")(
                {}, {"id": resource["id"]}
            )
        except toolkit.ObjectNotFound:
            pass
        else:
            # ensure there are actually previews as some resources are marked as datastore active but they don't have a preview and it breaks the page
            if not len(resource_views) > 0:
                continue

            featured_preview = {"preview": resource_views[0], "resource": resource}

    return featured_preview


@helper
def get_digital_twin_resources(pkg_id: str) -> list[dict[str, Any]]:
    """Select resource suitable for DTV(Digital Twin Visualization).

    Additional info:
    https://gist.github.com/steve9164/b9781b517c99486624c02fdc7af0f186
    """
    supported_formats: set[str] = conf.get_dtv_supported_formats()

    try:
        pkg = toolkit.get_action("package_show")({}, {"id": pkg_id})
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return []

    # Additional info #2
    if pkg["state"] != "active":
        return []

    acceptable_resources = {}
    for res in pkg["resources"]:
        if not res["format"]:
            continue

        fmt = res["format"].lower()
        # Additional info #1
        if fmt not in supported_formats:
            continue

        # Additional info #3
        if (
            fmt in {"kml", "kmz", "shp", "shapefile", "zip (shp)"}
            and len(pkg["resources"]) > 1
        ):
            continue

        # Additional info #3
        if fmt == "wms" and ~res["url"].find("data.gov.au/geoserver"):
            continue

        # Additional info #4
        if res["name"] in acceptable_resources:
            if acceptable_resources[res["name"]]["created"] > res["created"]:
                continue

        acceptable_resources[res["name"]] = res

    return list(acceptable_resources.values())


@helper
def url_for_dtv_config(ids: list[str], embedded: bool = True) -> str:
    """Build URL where DigitalTwin can get map configuration for the preview."""

    encoded = base64.urlsafe_b64encode(bytes(json.dumps(ids), "utf8"))
    return toolkit.url_for(
        "vic_odp.dtv_config", encoded=encoded, embedded=embedded, _external=True
    )


@helper
def is_resource_downloadable(resource: dict[str, Any]) -> bool:
    if (
        resource.get("has_views")
        or resource.get("url_type") == "upload"
        or resource["format"].upper() not in const.NOT_DOWNLOADABLE_FORMATS
    ):
        return True

    return False


@helper
def datastore_loaded_resources(pkg_dict: dict[str, Any]) -> list[str]:
    """Return a list of the dataset resources that are loaded to the datastore"""
    if not pkg_dict.get("resources"):
        return []

    return [
        resource["id"]
        for resource in pkg_dict["resources"]
        if resource["datastore_active"]
    ]


@helper
def datavic_max_image_size():
    """Return max size for image configurate for portal"""
    return toolkit.config["ckan.max_image_size"]


@helper
def datavic_get_dtv_url(ext_link: bool = False) -> str:
    """Return a URL for DTV map preview"""
    if toolkit.asbool(ext_link):
        url = conf.get_dtv_external_link()
    else:
        url = conf.get_dtv_url()

    if not url:
        return url

    if not url.endswith("/"):
        url = url + "/"

    return url


@helper
def dtv_exceeds_max_size_limit(resource_id: str) -> bool:
    """Check if DTV resource exceeds the maximum file size limit
    Args:
        resource_id (str): DTV resource id
    Returns:
        bool: return True if dtv resource exceeds maximum file size limit set
            in ckan config "ckanext.datavicmain.dtv.max_size_limit",
            otherwise - False
    """
    try:
        resource = toolkit.get_action("resource_show")({}, {"id": resource_id})
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return True

    limit = conf.get_dtv_max_size_limit()
    filesize = resource.get("filesize")
    if filesize and int(filesize) >= int(limit):
        return True

    return False


@helper
def datavic_datastore_dictionary(resource_id: str, resource_view_id: str):
    """
    Return the data dictionary info for a resource
    """
    try:
        resource_view = toolkit.get_action("resource_view_show")(
            {},
            {"id": resource_view_id}
        )
        headers = [
            f for f in toolkit.get_action("datastore_search")(
                {},
                {
                    "resource_id": resource_id,
                    "limit": 0,
                    "include_total": False
                }
            )["fields"]
            if not f["id"].startswith("_")
        ]

        if "show_fields" in resource_view:
            headers = [c for c in headers if c["id"] in resource_view["show_fields"]]

        return headers

    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return []


@helper
def datavic_update_org_error_dict(
    error_dict: dict[str, Any],
) -> dict[str, Any]:
    """Internal CKAN logic makes a validation for resource file size. We want
    to show it as an error on the Logo field."""
    if error_dict.pop("upload", "") == ["File upload too large"]:
        error_dict["Logo"] = [(
            f"File size is too large. Select an image which is no larger than {datavic_max_image_size()}MB."
        )]
    elif "Unsupported upload type" in error_dict.pop("image_upload", [""])[0]:
        error_dict["Logo"] = [(
            "Image format is not supported. "
            "Select an image in one of the following formats: "
            "JPG, JPEG, GIF, PNG, BMP, SVG."
        )]

    return error_dict

@helper
def resource_attributes(attrs):
    try:
        attrs = json.loads(attrs)
    except ValueError:
        return None

    return attrs
