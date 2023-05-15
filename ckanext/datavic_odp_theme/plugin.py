import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.xloader.plugin import xloaderPlugin

from ckanext.datavic_odp_theme.logic import auth_functions, actions
from ckanext.datavic_odp_theme.views import get_blueprints
from ckanext.datavic_odp_theme.helpers import get_helpers


class DatavicODPTheme(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IActions)
    p.implements(p.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("webassets", "datavic_odp_theme")

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()

    # IActions

    def get_actions(self):
        return actions()

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()


@tk.blanket.auth_functions(auth_functions)
class DatavicODPThemeAuth(p.SingletonPlugin):
    """Register auth function inside separate extension.

    We are chaining auth functions from activity and overriding its templates
    at the same time. The former requires us to put our plugin after the
    activty, while the latter will work only if we put our plugin before the
    activity. The only way to solve this puzzle is to split the logic between
    two sub-plugins.

    """
    pass


class DatavicXLoaderPlugin(xloaderPlugin):
    p.implements(p.IPackageController, inherit=True)

    # IPackageController

    def after_dataset_create(self, context, pkg_dict):
        """Dataset syndication doesn't trigger the `after_resource_create` method.
        So here we want to run submit for each resource after dataset creation.
        """
        for resource in pkg_dict.get("resources"):
            self._submit_to_xloader(resource)

    def _submit_to_xloader(self, resource_dict):
        """The original method doesn't check if `url_type` is here. Seems like
        it's not here if we are calling it from the `after_dataset_create`.
        Just set a default url_type and delete after to be sure, that it doesn't break
        some core logic.

        Do not touch proper values, because it will definitely break something."""

        resource_dict.setdefault("url_type", "datavic_xloader")

        super()._submit_to_xloader(resource_dict)

        if resource_dict["url_type"] == "datavic_xloader":
            resource_dict.pop("url_type")
