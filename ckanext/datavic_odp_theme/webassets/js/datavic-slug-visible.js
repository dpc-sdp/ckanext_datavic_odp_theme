// Override of CKAN's slug-preview module
// src/ckan/ckan/public/base/javascript/modules/slug-preview.js
// to address hidden slug field on load, ensuring it is visible
// and updated when the target field changes.
this.ckan.module('datavic-slug-visible', function (jQuery) {
  return {
    initialize: function () {
      var sandbox = this.sandbox;
      var el = this.el;
      var slug = el.slug();

      // Watch for updates to the target field and update the hidden slug field
      // triggering the "change" event manually.
      sandbox.subscribe('slug-target-changed', function (value) {
        slug.val(value).trigger('change');
      });
    }
  };
});
