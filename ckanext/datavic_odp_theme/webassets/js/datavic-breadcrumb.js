ckan.module("datavic-odp-breadcrumb", function ($, _) {
    "use strict";

    return {
        options: {},
        initialize: function () {
            // remove link for active breadcrumb item and nav-tav items
            $(".rpl-breadcrumbs__items li.active a, .page-header .nav-tabs li.active a").attr("href", "#")
        },
    };
});
