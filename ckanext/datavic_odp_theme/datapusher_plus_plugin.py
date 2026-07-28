# Fills the trigger gap in ckanext-datapusher-plus for inline resources
# (DD syndication, API imports, UI package saves) that never reach
# after_resource_create.
#
# Deliberately not a DatapusherPlusPlugin subclass: that plugin's
# IResourceUrlChange/IResourceController hooks and this one's
# IDomainObjectModification hook all dispatch through a method literally
# named notify, and a subclass only ever gets one. datapusher_plus must
# therefore be enabled separately in ckan.plugins (configure() below
# enforces this); submission is delegated to its live instance via
# ckan.plugins.get_plugin rather than duplicated here.
from __future__ import annotations

import logging

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.model.domain_object import DomainObjectOperation
from ckan.model.package import Package
from ckan.model.resource import Resource

log = logging.getLogger(__name__)

REQUIRED_PLUGIN = "datapusher_plus"


class DatavicDatapusherPlusPlugin(p.SingletonPlugin):
    p.implements(p.IDomainObjectModification)
    p.implements(p.IConfigurable)

    def configure(self, config):
        if not p.plugin_loaded(REQUIRED_PLUGIN):
            raise Exception(
                "datavic_datapusher_plus requires the "
                f"'{REQUIRED_PLUGIN}' plugin to also be enabled in "
                "ckan.plugins"
            )

    def notify(self, entity, operation):
        if isinstance(entity, Resource) and operation == DomainObjectOperation.new:
            self._notify_new_resource(entity)
        elif isinstance(entity, Package) and operation == DomainObjectOperation.changed:
            self._notify_changed_package(entity)

    def _notify_new_resource(self, entity):
        try:
            resource_dict = toolkit.get_action("resource_show")(
                {"ignore_auth": True}, {"id": entity.id}
            )
        except toolkit.ObjectNotFound:
            return

        self._infer_format_and_submit(resource_dict)

    def _notify_changed_package(self, entity):
        try:
            pkg_dict = toolkit.get_action("package_show")(
                {"ignore_auth": True}, {"id": entity.id}
            )
        except toolkit.ObjectNotFound:
            return

        self._submit_resources_needing_ingest(pkg_dict)

    def _should_reingest(self, resource):
        """True when the resource has no content hash and no active datastore."""
        return not resource.get("hash") and not resource.get("datastore_active")

    def _submit_resources_needing_ingest(self, pkg_dict):
        for resource in pkg_dict.get("resources", []):
            if self._should_reingest(resource):
                log.info(
                    "Resource %s in package %s needs ingest — submitting to"
                    " DataPusher+",
                    resource.get("id"),
                    pkg_dict.get("id"),
                )
                self._infer_format_and_submit(resource)

    def _infer_format_and_submit(self, resource):
        """Infer format from the URL when missing, then submit."""
        if resource and not resource.get("format"):
            if not resource.get("url_type"):
                url_without_params = resource.get("url", "").split("?")[0]
                resource["format"] = (
                    url_without_params.split(".")[-1].lower()
                )
        p.get_plugin(REQUIRED_PLUGIN)._submit_to_datapusher(resource)
