# Fills the trigger gap in ckanext-datapusher-plus for resources that arrive
# via ``package_create``/``package_update`` (e.g. API imports, UI package
# saves, bulk dataset updates).
#
# CKAN core does not call ``after_resource_create`` for inline resources, and
# ``IResourceUrlChange.notify`` only fires for changed URLs, not new ones.
#
# ``IDomainObjectModification.notify`` handles:
#
#   * ``Resource`` + ``new`` — submit inline resources the parent misses
#   * ``Package`` + ``changed`` — submit resources that still need ingest
#     (empty ``hash`` and inactive datastore) after a ``package_update``
#
# Per-resource ``changed`` is ignored (URL edits use ``IResourceUrlChange``).
# The parent's ``task_status`` guard prevents duplicate submissions.
from __future__ import annotations

import logging

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.model.domain_object import DomainObjectOperation
from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.datapusher_plus.plugin import DatapusherPlusPlugin

log = logging.getLogger(__name__)


class DatavicODPDatapusherPlusPlugin(DatapusherPlusPlugin, p.SingletonPlugin):
    p.implements(p.IDomainObjectModification)

    def notify(self, entity, operation):
        """Submit resources to DataPusher+ that the parent plugin misses."""
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
                resource["format"] = url_without_params.split(".")[-1].lower()
        self._submit_to_datapusher(resource)
