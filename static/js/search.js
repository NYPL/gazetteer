'use strict';

(function($) {

var map, jsonLayer;

$(function() {
    $('.mapListSection').css({'opacity': 0});
    $('#jsonLink').hide();

    var osm = new L.TileLayer($G.osmUrl,{minZoom:1,maxZoom:18,attribution:$G.osmAttrib});
    map = new L.Map('map', {layers: [osm], center: new L.LatLng($G.centerLat, $G.centerLon), zoom: $G.defaultZoom });

    //update search when map viewport changes
    map.on("moveend", function(e) {
        var center = map.getCenter();
        var zoom = map.getZoom();
        var urlData = queryStringToJSON(location.search);

        //this line is because moveend gets triggered when map is moved due to onpopstate(), in which case we don't want to call search again     
        if (urlData.lat == center.lat && urlData.lon == center.lng && urlData.zoom == center.zoom) {
            return;
        }

        //actually do the search in 250ms if user has not moved map any further                
        setTimeout(function() {
            var newCenter = map.getCenter()
            var newZoom = map.getZoom()
            if (center.lat == newCenter.lat && center.lng == newCenter.lng && zoom == newZoom) {
                submitSearch({
                    'bboxChanged': true
                });
            }
        }, 250);

    });
    

    //Define JSON layer
    jsonLayer = L.geoJson(null, {
        onEachFeature: function(feature, layer) {
            feature.properties.highlighted = false;
            var id = feature.properties.id;
            layer.on("mouseover", function(e) {
                var $row = $('#feature' + id);
                $row.addClass('highlighted');
            });
            layer.on("mouseout", function(e) {
                var $row = $('#feature' + id);
                $row.removeClass("highlighted");
            });
            layer.on("click", function(e) {
                var url = $G.placeUrlPrefix + feature.properties.id;
                location.href = url;
            });
        },
        pointToLayer: function(feature, latlng) {
            //Convert point fields to circle markers to display on map
            return L.circleMarker(latlng, $G.styles.geojsonDefaultCSS);
        }

    }).addTo(map);

    /*
    Function to submit search and display results
    Accepts options:
        pushState: if true (default), also push URL state.  
    */
    function submitSearch(options) {
        var o = $.extend({
            //'bboxChanged': false,
            'pushState': true                
        }, options);
    
        var currentState = queryStringToJSON(location.search);
        var search_term = $('#searchField').val();

        if ($.trim(search_term) === '') return; //if search term is empty, do nothing, return.

        var center = map.getCenter()
        var zoom = map.getZoom()
        var bbox = map.getBounds().toBBoxString();
        
        //if search term has changed from what's in the URL, set page no to 1
        if (currentState.hasOwnProperty("q")) {
            if (decodeURIComponent(currentState.q) != search_term) {
                $('#page_no').val('1');
            }                    
        }

        //Get page no
        var page_no = parseInt($('#page_no').val());        
        var totalPages = parseInt($('#totalPages').text());

        if (totalPages === 0) {
            page_no = 1;
        } else if (page_no > totalPages) {
            page_no = totalPages;
        }


        //Set 'loading' states        
        jsonLayer.clearLayers();
        $('#searchField').addClass("loading");
        $('#searchTerm').text(search_term);
        $('#searchField').attr("disabled", "disabled");
        $('#searchButton').attr("disabled", "disabled");
        $('#mapList tbody').empty();
        $('#currPageNo').text('*');
        
        //get URL to use for pushState
        var urlParams = "?" + 'q=' + encodeURIComponent(search_term) + '&lat=' + center.lat + '&lon=' + center.lng + '&zoom=' + zoom + '&page=' + page_no;

        if (o.pushState) {
            console.log("pushing state " + urlParams);
            history.pushState({}, "Gazetteer Search: " + search_term, urlParams);
        }
        document.title = "Gazetteer Search: " + search_term

        //FIXME: rationalize URLs ?
        //Get URL to use for GeoJSON feed
        var geojsonUrl = "?" + 'q=' + encodeURIComponent(search_term) + '&bbox=' + bbox + '&page=' + page_no;        
        var feedUrl = $G.apiBase + "search.json" + geojsonUrl;
        $('#jsonLink').attr("href", feedUrl); 

        $.getJSON($G.apiBase + "search.json", {
            'bbox': bbox,
            'q': search_term,
            //'srid': 4326,
            'threshold': 0.5,
            'count': 20,
            'page': page_no
            }, function(features) {

            //If search results area is hidden, show
            if ($('.mapListSection').css("opacity") == '0') {
                $('.mapListSection').animate({'opacity': '1'}, 1000);
                $('#jsonLink').show();
                //$('#updateSearch').show();
            }

            //If the server sent an 'error' property, alert it and return
            //FIXME: better handling of errors
            if (features.hasOwnProperty("error") && features.error != '') {
                alert(features.error);
                return;
            }
            
            //populate pagination details
            $('#noOfResults').text(features.total);
            $('#currPageNo').text(features.page);
            $('#totalPages').text(features.pages);
            if (features.total === 0) {
                $('#currPageNo').text('0');
                $('#totalPages').text('0');                
            }
            $('#searchField').removeAttr("disabled");
            $('#searchField').removeClass("loading");
            $('#searchButton').removeAttr("disabled");

            //Add features to map
            jsonLayer.addData(features);

            //add features to results table
            for (var i=0; i<features.features.length;i++) {
                var f = features.features[i];
                var props = f.properties;
                var listItem = getRow(props);
                $('#mapList tbody').append(listItem);
            }
                   
        });
    }

    //When search form is submitted, eg. by user pressing 'enter' in search field
    $('#searchForm').submit(function(e) {
        e.preventDefault();
        submitSearch();
    });    

    //Handle URL / window onpopstate
    window.onpopstate = function(obj) {
        var queryString = location.search;
        var data = queryStringToJSON(queryString);

        if (data.q) {
            $('#searchField').val(decodeURIComponent(data.q));
        }
        if (data.page) {
            $('#page_no').val(data.page);
        }

        //FIXME: better error handling for invalid values
        if (data.lat && data.lon) {
            if (!data.zoom) {
                data.zoom = 5; //if lat and lng exist, but zoom is missing, set to value of 5 (is this sane?)
            }
            map.setView([data.lat, data.lon], data.zoom);
        }
        submitSearch({
            'pushState': false
        });
    };

    //call window.onpopstate() on page load.
    window.onpopstate();


    /* pagination code */
    $('.first').click(function() {
        $('#page_no').val('1');
        $('#searchForm').submit();
    });

    $('.last').click(function() {
        var lastPage = parseInt($('#totalPages').text());
        $('#page_no').val(lastPage);
        $('#searchForm').submit();
    });

    $('.next').click(function() {
        var currPage = parseInt($('#page_no').val());
        var lastPage = parseInt($('#totalPages').text());
        if (currPage < lastPage) {
            $('#page_no').val(currPage + 1);
            $('#searchForm').submit();
        }
    });

    $('.previous').click(function() {
        var currPage = parseInt($('#page_no').val());
        if (currPage > 1) {
            $('#page_no').val(currPage - 1);
            $('#searchForm').submit();            
        }
    });
    /* pagination code end */

    //silly code to set the size of the table to fit in the viewport
    $(window).resize(function() {
        var $tbody = $('#mapList tbody');
        var topOffset = $tbody.offset().top;
        var footerHeight = $('#footer').height();
        var viewportHeight = $(window).height();
        $tbody.height(viewportHeight - (topOffset + footerHeight));
    });
    $(window).resize();

});


//function to return a jQuery DOM element for each feature row.
function getRow(props) {
    var $tr = $('<tr />').attr("id", "feature" + props.id).data("id", props.id).data("properties", props).hover(function() {
        var id = $(this).attr("id");
        id = id.replace("feature", "");
        var layer = getFeatureById(id);
        layer.feature.properties.highlighted = true;
        jsonLayer.setStyle(styleFunc);
        layer.bringToFront();
    }, function() {
        var id = $(this).attr("id");
        id = id.replace("feature", "");
        var layer = getFeatureById(id);
        layer.feature.properties.highlighted = false;
        jsonLayer.setStyle(styleFunc);            
    });
    var $one = $('<td />').addClass("col1").appendTo($tr);
    var $a = $('<a />').attr("href", $G.placeUrlPrefix + props.id).text(props.name).appendTo($one);
//    var $a2 = $('<a />').addClass("viewSimilar").attr("target", "_blank").attr("href", "/search_related?id=" + props.id).text("view similar").appendTo($one);
    $('<td />').addClass("col2").text(props.feature_code_name).appendTo($tr);
//    $('<td />').text(props.admin2).appendTo($tr);
//    $('<td />').text(props.admin1).appendTo($tr);
    return $tr;     
}


//get feature on map based on feature id
function getFeatureById(feature_id) {
    var ret = false;
    jsonLayer.eachLayer(function(layer) {
        if (layer.feature.properties.id == feature_id) {
            ret = layer;
        }
    });
    return ret;
}


//set styles for highlighted layer on map
function styleFunc(feature) {
    switch (feature.properties.highlighted) {
        case true:
            return $G.styles.geojsonHighlightedCSS;
        case false:
            return $G.styles.geojsonDefaultCSS;
    } 
}

//FIXME: move following utility functions somewhere, perhaps gazetteer.js
/*
Convert a JSON object to a URL query string
>>>var foo = {'var1': 'bar', 'var2': 'baz'}
>>> JSONtoQueryString(foo);
'?var1=bar&var2=baz'
*/
function JSONtoQueryString(obj) {
    var s = "?";
    for (var o in obj) {
        if (obj.hasOwnProperty(o)) {
            s += o + "=" + obj[o] + "&";
        }
    }
    return s.substring(0, s.length - 1);
}

/*
Convert a URL query string to a JSON object
>>>var foo = "/something/bla/?var1=bar&var2=baz";
>>>QueryStringToJSON(foo);
{'var1': 'bar', 'var2': 'baz'}
*/
function queryStringToJSON(qstring) {
    if (qstring.indexOf("?") == -1) {
        return {};
    }
    var q = qstring.split("?")[1];
    var args = {};
    var vars = q.split('&');
//    console.log(vars);
    for (var i=0; i<vars.length; i++) {
        var kv = vars[i].split('=');
        var key = kv[0];
        var value = kv[1];
        args[key] = value;
    }		
    return args;		
}


/*
>>>bboxFromString('-1,2,-5,6')
>>>[[2,-1],[6,-5]]

function bboxFromString(s) {
    var points = s.split(",");
    var southwest = new L.LatLng(points[1], points[0]);
    var northeast = new L.LatLng(points[3], points[2]);
    return [southwest, northeast]
}
*/

})(jQuery);

