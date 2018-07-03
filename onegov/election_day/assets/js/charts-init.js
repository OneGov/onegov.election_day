var initBarChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var chart = barChart({
            data: data,
            interactive: true
        })(el);

        var embed_link = $(el).data('embed-link');
        var embed_source = $(el).data('embed-source');
        if (embed_link && embed_source) {
            appendEmbedCode(
                el,
                '100%',
                chart.height() + 50,
                embed_source,
                embed_link
            );
        }
    });
};

var initSankeyChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var inverse = $(el).data('inverse');
        var chart = sankeyChart({
            data: data,
            interactive: true,
            inverse: inverse
        })(el);

        var embed_link = $(el).data('embed-link');
        var embed_source = $(el).data('embed-source');
        if (embed_link && embed_source) {
            appendEmbedCode(
                el,
                '100%',
                chart.height() + 50,
                embed_source,
                embed_link
        );
        }
    });
};

var initGroupedChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var chart = groupedChart({
            data: data,
            interactive: true
        })(el);

        var embed_link = $(el).data('embed-link');
        var embed_source = $(el).data('embed-source');
        if (embed_link && embed_source) {
            appendEmbedCode(
                el,
                '100%',
                chart.height(),
                embed_source,
                embed_link
            );
        }
    });
};

var initEntitiesMap = function(el) {
    var mapurl =  $(el).data('mapurl');
    var dataurl =  $(el).data('dataurl');
    $.ajax({ url: mapurl }).done(function(mapdata) {
        $.ajax({ url: dataurl }).done(function(data) {
            var canton =  $(el).data('canton');
            var thumbs = $(el).data('thumbs');
            var label_left_hand = $(el).data('label-left-hand');
            var label_right_hand = $(el).data('label-right-hand');
            var label_expats = $(el).data('label-expats');
            var map = entitiesMap({
                mapdata: mapdata,
                data: data,
                canton: canton,
                interactive: true,
                thumbs: thumbs,
                label_left_hand: label_left_hand,
                label_right_hand: label_right_hand,
                label_expats: label_expats
            })(el);

            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                var ratio = map.width() / map.height();
                appendEmbedCode(el, 500, Math.floor(500 / ratio), embed_source, embed_link);
            }
        });
    });
};


var initDistrictsMap = function(el) {
    var mapurl =  $(el).data('mapurl');
    var dataurl =  $(el).data('dataurl');
    $.ajax({ url: mapurl }).done(function(mapdata) {
        $.ajax({ url: dataurl }).done(function(data) {
            var canton =  $(el).data('canton');
            var thumbs = $(el).data('thumbs');
            var gradient = $(el).data('gradient');
            var label_left_hand = $(el).data('label-left-hand');
            var label_right_hand = $(el).data('label-right-hand');
            var label_expats = $(el).data('label-expats');
            var map = districtsMap({
                mapdata: mapdata,
                data: data,
                canton: canton,
                interactive: true,
                thumbs: thumbs,
                gradient: gradient,
                label_left_hand: label_left_hand,
                label_right_hand: label_right_hand,
                label_expats: label_expats
            })(el);

            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                var ratio = map.width() / map.height();
                appendEmbedCode(el, 500, Math.floor(500 / ratio), embed_source, embed_link);
            }
        });
    });
};

(function($) {
    $(document).ready(function() {
        $('.bar-chart').each(function(ix, el) {
            initBarChart(el);
        });
        $('.grouped-bar-chart').each(function(ix, el) {
            initGroupedChart(el);
        });
        $('.sankey-chart').each(function(ix, el) {
            initSankeyChart(el);
        });
        $('.entities-map').each(function(ix, el) {
            initEntitiesMap(el);
        });
        $('.districts-map').each(function(ix, el) {
            initDistrictsMap(el);
        });
    });
})(jQuery);
