from __future__ import annotations

import logging

from ckan import model
from ckan.lib.search import rebuild, commit


log = logging.getLogger(__name__)


def reindex_organization(id_or_name: str) -> None:
    """Rebuild search index for all datasets inside the organization."""
    org = model.Group.get(id_or_name)

    if not org:
        log.warning("Organization with ID or name %s not found", id_or_name)
        return

    query = model.Session.query(model.Package.id).filter_by(owner_org=org.id)

    rebuild(package_ids=(p.id for p in query), force=True)
    commit()
