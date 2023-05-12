import ckan.plugins as p
import ckan.plugins.toolkit as toolkit

from ckanext.datavic_odp_theme.logic import auth_functions, actions
from ckanext.datavic_odp_theme.views import get_blueprints
from ckanext.datavic_odp_theme.helpers import get_helpers


class DatavicODPTheme(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IAuthFunctions)
    p.implements(p.IActions)
    p.implements(p.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("webassets", "datavic_odp_theme")

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()

    # IAuthFunctions

    def get_auth_functions(self):
        return auth_functions()

    # IActions

    def get_actions(self):
        return actions()

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()
