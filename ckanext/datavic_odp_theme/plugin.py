import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.datavic_odp_theme import helpers


class DatavicODPTheme(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IMiddleware, inherit=True)

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
        }

    # IMiddleware
    def make_middleware(self, app, config):
        return AuthMiddleware(app, config)


class AuthMiddleware(object):
    def __init__(self, app, app_conf):
        self.app = app

    def __call__(self, environ, start_response):
        # Redirect homepage (/) to /dataset
        if environ['PATH_INFO'] == '/':
            print('hello')
            environ['wsgiorg.routing_args'] = '', {'action': 'search', 'controller': 'package'}
        return self.app(environ, start_response)

