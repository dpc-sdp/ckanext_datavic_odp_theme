from __future__ import annotations

import logging
from typing import Any, Optional

from flask import Response, session

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model, types

from ckanext.search_autocomplete.interfaces import ISearchAutocomplete
from ckanext.datapusher.plugin import DatapusherPlugin

from ckanext.datavic_odp_theme.logic import auth_functions, actions, get_validators
from ckanext.datavic_odp_theme.views import get_blueprints
from ckanext.datavic_odp_theme.helpers import get_helpers, group_list

log = logging.getLogger(__name__)


class DatavicODPTheme(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IActions)
    p.implements(p.IBlueprint)
    p.implements(p.IValidators)
    p.implements(p.IPackageController, inherit=True)
    p.implements(ISearchAutocomplete)
    p.implements(p.IAuthenticator, inherit=True)
    p.implements(p.ISignal)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("webassets", "datavic_odp_theme")

        # Reset group/organization cache on server restart
        group_list.reset(is_organization=False)
        group_list.reset(is_organization=True)

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()

    # IActions

    def get_actions(self):
        return actions()

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()

    # IValidators

    def get_validators(self):
        return get_validators()

    # IPackageController

    def before_dataset_index(self, pkg_dict: dict[str, Any]) -> dict[str, Any]:
        if pkg_dict.get("res_format"):
            pkg_dict["res_format"] = [
                res_format.upper().split(".")[-1]
                for res_format in pkg_dict["res_format"]
            ]

        if pkg_dict.get("res_format") and self._is_all_api_format(pkg_dict):
            pkg_dict.get("res_format").append("ALL_API")
        return pkg_dict

    def _is_all_api_format(self, pkg_dict: dict[str, Any]) -> bool:
        """Check if the dataset contains a resource in a format recognized as an API.
        This involves determining if the format of the resource is CSV and if this
        resource exists in the datastore or matches a format inside a predefined list.
        """
        for resource in tk.get_action("package_show")(
            {"ignore_auth": True},
            {"id": pkg_dict["id"]}
        ).get("resources", []):
            if resource["format"].upper() == "CSV" and resource["datastore_active"]:
                return True

        if [
            res_format
            for res_format in pkg_dict["res_format"]
            if res_format
                in [
                    "WMS",
                    "WFS",
                    "API",
                    "ARCGIS GEOSERVICES REST API",
                    "ESRI REST",
                    "GEOJSON",
                ]
        ]:
            return True
        return False

    # ISearchAutocomplete

    def get_categories(self):
        return {
            'organization': tk._('Organisations'),
            'res_format': tk._('Formats'),
            'groups': tk._('Categories'),
        }

    # IAuthenticator

    def login(self) -> Optional[Response]:
        session.modified = True

    def logout(self) -> Optional[Response]:
        session.modified = True

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.action_succeeded: [
                {
                    "receiver": clear_group_list_cache,
                    "sender": "group_create",
                },
                {
                    "receiver": clear_group_list_cache,
                    "sender": "group_update",
                },
                {
                    "receiver": clear_group_list_cache,
                    "sender": "group_delete",
                },
                {
                    "receiver": clear_group_list_cache,
                    "sender": "organization_create",
                },
                {
                    "receiver": clear_group_list_cache,
                    "sender": "organization_update",
                },
                {
                    "receiver": clear_group_list_cache,
                    "sender": "organization_delete",
                },
            ]
        }


def clear_group_list_cache(
    action_name: str,
    context: types.Context,
    data_dict: dict[str, Any],
    result: dict[str, Any],
):
    """Invalidates the cached group or organization list after
    create, update, or delete actions."""

    is_organization = (
        action_name.startswith("organization")
        or data_dict.get("type") == "organization"
    )
    group_list.reset(is_organization=is_organization)


@tk.blanket.auth_functions(auth_functions)
class DatavicODPThemeAuth(p.SingletonPlugin):
    """Register auth function inside separate extension.

    We are chaining auth functions from activity and overriding its templates
    at the same time. The former requires us to put our plugin after the
    activity, while the latter will work only if we put our plugin before the
    activity. The only way to solve this puzzle is to split the logic between
    two sub-plugins.

    """
    pass


