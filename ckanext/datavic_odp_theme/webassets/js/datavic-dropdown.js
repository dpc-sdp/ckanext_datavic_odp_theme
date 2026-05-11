this.ckan.module("datavic-dropdown", function ($) {
    "use strict";

    return {
        options: {
            isMobile: false
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            $(".rpl-site-header__inner").addClass("dropdown-hidden");

            this.el.find(".vic-dropdown-menu .dropdown-toggle").click(this._onDropdownClick);
        },

        _onDropdownClick: function (e) {
            if (e.target.tagName === "SPAN") {
                e.target = $(e.target).parent()[0];
            }

            let dropdownItem = e.target;
            let openedItem = $(".dropdown.dropdown-shown").prev(".dropdown-toggle");
            let isCloseAction = e.target === openedItem[0];
            let isOpenAction = openedItem.length && !isCloseAction;

            let header;

            if (this.options.isMobile) {
                header = $("#mobile-menu").children(".rpl-site-header__inner");
            } else {
                header = $("#main-menu").children(".rpl-site-header__inner");

                let dropdown_top = header.offset().top + header.outerHeight(true) - 2;
                let dropdown_height = window.innerHeight - header[0].getBoundingClientRect().bottom - 20;

                $(dropdownItem).next(".dropdown").css("transform", `translate(40px, ${dropdown_top}px)`);
                $(dropdownItem).next(".dropdown").css("height", `${dropdown_height}px`);
            }

            this.el.find(".rpl-link.dropdown-toggle").each((_, el) => {
                if (dropdownItem === el) {
                    return;
                }

                $(el).next(".dropdown").hide();
                $(el).removeClass("show");
                $(el).next(".dropdown").removeClass("dropdown-shown");
            })

            $(dropdownItem).next(".dropdown").slideToggle(!isOpenAction ? 400 : 0);
            $(dropdownItem).toggleClass("show");
            $(dropdownItem).next(".dropdown").toggleClass("dropdown-shown");

            if ($(".rpl-link.dropdown-toggle.show").length) {
                header.removeClass("dropdown-hidden")
                header.addClass("dropdown-shown");
                $(document.body).addClass("rpl-u-viewport-locked");
            }
            else {
                header.addClass("dropdown-hidden")
                header.removeClass("dropdown-shown");
                $(document.body).removeClass("rpl-u-viewport-locked");
            }
        },
    };
});
