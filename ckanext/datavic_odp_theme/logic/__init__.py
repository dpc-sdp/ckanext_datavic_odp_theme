from .auth import get
from . import action
from . import validators


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
    }


def get_validators():
    return {
        "datavic_organization_upload": validators.datavic_organization_upload
    }
