ckan.module("datavic-odp-advanced-search", function ($) {
    "use strict";

    return {
        options: {},
        initialize: function () {
            this.showDropdown = this.showDropdown.bind(this);
            var self = this;

            $('body').on('click', function (e) {
                self.closeAllDropdowns();
            }).bind(this);

            $('.rpl-checklist .rpl-checklist__main-row button').on('click', function (e) {
                var target = '#' + $(this).attr('data-checklist');
                self.showDropdown(target);
                return false;
            });

            $('.rpl-checklist button.rpl-checklist__single-item').on('click', function (e) {
                var name = $(this).find('span').text();
                var value = $(this).attr('data-value');
                var target = '#' + $(this).attr('data-target');
                var checklist = '#' + $(this).attr('data-checklist');

                if ($(target).val() != value) {
                    $(target).val(value);
                    $(checklist).find('button span.rpl-visually-hidden').remove();
                    $(this).append('<span class="rpl-visually-hidden">(Selected)</span>');
                    $(checklist + ' .rpl-checklist__combobox .rpl-checklist__main-row button span').text(name);
                    $(checklist + ' .rpl-checklist__combobox .rpl-checklist__list-row.is-checked').removeClass('is-checked');
                    $(this).parent().addClass('is-checked');
                    $(checklist + ' .rpl-checklist__combobox .rpl-checklist__list-row button.rpl-checklist__single-item--selected').removeClass('rpl-checklist__single-item--selected');
                    $(this).addClass('rpl-checklist__single-item--selected');

                    if ($(this).attr('data-checklist') == 'checklist-order-by') {
                        $('.rpl-search-form input[name="sort"]').val(value);
                        $('.rpl-search-form form').submit();
                    }
                }

                self.hideDropdown(checklist);
                return false;
            });

            $('button.rpl-clearform').on('click', function (e) {
                $('#organization').val('');
                $('#groups').val('');
                $('#res_format').val('');
                $('input[name="q"]').val('');
                $('.rpl-checklist__combobox').each(function () {
                    var value = $(this).find('.rpl-checklist__list-row button.default span').text();
                    $(this).find('.rpl-checklist__main-row button span').text(value);
                });
                $('.rpl-checklist__combobox .rpl-checklist__list-row button span.rpl-visually-hidden').remove();
                $('.rpl-checklist__combobox .rpl-checklist__list-row button.rpl-checklist__single-item--selected').removeClass('rpl-checklist__single-item--selected');
                $('.rpl-checklist__combobox .rpl-checklist__list-row.is-checked').removeClass('is-checked');
                e.preventDefault();
            });

            $('button.rpl-search-form__show-filters').on('click', function (e) {
                var expandedClass = 'rpl-search-form__show-filters--expanded';
                if ($(this).hasClass(expandedClass)) {
                    $(this).removeClass(expandedClass);
                    $(this).attr('aria-expanded', false);
                    $('div.rpl-search-form__filters').hide();
                }
                else {
                    $(this).addClass(expandedClass);
                    $(this).attr('aria-expanded', true);
                    $('div.rpl-search-form__filters').show();
                }
                e.preventDefault();
            });
        },

        showDropdown: function (target) {
            this.closeAllDropdowns();
            $(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').css('display', 'block');
            $(target + ' .rpl-checklist__main-row').addClass('expanded');
            $(target + ' .rpl-checklist__combobox').addClass('rpl-checklist__combobox--expanded');
            $(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').attr('aria-hidden', "false");
        },

        closeAllDropdowns: function () {
            $('.rpl-search-form__filters .rpl-checklist__combobox--expanded').removeClass('rpl-checklist__combobox--expanded');
            $('.rpl-search-form__filters .rpl-checklist__main-row.expanded').removeClass('expanded');
            $('.rpl-search-form__filters .rpl-checklist__list--dropdown').css('display', 'none');
            $('.rpl-search-form__filters .rpl-checklist__combobox .rpl-checklist__list--dropdown').attr('aria-hidden', "true");
        },

        hideDropdown: function (target) {
            $(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').css('display', 'none');
            $(target + ' .rpl-checklist__main-row').removeClass('expanded');
            $(target + ' .rpl-checklist__combobox').removeClass('rpl-checklist__combobox--expanded');
            $(target + ' .rpl-checklist__combobox .rpl-checklist__list--dropdown').attr('aria-hidden', "true");
        }
    };
});
