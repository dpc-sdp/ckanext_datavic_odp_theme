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
    }
