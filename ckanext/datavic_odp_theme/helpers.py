from __future__ import annotations

import json
import base64

from typing import Any
import ckan.plugins.toolkit as toolkit
import ckan.logic           as logic
import ckan.model as model
import logging

from sqlalchemy import and_ as _and_
from sqlalchemy.sql import func
from ckan.common import config, request

NotFound = toolkit.ObjectNotFound
log = logging.getLogger(__name__)

CONFIG_DTV_FQ = "ckanext.datavicmain.dtv.supported_formats"
DEFAULT_DTV_FQ = [
    "wms", "shapefile", "zip (shp)", "shp", "kmz",
    "geojson", "csv-geo-au", "aus-geo-csv"
]

def organization_list():
    org_list = toolkit.get_action('organization_list')({}, {})
    organizations = []
    for org in org_list:
        org_dict = toolkit.get_action('organization_show')({}, {'id': org})
        organizations.append(org_dict)

    return organizations


def group_list():
    return toolkit.get_action('group_list')({}, {'all_fields': True})


def format_list(limit=100):
    resource_formats = []
    try:
        session = model.Session

        query = (session.query(
            model.Resource.format,)
            .filter(_and_(
                model.Resource.state == 'active',
            ))
            .group_by(model.Resource.format)
            .order_by(
                func.lower(model.Resource.format)
            ))
        resource_formats = [resource.format for resource in query if not resource.format == '']
    except Exception as e:
        log.error(e.message)

    return resource_formats


def hotjar_tracking_enabled():
    return toolkit.asbool(config.get('ckan.tracking.hotjar_enabled', False))


def monsido_tracking_enabled():
    return toolkit.asbool(config.get('ckan.tracking.monsido_enabled', False))


def get_hotjar_hsid():
    return config.get('ckan.tracking.hotjar.hjid', None)


def get_hotjar_hjsv():
    return config.get('ckan.tracking.hotjar.hjsv', None)


def get_monsido_domain_token():
    return config.get('ckan.tracking.monsido.domain_token', None)


def get_ga_site():
    from urlparse.parse import urlparse
    site_url = config.get('ckan.site_url', None)
    o = urlparse(site_url)
    return o.hostname


def get_parent_site_url():
    return config.get('ckan.parent_site_url', 'https://www.data.vic.gov.au/')


def release_date(pkg_dict):
    """
    Copied from https://github.com/salsadigitalauorg/datavic_ckan_2.2/blob/develop/iar/src/ckanext-datavic/ckanext/datavic/plugin.py#L296
    :param pkg_dict:
    :return:
    """
    dates = []
    dates.append(pkg_dict['metadata_created'])
    for resource in pkg_dict['resources']:
        if 'release_date' in resource and resource['release_date'] != '' and resource['release_date'] != '1970-01-01':
            dates.append(resource['release_date'])
    dates.sort()
    return dates[0].split("T")[0]


def get_gtm_code():
    # To get Google Tag Manager Code
    gtm_code = config.get('ckan.google_tag_manager.gtm_container_id', False)
    return str(gtm_code)


def featured_resource_preview(package):
    # To get a featured preview for the dataset
    featured_preview = None
    if package.get('nominated_view_resource',None):
        try:
            resource_view = toolkit.get_action('resource_view_list')(
                {}, {'id': package['nominated_view_resource']})[0]
            resource = toolkit.get_action('resource_show')(
                {}, {'id': resource_view['resource_id']})
            featured_preview = {
                            'preview':resource_view,
                            'resource':resource
                            }
        except NotFound:
            pass
    return featured_preview

def get_google_optimize_id():
    return config.get('ckan.google_optimize.id', None)


def get_digital_twin_resources(pkg_id: str) -> list[dict[str, Any]]:
    """Select resource suitable for DTV(Digital Twin Visualization).

    Additional info:
    https://gist.github.com/steve9164/b9781b517c99486624c02fdc7af0f186
    """
    supported_formats = {
        fmt.lower() for fmt in
        toolkit.aslist(toolkit.config.get(CONFIG_DTV_FQ, DEFAULT_DTV_FQ))
    }

    try:
        pkg = toolkit.get_action("package_show")({}, {"id": pkg_id})
    except (toolkit.ObjectNotFound, toolkit.NotAuthorized):
        return []

    if not pkg.get("enable_dtv", False):
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
        if fmt in {"kml", "kmz", "shp", "shapefile", "zip (shp)"} and len(
                pkg["resources"]
        ) > 1:
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


def url_for_dtv_config(ids: list[str], embedded: bool = True) -> str:
    """Build URL where DigitalTwin can get map configuration for the preview.

    """

    encoded = base64.urlsafe_b64encode(bytes(json.dumps(ids), "utf8"))
    return toolkit.url_for(
        "vic_odp.dtv_config",
        encoded=encoded, embedded=embedded,
        _external=True
    )