class DatavicDatapusherPlugin(DatapusherPlugin, p.SingletonPlugin):
    p.implements(p.IPackageController, inherit=True)

    # IPackageController

    def after_dataset_create(self, context, pkg_dict):
        self._trigger_after_resource_create(pkg_dict)

        # Only add packages to groups when being created via the CKAN UI
        # (i.e. not during harvesting)
        if repr(tk.request) != '<LocalProxy unbound>' \
            and tk.get_endpoint()[0] in ['dataset', 'package', "datavic_dataset"]:
            # Add the package to the group ("category")
            pkg_group = pkg_dict.get('category', None)
            if pkg_group and pkg_dict.get('type', None) in ['dataset', 'package']:
                group = model.Group.get(pkg_group)
                group.add_package_by_name(pkg_dict.get('name', None))

    def after_dataset_update(self, context, pkg_dict):
        self._submit_new_resources_only(pkg_dict)

        group_id = pkg_dict.get('category', None)
        if group_id:
            group = model.Group.get(group_id)
            groups = context.get('package').get_groups('group')
            if group not in groups:
                group.add_package_by_name(pkg_dict.get('name'))

    def _submit_new_resources_only(self, pkg_dict):
        """Submit only newly added resources to xloader during dataset update.

        Compares current resource IDs against the previous activity snapshot
        to detect new resources. URL changes for existing resources are
        handled by the parent xloaderPlugin via ``notify()``.

        Falls back to submitting all resources if no activity data is
        available (e.g. activity plugin disabled, data migration).
        """
        current_resources = pkg_dict.get("resources", [])
        current_res_ids = {
            r.get("id") for r in current_resources if r.get("id")
        }

        previous_res_ids = self._get_previous_resource_ids(pkg_dict.get("id"))

        if previous_res_ids is None:
            log.info(
                "No previous activity for package %s — "
                "submitting all %d resources",
                pkg_dict.get("id"),
                len(current_resources),
            )
            for resource in current_resources:
                self._infer_format_and_submit(resource)
            return

        new_res_ids = current_res_ids - previous_res_ids

        if not new_res_ids:
            return

        log.info(
            "Detected %d new resource(s) for package %s: %s",
            len(new_res_ids),
            pkg_dict.get("id"),
            new_res_ids,
        )

        for resource in current_resources:
            if resource.get("id") in new_res_ids:
                self._infer_format_and_submit(resource)

    def _get_previous_resource_ids(self, pkg_id):
        """Return resource IDs from the most recent activity, or ``None``
        if unavailable.
        """
        if not pkg_id or not p.plugin_loaded("activity"):
            return None

        try:
            activities = tk.get_action("package_activity_list")(
                {"ignore_auth": True},
                {
                    "id": pkg_id,
                    "limit": 1,
                    "include_hidden_activity": True,
                },
            )
        except Exception:
            return None

        if not activities:
            return None

        prev_pkg = activities[0].get("data", {}).get("package", {})
        prev_resources = prev_pkg.get("resources", [])
        return {r.get("id") for r in prev_resources if r.get("id")}

    def _infer_format_and_submit(self, resource):
        """Infer the resource format from its URL if missing, then submit."""
        if resource and not resource.get("format"):
            if not resource.get("url_type"):
                url_without_params = resource.get("url", "").split("?")[0]
                resource["format"] = (
                    url_without_params.split(".")[-1].lower()
                )
        self._submit_to_xloader(resource)

    def _trigger_after_resource_create(self, pkg_dict):
        """Submit all resources after dataset creation.

        Syndication via ``package_create`` does not trigger
        ``after_resource_create``, so we handle it here.
        """
        for resource in pkg_dict.get("resources", []):
            self._infer_format_and_submit(resource)

    def _submit_to_datapusher(self, resource_dict):
        """The original method doesn't check if `url_type` is here. Seems like
        it's not here if we are calling it from the `after_dataset_create`.
        Just set a default url_type and delete after to be sure, that it doesn't break
        some core logic.

        Do not touch proper values, because it will definitely break something."""

        resource_dict.setdefault("url_type", "datavic_datapusher")
        resource_dict.setdefault("format", "")

        super()._submit_to_datapusher(resource_dict)

        if resource_dict["url_type"] == "datavic_datapusher":
            resource_dict.pop("url_type")
