this.ckan.module('datavic-slug-visible', function (jQuery) {
  return {
    options: {
      prefix: '',
      placeholder: '<slug>'
    },

    initialize: function () {
      var sandbox = this.sandbox;
      var options = this.options;
      var el = this.el;
      var _ = sandbox.translate;

      var slug = el.slug();
      var parent = slug.parents('.form-group');
      if (!(parent.length)) {
        return;
      }

      if (!parent.hasClass('error')) {
        parent.show();
      }

      // Watch for updates to the target field and update the hidden slug field
      // triggering the "change" event manually.
      sandbox.subscribe('slug-target-changed', function (value) {
        slug.val(value).trigger('change');
      });
    }
  };
});
