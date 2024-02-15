this.ckan.module('datavicmain-image-upload-helptext', function ($) {
    return {
        options: {
            help_text: false,
        },
        initialize: function () {
            if (this.options.help_text) {
                this.button_url = $("a:contains('Link')")
                $('<div class="info-block">' +
                    '<i class="fa fa-info-circle"></i> ' +
                    this.options.help_text +
                    '</div>')
                    .insertAfter(this.button_url);
            }
        },
    };
});
