define(['Backbone', 'marionette', 'jquery', 'app/views/map', 'app/views/search', 'app/views/header', 'app/core/router', 'app/core/mediator', 'app/helpers/search', 'app/collections/recentplaces'], function(Backbone, Marionette, $, MapView, SearchView, HeaderView, GazRouter, mediator, searchHelper, RecentPlaces) {

    var app = new Marionette.Application({
        views: {},
        models: {},
        collections: {},
        user: {},
        helpers: {
            'search': searchHelper
        },
        mediator: mediator
    });

    app.addRegions({
        'map': '#mapBlock',
        'search': '#searchBlock',
        'results': '#mainResultsBlock',
        'content': '#mainContentBlock',
        'modal': '#lightBoxContent'
        //'results': '#resultsBlock'
    });
    
    app.on('initialize:after', function() {
        $.getJSON("/user_json", {}, function(user) {
            app.user = user;
            app.views.search = new SearchView();
            app.views.header = new HeaderView();
            app.collections.recentPlaces = new RecentPlaces();
            app.views.map = new MapView().render();
            app.router = new GazRouter();
            Backbone.history.start();
        });
    });

    
    return app;
});
