import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config

from ckanext.datavic_odp_theme import helpers
from ckanext.datavic_odp_theme.logic import auth_functions, actions
from ckanext.datavic_odp_theme.views import vic_odp, redirect_read


class DatavicODPTheme(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('webassets', 'datavic_odp_theme')

    # ITemplateHelpers

    def get_helpers(self):
        ''' Return a dict of named helper functions (as defined in the ITemplateHelpers interface).
        These helpers will be available under the 'h' thread-local global object.
        '''
        return {
            'organization_list': helpers.organization_list,
            'group_list': helpers.group_list,
            'format_list': helpers.format_list,
            'hotjar_tracking_enabled': helpers.hotjar_tracking_enabled,
            'monsido_tracking_enabled': helpers.monsido_tracking_enabled,
            'get_hotjar_hsid': helpers.get_hotjar_hsid,
            'get_hotjar_hjsv': helpers.get_hotjar_hjsv,
            'get_monsido_domain_token': helpers.get_monsido_domain_token,
            'get_ga_site': helpers.get_ga_site,
            'get_parent_site_url': helpers.get_parent_site_url,
            'release_date': helpers.release_date,
            'get_gtm_code': helpers.get_gtm_code,
            'get_digital_twin_resources': helpers.get_digital_twin_resources,
            'url_for_dtv_config': helpers.url_for_dtv_config,
            'get_google_optimize_id': helpers.get_google_optimize_id,
            'featured_resource_preview': helpers.featured_resource_preview,
        }

    # IMiddleware
    def make_middleware(self, app, config):
        return AuthMiddleware(app, config)

    # IAuthFunctions

    def get_auth_functions(self):
        return auth_functions()

    # IActions

    def get_actions(self):
        return actions()

    # IBlueprint
    def get_blueprint(self):
        # Check feature preview is enabled or not
        # If enabled add the redirect view for read pkg
        preview_redirect_enabled = toolkit.asbool(
            config.get('ckan.dataset.preview_redirect', 1)
            )
        if preview_redirect_enabled:
            vic_odp.add_url_rule( u'/dataset/<id>', view_func=redirect_read)
        return [vic_odp]


class AuthMiddleware(object):
    def __init__(self, app, app_conf):
        self.app = app

    def __call__(self, environ, start_response):
        # Redirect homepage (/) to /dataset
        if environ['PATH_INFO'] == '/':
            location = toolkit.h.url_for('dataset.search')
            headers = [('Location', location)]
            status = "301 Moved Permanently"
            start_response(status, headers)
            return []
        return self.app(environ, start_response)
