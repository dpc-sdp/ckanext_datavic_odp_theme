# DataPusher+: fills the trigger gap in ckanext-datapusher-plus for
# resources that arrive via ``package_create``/``package_update`` (e.g.
# the ckanext-syndicate push from the Data Directory to this ODP).
#
# CKAN core does not call ``after_resource_create`` for resources created
# inline via ``package_create``/``package_update``, and the parent
# plugin's ``IResourceUrlChange.notify`` only fires for *changed* URLs,
# not for new resources. Syndication from the Data Directory reaches this
# portal through the CKAN API as ``package_create``/``package_update``
# calls, so those resources would otherwise never be submitted to
# DataPusher+.
#
# ``IDomainObjectModification.notify`` does fire for new Resource entities
# (dispatched by ``ckan.model.modification.DomainObjectModificationExtension``)
# and for the parent Package on ``changed``. We therefore:
#
#   * submit *new* Resource entities  -> covers inline resource creation
#     (syndication create, UI/API inline package_create/update); and
#   * on Package ``changed`` re-check the dataset's resources and submit
#     those still needing ingest (empty ``hash`` and inactive datastore)
#     -> covers the syndication *data change* path, where the Data
#     Directory pushes updated data via ``package_update`` and the
#     datastore has not yet been populated.
#
# The parent ``_submit_to_datapusher`` de-duplicates via its
# ``task_status`` pending/submitting guard, so it is safe for both the
# parent's own triggers and ours to fire for the same resource.

from __future__ import annotations

import logging

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.model.domain_object import DomainObjectOperation
from ckan.model.package import Package
from ckan.model.resource import Resource

from ckanext.datapusher_plus.plugin import DatapusherPlusPlugin

log = logging.getLogger(__name__)


class DatavicDatapusherPlusPlugin(DatapusherPlusPlugin, p.SingletonPlugin):
    p.implements(p.IDomainObjectModification)

    # IDomainObjectModification
    def notify(self, entity, operation):
        """Submit resources to DataPusher+ that the parent plugin misses.

        * ``Resource`` + ``new``: resources created inline via
          ``package_create``/``package_update`` (the syndication create
          path and any inline API/UI create). The parent's
          ``after_resource_create`` / ``IResourceUrlChange.notify`` do not
          fire for these.

        * ``Package`` + ``changed``: fired reliably whenever any of the
          dataset's resources are new/changed/deleted. Used to catch the
          syndication *data change* path, where updated data arrives via
          ``package_update`` and the resource still needs ingest.

        Resource ``changed`` is intentionally ignored: in-place URL changes
        are handled by the parent's ``IResourceUrlChange.notify``, and the
        re-ingest case is covered via the reliable Package ``changed``
        signal. ``deleted`` never needs a DataPusher+ run.
        """
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

    def _submit_resources_needing_ingest(self, pkg_dict):
        """Submit resources which hash = '' and datastore_active = False.

        This is the syndication re-ingest path: the Data Directory pushes
        updated data via ``package_update`` and the datastore has not yet
        been populated for the resource.
        """
        current_resources = pkg_dict.get("resources", [])

        for resource in current_resources:
            if resource.get("hash") == "" and not resource.get("datastore_active"):
                log.info(
                    "Resource %s in package %s has empty hash and inactive"
                    " datastore — submitting to DataPusher+",
                    resource.get("id"),
                    pkg_dict.get("id"),
                )
                self._infer_format_and_submit(resource)

    def _infer_format_and_submit(self, resource):
        """Infer the resource format from its URL if missing, then submit.

        DataPusher+'s ``_submit_to_datapusher`` silently no-ops when
        ``format`` is missing (see
        ``DatapusherPlusPlugin._submit_to_datapusher``). Syndicated
        resources can arrive without a format set, so without this
        fallback they would never reach the download stage that could
        detect a mimetype.
        """
        if resource and not resource.get("format"):
            if not resource.get("url_type"):
                url_without_params = resource.get("url", "").split("?")[0]
                resource["format"] = url_without_params.split(".")[-1].lower()
        self._submit_to_datapusher(resource)

    def _submit_to_datapusher(self, resource_dict):
        """Submit a resource, tolerating inline resources with no url_type.

        The parent gate skips resources whose ``url_type == "datapusher"``
        (datastore-managed API resources). Inline resources created via
        ``package_create``/``package_update`` can arrive without a
        ``url_type``; we set a sentinel that passes the parent gate, then
        remove it so it is never persisted back onto the resource.
        """
        resource_dict.setdefault("url_type", "datavic_datapusher")
        resource_dict.setdefault("format", "")

        try:
            return super()._submit_to_datapusher(resource_dict)
        finally:
            if resource_dict.get("url_type") == "datavic_datapusher":
                resource_dict.pop("url_type", None)
