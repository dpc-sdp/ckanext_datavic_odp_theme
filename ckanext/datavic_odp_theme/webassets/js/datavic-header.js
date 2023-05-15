this.ckan.module("datavic-odp-header", function ($) {
    "use strict";

    return {
        options: {},
        initialize: function () {
            $('#btn-mobile-menu-close').on('click', function(){
                $('body').css('overflow', '');
                $('#mobile-menu').removeClass('rpl-site-header--open').addClass('hidden');
                $('#main-menu').show();
            });

            $('#btn-mobile-menu-open').on('click', function(){
                $('body').css('overflow', 'hidden');
                $('#mobile-menu').addClass('rpl-site-header--open').removeClass('hidden');
                $('#main-menu').hide();
            });
        },
    };
});
