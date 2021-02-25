  jQuery(document).ready(function() {
    jQuery('#btn-mobile-menu-close').on('click', function(){
        jQuery('body').css('overflow', '');
        jQuery('#mobile-menu').removeClass('rpl-site-header--open').addClass('hidden');
        jQuery('#main-menu').show();
    });

    jQuery('#btn-mobile-menu-open').on('click', function(){
        jQuery('body').css('overflow', 'hidden');
        jQuery('#mobile-menu').addClass('rpl-site-header--open').removeClass('hidden');
        jQuery('#main-menu').hide();
    });

    function closeAllDropdowns() {
        jQuery('.rpl-search-form__filters .rpl-checklist__combobox--expanded').removeClass('rpl-checklist__combobox--expanded');
        jQuery('.rpl-search-form__filters .rpl-checklist__main-row.expanded').removeClass('expanded');
        jQuery('.rpl-search-form__filters .rpl-checklist__list--dropdown').css('display', 'none');
    }

    function showDropdown(target) {
        closeAllDropdowns();
        jQuery(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').css('display', 'block');
        jQuery(target + ' .rpl-checklist__main-row').addClass('expanded');
        jQuery(target + ' .rpl-checklist__combobox').addClass('rpl-checklist__combobox--expanded');
    }

    function hideDropdown(target) {
        jQuery(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').css('display', 'none');
        jQuery(target + ' .rpl-checklist__main-row').removeClass('expanded');
        jQuery(target + ' .rpl-checklist__combobox').removeClass('rpl-checklist__combobox--expanded');
    }

    jQuery('body').on('click', function(e) {
        closeAllDropdowns();
    });

    jQuery('.rpl-checklist .rpl-checklist__main-row button').on('click', function(e) {
        target = '#' + jQuery(this).attr('data-checklist');
        showDropdown(target);
        return false;
    });

    jQuery('.rpl-checklist button.rpl-checklist__single-item').on('click', function(e) {
        name = jQuery(this).find('span').text();
        value = jQuery(this).attr('data-value');
        target = '#' + jQuery(this).attr('data-target');
        checklist = '#' + jQuery(this).attr('data-checklist');

        if (jQuery(target).val() != value) {
            jQuery(target).val(value);
            jQuery(checklist).find('button span.rpl-visually-hidden').remove();
            jQuery(this).append('<span class="rpl-visually-hidden">(Selected)</span>');
            jQuery(checklist + ' .rpl-checklist__combobox .rpl-checklist__main-row button span').text(name);
            jQuery(checklist + ' .rpl-checklist__combobox .rpl-checklist__list-row.is-checked').removeClass('is-checked');
            jQuery(this).parent().addClass('is-checked');
            jQuery(checklist + ' .rpl-checklist__combobox .rpl-checklist__list-row button.rpl-checklist__single-item--selected').removeClass('rpl-checklist__single-item--selected');
            jQuery(this).addClass('rpl-checklist__single-item--selected');

            if (jQuery(this).attr('data-checklist') == 'checklist-order-by') {
                jQuery('.rpl-search-form input[name="sort"]').val(value);
                jQuery('.rpl-search-form form').submit();
            }
        }

        hideDropdown(checklist);
        return false;
    });

    jQuery('button.rpl-clearform').on('click', function(e) {
        jQuery('#organization').val('');
        jQuery('#groups').val('');
        jQuery('#res_format').val('');
        jQuery('input[name="q"]').val('');
        jQuery('.rpl-checklist__combobox').each(function() {
            var value = jQuery(this).find('.rpl-checklist__list-row button.default span').text();
            jQuery(this).find('.rpl-checklist__main-row button span').text(value);
        });
        jQuery('.rpl-checklist__combobox .rpl-checklist__list-row button span.rpl-visually-hidden').remove();
        jQuery('.rpl-checklist__combobox .rpl-checklist__list-row button.rpl-checklist__single-item--selected').removeClass('rpl-checklist__single-item--selected');
        jQuery('.rpl-checklist__combobox .rpl-checklist__list-row.is-checked').removeClass('is-checked');
        e.preventDefault();
    });

    jQuery('button.rpl-search-form__show-filters').on('click', function(e) {
        var expandedClass = 'rpl-search-form__show-filters--expanded';
        if (jQuery(this).hasClass(expandedClass)) {
            jQuery(this).removeClass(expandedClass);
            jQuery(this).attr('aria-expanded', false);
            jQuery('div.rpl-search-form__filters').hide();
        }
        else {
            jQuery(this).addClass(expandedClass);
            jQuery(this).attr('aria-expanded', true);
            jQuery('div.rpl-search-form__filters').show();
        }
        e.preventDefault();
    });
  });