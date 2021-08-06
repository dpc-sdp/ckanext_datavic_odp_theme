# ckanext-datavic-odp-theme
A custom CKAN extension theme for Data.vic.gov.au (Public)

## Installation

Add this repository as a sub-module to your main project repository:

        git submodule add git@github.com:salsadigitalauorg/ckanext_datavic_odp_theme.git ckan/default/src/ckanext-datavic-odp-theme

Activate the Python virtual environment:

        . /usr/lib/ckan/default/bin/activate

Install the CKAN extension:

        cd /usr/lib/ckan/default/src/ckanext-datavic-odp-theme

        python setup.py develop
        
*Add* `datavic_odp_theme` to plugins in /etc/ckan/default/development.ini & /etc/ckan/default/production.ini

        ckan.plugins = [...existing plugins...] datavic_odp_theme

Restart CKAN

        paster serve /etc/ckan/default/development.ini

Or... Restart Nginx & Apache:

        sudo service nginx stop
        sudo service apache2 stop
        sudo service apache2 start
        sudo service nginx start

## Additional Configuration Settings

### Trackers

#### Google Tag Manager

        ckan.google_tag_manager.gtm_container_id = GTM-...
        Or using lagoon environment files eg .lagoon.env.develop, .lagoon.env.master
#### Hotjar

        ckan.tracking.hotjar_enabled = true
        ckan.tracking.hotjar.hjid = ...
        ckan.tracking.hotjar.hjsv = ...

#### Monsido

        ckan.tracking.monsido_enabled = true
        ckan.tracking.monsido.domain_token = ...

## CSS & Grunt

This theme adds a CSS resource to CKAN via the `fanstatic` dir:

        ~/ckanext-datavic-odp-theme/ckanext/datavic_odp_theme/fanstatic/datavic_odp_theme.css

This CSS file is generated through a basic `grunt` configuration in:

        ~/ckanext-datavic-odp-theme/ckanext/datavic_odp_theme/grunt

CD into that directory and run `npm install` to install grunt and its dependencies.

Then compile the `.scss` files in the `ckanext-datavic-odp-theme/ckanext/datavic_odp_theme/grunt/sass` dir using:

        grunt
