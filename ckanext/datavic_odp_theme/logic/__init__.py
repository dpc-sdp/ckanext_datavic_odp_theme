from .auth import get
from . import action


def auth_functions():
    return dict(
        activity_list=get.vic_activity_list,
        package_activity_list=get.vic_package_activity_list,
        organization_activity_list=get.vic_organization_activity_list,
    )


def actions():
    return {
        "organization_update": action.organization_update,
        "package_update": action.package_update,
        "package_delete": action.package_delete,
        "resource_update": action.resource_update,
        "resource_create": action.resource_create,
        "datavic_list_incomplete_resources": action.datavic_list_incomplete_resources,
        "datavic_datatables_view_prioritize": action.datavic_datatables_view_prioritize,
        "resource_view_create": action.resource_view_create,
    }
