ckan.module('datavic-search-autocomplete', function ($) {
    'use strict';

    function follow(suggestion) {
        window.location.href = suggestion.href;
    }

    function formatLabel(type, q, item) {
        var text = $('<span>', {html: item.label}).text();
        switch (type) {
            case 'datasets':
                return $('<span>', {
                    html: text.replace(
                        new RegExp(
                            '(' + q.split(' ').filter(Boolean).join('|') + ')',
                            'gi'
                        ),
                        '<strong>$1</strong>'
                    ),
                });
                break;
            case 'categories':
                return $('<span>', {text: text}).append(
                    $('<span>', {text: '(' + item.type + ')'}).addClass('muted')
                );
                break;
            default:
                return item.label;
        }
    }

    return {
        activePosition: 0,
        suggestions: [],
        requestId: null,
        queries: [],
        isPending: null,
        options: {
            delay: 400,
            autocompleteInput: null,
            suggestionBox: null,
        },
        setup: function () {
            this.input = this.$(this.options.autocompleteInput);
            if (!this.input.length) {
                console.error(
                    '[search-autocomplete] input does not exist: %s',
                    this.options.autocompleteInput
                );
            }

            this.suggestionBox = this.$(this.options.suggestionBox);
            if (!this.suggestionBox.length) {
                console.error(
                    '[search-autocomplete] suggestion box does not exist: %s',
                    this.options.suggestionBox
                );
            }
        },
        initialize: function () {
            this.setup();

            $.proxyAll(this, /_on/);
            this.input.on({
                keyup: this._onKeyUp,
            });
            this.suggestionBox.on({
                keydown: this._onKeyDown,
            });
            var self = this
            $('body').on({
                click: self._onClick,
            });
        },
        _onClick: function (e) {
            this.cleanSchedule();
            this.dropSuggestionList();
        },
        _onKeyUp: function (e) {
            if (~e.key.indexOf('Arrow') || e.key === 'Escape') {
                return;
            }
            this.cleanSchedule();
            this.queries.push(e.target.value);
            this.scheduleRequest();
        },
        _onKeyDown: function (e) {
            switch (e.key) {
                case 'ArrowDown':
                    this.cycleSuggestions(+1);
                    e.preventDefault();
                    break;
                case 'ArrowUp':
                    this.cycleSuggestions(-1);
                    e.preventDefault();
                    break;
                case 'Tab':
                    this.cycleSuggestions(+1);
                    e.preventDefault();
                    break;
                case 'Enter':
                    if (this.activePosition) {
                        e.preventDefault();
                        this.pickActive();
                    }
                    break;
                case 'Escape':
                    this.cleanSchedule();
                    this.dropSuggestionList();
                    break;
                default:
                    return;
            }
        },
        cycleSuggestions: function (step) {
            this.setActive(this.activePosition + step);
        },
        pickActive: function () {
            var idx = this.activePosition - 1;
            var suggestion = this.suggestions[idx];
            if (!suggestion) {
                console.error('Index %s is out of bounds: %o', idx, this.suggestions);
                return;
            }
            follow(suggestion);
        },
        setActive: function (idx) {
            var cap = this.suggestions.length + 1;
            this.activePosition = idx === 0 ? 0 : ((idx % cap) + cap) % cap;
            this.suggestionBox.find('.selected').removeClass('selected');
            this.suggestionBox.find('.suggestions li').removeClass('active');
            if (this.activePosition !== 0) {
                this.suggestionBox
                    .find('.suggestions li a')
                    .eq(this.activePosition - 1)
                    .addClass('selected')
                    .focus()
                    .parent()
                    .addClass('active');
            }
        },
        cleanSchedule: function () {
            clearTimeout(this.requestId);
            this.requestId = null;
        },
        scheduleRequest: function () {
            if (this.isPending || !this.queries.length) {
                return;
            }
            var self = this;
            this.requestId = setTimeout(function () {
                self.isPending = true;
                self.el.addClass('pending-suggestions');
                var q = self.queries.splice(0).pop();
                self.sandbox.client.call(
                    'POST',
                    'search_autocomplete', {q: q, fq: self.options.fq},
                    function (data) {
                        self.isPending = false;
                        self.el.removeClass('pending-suggestions');
                        if (self.requestId === null) {
                            return;
                        }
                        self.buildSuggestionList(data.result, q);
                        self.scheduleRequest();
                    },
                    function (err) {
                        self.isPending = false;
                        self.el.removeClass('pending-suggestions');
                        console.error(err);
                        self.scheduleRequest();
                    }
                );
            }, this.options.delay);
        },
        buildSuggestionList: function (data, q) {
            this.setActive(0);
            this.suggestions = [].concat(data.datasets).concat(data.categories);
            if (this.suggestions.length) {
                this.el.addClass('active-suggestions');
            } else {
                this.el.removeClass('active-suggestions');
            }

            for (var key in data) {
                this.suggestionBox
                    .find('[data-section="' + key + '"] .suggestions')
                    .children()
                    .remove()
                    .prevObject.append(
                        data[key].map(function (item) {
                            return $('<li>').append(
                                $('<a>', {html: formatLabel(key, q, item), href: item.href})
                            );
                        })
                    );
            }
        },
        dropSuggestionList: function () {
            this.setActive(0);
            this.suggestions = [];
            this.suggestionBox.find('.suggestions').children().remove();
            this.el.removeClass('active-suggestions');
        },
    };
});
