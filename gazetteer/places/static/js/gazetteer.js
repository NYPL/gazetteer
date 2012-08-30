var map;
var geojsonMarkerOptions = {
    radius: 8,
    fillColor: "#00f",
    color: "#000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8
};

$(function() {
    $('.mapListSection').css({'opacity': 0});
    $('#jsonLink').hide();

    
    var osmUrl='http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    var osmAttrib='Map data © openstreetmap contributors';
    var osm = new L.TileLayer(osmUrl,{minZoom:1,maxZoom:18,attribution:osmAttrib});
    map = new L.Map('map', {layers: [osm], center: new L.LatLng(34.11577, -93.855211), zoom: 4 });
    jsonLayer = L.geoJson(null, {
        onEachFeature: function(feature, layer) {
            //console.log(feature);
            feature.properties.highlighted = false;
            var id = feature.properties.id;
            layer.on("mouseover", function(e) {
                var $row = $('#feature' + id);
                $row.addClass('highlighted');
                //console.log("FOOOOOOOO");                
                //console.log("entered " + id);
            });
            layer.on("mouseout", function(e) {
                var $row = $('#feature' + id);
                $row.removeClass("highlighted");
                //console.log("left " + id);
            });
        },
        pointToLayer: function(feature, latlng) {
            return L.circleMarker(latlng, geojsonMarkerOptions);
        }

    }).addTo(map);
//    map = new OpenLayers.Map('map', {});
//    var baseLayer = new OpenLayers.Layer.OSM( "Openstreetmap Base Layer");
////    map.addLayer(baseLayer);
//    var geojson_format = new OpenLayers.Format.GeoJSON();
//    var jsonLayer = new OpenLayers.Layer.Vector();

//    map.addLayers([baseLayer, jsonLayer]);
//    var center = new OpenLayers.LonLat(-95, 37.5).transform(
//                    new OpenLayers.Projection("EPSG:4326"),
//                    map.getProjectionObject()
//                ); 
//    map.setCenter(center, 4);
//    var mapControl = new OpenLayers.Control.SelectFeature(jsonLayer, {hover: true});
//    map.addControl(mapControl);
//    mapControl.activate();
//    jsonLayer.events.on({
//      'featureselected': onFeatureSelect,
//      'featureunselected': onFeatureUnselect
//    }); 


    $('#searchForm').submit(function(e) {
        e.preventDefault();
        var bbox = map.getBounds().toBBoxString();
        var search_term = $('#searchField').val();
        $('#searchField').addClass("loading");
        $('#searchTerm').text(search_term);
        $('#searchField').attr("disabled", "disabled");
        $('#mapList tbody').empty();
        var url = "/feature/search.json?" + 'bbox=' + bbox + '&q=' + search_term + '&srid=' + '4326' + '&count=20&page=' + $('#page_no').val();
        $('#jsonLink').attr("href", url); 
        $.getJSON("/feature/search.json", {
            'bbox': bbox,
            'q': search_term,
            'srid': 4326,
            'threshold': 0.5,
            'count': 20,
            'page': $('#page_no').val()
            }, function(features) {
            if ($('.mapListSection').css("opacity") == '0') {
                $('.mapListSection').animate({'opacity': '1'}, 1000);
                $('#jsonLink').show();
            }
            if (features.hasOwnProperty("error") && features.error != '') {
                alert(features.error);
                return;
            }

            $('#noOfResults').text(features.results);
            $('#currPageNo').text(features.current_page);
            $('#totalPages').text(features.pages);
            $('#searchField').removeAttr("disabled");
            $('#searchField').removeClass("loading");
            jsonLayer.clearLayers();
            jsonLayer.addData(features);
//            var headerRow = getHeaderRow();
//            console.log(response);
//            var currFeatures = jsonLayer.features;
//            jsonLayer.removeFeatures(currFeatures);
//            jsonLayer.addFeatures(geojson_format.read(features));
            for (var i=0; i<features.features.length;i++) {
                var f = features.features[i];
                var props = f.properties;
                var listItem = getRow(props);
                $('#mapList tbody').append(listItem);
            }             
        });
    });

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

    function getRow(props) {
        var $tr = $('<tr />').attr("id", "feature" + props.id).data("id", props.id).hover(function() {
            var id = $(this).attr("id");
            id = id.replace("feature", "");
            var layer = getFeatureById(id);
            layer.feature.properties.highlighted = true;
            jsonLayer.setStyle(styleFunc);
            //layer.feature.properties.highlighted = true;
        }, function() {
            var id = $(this).attr("id");
            id = id.replace("feature", "");
            var layer = getFeatureById(id);
            layer.feature.properties.highlighted = false;
            jsonLayer.setStyle(styleFunc);            
        });
        var $one = $('<td />').appendTo($tr);
        var $a = $('<a />').attr("href", "/admin/places/feature/" + props.id).text(props.preferred_name).appendTo($one);
    //    var $a2 = $('<a />').addClass("viewSimilar").attr("target", "_blank").attr("href", "/search_related?id=" + props.id).text("view similar").appendTo($one);
        $('<td />').text(props.feature_type).appendTo($tr);
        $('<td />').text(props.admin2).appendTo($tr);
        $('<td />').text(props.admin1).appendTo($tr);
        return $tr;     
    }




});


function getFeatureById(feature_id) {
    //var ret = false;
    //console.log("Feature_id", feature_id);
    //var id = feature_id.replace("feature", "");
    var ret = false;
    jsonLayer.eachLayer(function(layer) {
        if (layer.feature.properties.id == feature_id) {
            ret = layer;
        }
    });
    return ret;
}

function styleFunc(feature) {
    switch (feature.properties.highlighted) {
        case true:
            return {
                'color': '#f00',
                'fillColor': '#f00'                
            };
        case false:
            return {
                'color' : '#000',
                'fillColor': '#00f'
            }   
    } 
}


//function onFeatureSelect(f) {
//    var id = f.feature.attributes.id;
////    $('.highlightOverlay').hide().remove();
//  //  $('img').removeClass('mapSelect');
//    var $tr = $('#feature' + id);
//    $tr.css({"backgroundColor": "#C4DFFB"});
//}

//function onFeatureUnselect(f) {
//    var id = f.feature.attributes.id;
////    $('.highlightOverlay').hide().remove();
//  //  $('img').removeClass('mapSelect');
//    var $tr = $('#feature' + id);
//    $tr.css({"backgroundColor": "#ffffff"});    
//}

/*
function getLi(props) {
    var $li = $('<li />').addClass("mapListItem").attr("data-id", props.id);
    var $a = $('<a />').attr("target", "_blank").attr("href", "/admin/places/feature/" + props.id).text(props.preferred_name).appendTo($li);
    return $li;
}


function getHeaderRow() {
    var heads = ['Preferred Name', 'Feature Type', 'State', 'County']
    var $thead = $('<thead />');
}
*/
