from __future__ import annotations

from typing import Optional

import ckan.plugins.toolkit as tk


CONFIG_BASE_MAP = "ckanext.datavicmain.dtv.base_map_id"
DEFAULT_BASE_MAP = "basemap-vic-topographic"

CONFIG_BASE_URL = "ckanext.datavicmain.odp.public_url"

CONFIG_DTV_FQ = "ckanext.datavicmain.dtv.supported_formats"
DEFAULT_DTV_FQ = [
    "wms",
    "shapefile",
    "zip (shp)",
    "shp",
    "kmz",
    "geojson",
    "csv-geo-au",
    "aus-geo-csv",
]
CONFIG_DTV_MAX_SIZE_LIMIT = "ckanext.datavicmain.dtv.max_size_limit"
CONFIG_DTV_URL = "ckanext.datavic_odp_theme.dtv.url"
CONFIG_DTV_EXTERNAL_LINK = "ckanext.datavic_odp_theme.dtv.external_link"

CONFIG_PARENT_SITE_URL = "ckan.parent_site_url"
DEFAULT_PARENT_SITE_URL = "https://www.data.vic.gov.au"

CONFIG_HOTJAR_ENABLED = "ckan.tracking.hotjar_enabled"
CONFIG_MONSIDO_TRACKING_ENABLED = "ckan.tracking.monsido_enabled"
CONFIG_HOTJAR_HJID = "ckan.tracking.hotjar.hjid"
CONFIG_HOTJAR_HJSV = "ckan.tracking.hotjar.hjsv"
CONFIG_MONSIDO_DOMAIN_TOKEN = "ckan.tracking.monsido.domain_token"
CONFIG_GOOGLE_OPTIMIZE_ID = "ckan.google_optimize.id"


def get_default_base_map() -> str:
    return tk.config.get(CONFIG_BASE_MAP, DEFAULT_BASE_MAP)


def get_base_url() -> str:
    return tk.config.get(CONFIG_BASE_URL) or tk.config["ckan.site_url"]


def get_dtv_supported_formats() -> set[str]:
    return {
        fmt.lower() for fmt in tk.aslist(tk.config.get(CONFIG_DTV_FQ)) or DEFAULT_DTV_FQ
    }


def get_dtv_max_size_limit() -> str:
    return tk.config.get(CONFIG_DTV_MAX_SIZE_LIMIT, "157286400")


def get_dtv_url() -> str:
    return tk.config.get(CONFIG_DTV_URL, "")


def get_dtv_external_link() -> str:
    return tk.config.get(CONFIG_DTV_EXTERNAL_LINK, "")


def get_parent_site_url() -> str:
    return tk.config.get(CONFIG_PARENT_SITE_URL, DEFAULT_PARENT_SITE_URL).rstrip("/")


def hotjar_tracking_enabled() -> bool:
    return tk.asbool(tk.config.get(CONFIG_HOTJAR_ENABLED))


def monsido_tracking_enabled() -> bool:
    return tk.asbool(tk.config.get(CONFIG_MONSIDO_TRACKING_ENABLED))


def get_hotjar_hsid() -> Optional[str]:
    return tk.config.get(CONFIG_HOTJAR_HJID)


def get_hotjar_hjsv() -> Optional[str]:
    return tk.config.get(CONFIG_HOTJAR_HJSV)


def get_monsido_domain_token() -> Optional[str]:
    return tk.config.get(CONFIG_MONSIDO_DOMAIN_TOKEN)
