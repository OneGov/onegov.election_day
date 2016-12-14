var init_sankey_chart = function(el) {

    var offsetMargin = 6;
    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var height = 600;
    var svg = d3.select(el).append('svg')
        .attr('width', width)
        .attr('height', height + 15)
        .attr('xmlns', "http://www.w3.org/2000/svg")
        .attr('version', '1.1');
    var offset = width * 0.25;
    var scale = d3.scale.linear();
    var sankey = d3.sankey()
        .nodeWidth(25)
        .nodePadding(15)
        .size([width, height]);
    var node = null;
    var link = null;
    var path = null;
    var inverse = $(el).data('inverse') || false;

    $.ajax({ url: dataurl }).done(function(data) {

        if (data.nodes && data.links) {

            sankey.nodes(data.nodes)
                .links(data.links)
                .layout(1);

            // Add the nodes <g><rect><text></g>
            var count = 0;
            node = svg.append("g").selectAll(".node")
                .data(data.nodes)
                .enter().append("g")
                .attr("class", "node")
                .attr("id", function(d) { return 'node-' + count++; })
                .call(
                    d3.behavior.drag()
                        .origin(function(d) { return d; })
                        .on("dragstart", function() { this.parentNode.appendChild(this); })
                        .on("drag", function(d) {
                            d3.select(this).attr("transform", "translate(" + scale(d.x) + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
                            sankey.relayout();
                            link.attr("d", path);
                        })
                );

            // ... the bar
            var bar = node.append("rect")
                .attr("height", function(d) { return d.dy; })
                .attr("width", sankey.nodeWidth())
                .style("cursor", "move")
                .style("fill", "#999")
                .style("shape-rendering", "crispEdges");
            bar.append("title")
                .text(function(d) { return d.value; });
            bar.filter(function(d) { return d.active; })
                .style("fill", "#0571b0");

            // ... the inner value of the bar
            node.filter(function(d) { return d.display_value; })
                .append("text")
                .text(function(d) { return d.display_value; })
                .attr("x", 0)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dx", ".5em")
                .attr("dy", ".35em")
                .style("font-size", "14px")
                .style("font-family", "sans-serif")
                .style("fill", "#fff")
                .style("pointer-events", "none");

            // Add the node names to the left of the bars
            var name = node.filter(function(d) { return d.name; })
                .append("text")
                .text(function(d) { return d.name; })
                .attr("x", 0)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dx", inverse ? offsetMargin + sankey.nodeWidth() : -offsetMargin)
                .attr("dy", ".35em")
                .attr("text-anchor", inverse ? "start" : "end")
                .style("font-size", "14px")
                .style("font-family", "sans-serif")
                .style("pointer-events", "none");

            offset = d3.max(name[0], function(d) {return d.getBBox().width;}) || 0;

            scale.domain([0, width])
                 .range([
                     inverse ? width-offsetMargin-2*sankey.nodeWidth()-offset : offset+offsetMargin,
                     inverse ? 0 : width-2*offsetMargin
                 ]);

            node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });

            // Add the links
            path = sankey.link(
                scale,
                inverse ? -sankey.nodeWidth() : 0,
                inverse ? sankey.nodeWidth() : 0
            );
            link = svg.append("g").selectAll(".link")
                .data(data.links)
                .enter().append("path")
                .attr("class", "link")
                .attr("d", path)
                .attr("style", function(d) { return "stroke: #000; stroke-opacity: 0.2; fill: none; stroke-width: " + Math.round(Math.max(1, d.dy)) + "px"; })
                .sort(function(a, b) { return b.dy - a.dy; });

            link.append("title")
                .text(function(d) { return d.value; });

            // Fade-Effect on mouseover
            node.on("mouseover", function(d) {
            	link.transition()
                    .duration(700)
            		.style("opacity", 0.1);
            	link.filter(function(s) { return d.id == s.source.id; })
                    .transition()
                    .duration(700)
            		.style("opacity", 1);
            	link.filter(function(t) { return d.id == t.target.id; })
                    .transition()
                    .duration(700)
            		.style("opacity", 1);
            });
            node.on("mouseout", function(d) {
                link.transition()
                    .duration(700)
            		.style("opacity", 1);
            });
            link.on("mouseover", function(d) {
            	link.filter(function(s) { return s != d; })
                    .transition()
                    .duration(700)
            		.style("opacity", 0.1);
            });
            link.on("mouseout", function(d) {
                link.transition()
                    .duration(700)
            		.style("opacity", 1);
            });

            var download_link = $(el).data('download-link');
            if (download_link) {
                append_svg_download_link(el, $(el).html(), data.title, download_link);
            }

            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                append_embed_code(el, '100%', height + 50, embed_source, embed_link);
            }
        }
    });

    d3.select(window).on('resize.sankey', function() {
        if (node && link && path) {
            // Resize
            width = $(el).width();
            scale.range([offset+offsetMargin, width-2*offsetMargin]);
            scale.range([
                inverse ? width-offsetMargin-2*sankey.nodeWidth()-offset : offset+offsetMargin,
                inverse ? 0 : width-2*offsetMargin
            ]);

            svg.attr('width', width);
            node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });
            path = sankey.link(
                scale,
                inverse ? -sankey.nodeWidth() : 0,
                inverse ? sankey.nodeWidth() : 0
            );
            link.attr("d", path);
        }
    });
};

(function($) {
    $(document).ready(function() {
        $('.sankey-chart').each(function(ix, el) {
            init_sankey_chart(el);
        });
    });
})(jQuery);
