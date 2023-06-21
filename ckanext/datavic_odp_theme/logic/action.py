from __future__ import annotations

import ckan.plugins.toolkit as tk

from ckanext.datavic_odp_theme import jobs


@tk.chained_action
def organization_update(next_, context, data_dict):
    result = next_(context, data_dict)
    tk.enqueue_job(jobs.reindex_organization, [result["id"]])
    return result
