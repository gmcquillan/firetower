var firetower = (function(){

    var timeSinceReload = 0;
    var reloadEvery = 0;
    // Stores category metadata
    var catData = new Array();
    // Categories with counts lower than this won't be graphed
    var filterThreshold = 0;
    // array consisting of category_id: category count
    var catCounts = new Array();
    // array of timestamp: count for all categories
    var totalCounts = new Array();
    var timeSlice = "minute";

    $("#slice_selection").val(timeSlice);

    var timeseriesData = new Array();
    // Hashmap holding the currently graphed timeseries
    var graphedData = new Array();

    var addSeries = function(){
        toggleSeries($(this), true);
        return false;
    }

    var killSeries = function(){
        toggleSeries($(this), false);
        return false;
    }

    var getCategoryMetadata = function(){
        $.ajax({
            url: "/api/categories/",
            async: false,
            success: function(jsonData, httpStatus, xhr){
                catData = JSON.parse(jsonData);
            }
        });
    }

    // Turn a local timestamp into a GMT stamp with the same time string
    // e.g. 2012 Dec 12 13:00 PST -> 2012 Dec 12 13:00 GMT
    // This means Flot will give local time on the x-axis
    var localToGmt = function(ts){
        var d = new Date(ts);
        var d1 = new Date(d.getTime() - (d.getTimezoneOffset()*60*1000));
        return d1.getTime();
    }

    // Inverse of localToGmt
    var gmtToLocal = function(ts){
        var d = new Date(ts);
        var d1 = new Date(d.getTime() + (d.getTimezoneOffset()*60*1000));
        return d1.getTime();
    }

    var getTimeseriesUrl = function(){
        var url_args = "?time_slice=" + timeSlice
        var last_x_minutes = $("#last_x_minutes").val();
        if (last_x_minutes.length > 0){
            var start = new Date();
            start.setMinutes(start.getMinutes() - parseInt(last_x_minutes))
            var end = new Date();
            url_args = (
                url_args +
                "&start=" + encodeURIComponent(start.toUTCString()) +
                "&end=" + encodeURIComponent(end.toUTCString())
            )
        }

        return "/api/categories/timeseries/" + url_args;
    }

    var toggleSeries = function(link, add){
        var link_id = link.attr("id");
        var cat_id = link_id.replace("_link", "")
        graphedData[cat_id] = add ? timeseriesData[cat_id] : new Array();
        loadGraphData();

        for (cat_id in graphedData){
            var link_id = "#" + cat_id + "_link";
            var new_link = $(link_id);
            var visible = graphedData[cat_id].length > 0;
            new_link.html(visible ? "-" : "+");
            if (!visible){
                new_link.attr("class", "addSeries")
            }
        }

        $('.addSeries').unbind('click')
        $('.killSeries').unbind('click')
        $('.addSeries').bind('click', addSeries)
        $('.killSeries').bind('click', killSeries)
        $("#tooltip").remove();
        return false;
    }

    var buildLabel = function(label, series) {
        var link = "";
        if (graphedData[label].length > 0){
            link = "<a id='" + label + "_link' class='killSeries' href='#'>-</a>"
        }
        else {
            link = "<a id='" + label + "_link' class='addSeries' href='#'>+</a>"
        }
        var human_name = catData[label]["human_name"];
        return human_name + "&nbsp;" + link;
    }

    var loadGraphData = function(){
        var filterThresholdStr = $("#filter_threshold").val();
        if (filterThresholdStr.length === 0){
            filterThresholdStr = "0";
        }
        filterThreshold = parseInt(filterThresholdStr);

        // Empty array to hold chart data
        var chartData = new Array();
        for (cat in graphedData) {
            // Store category name & data for chart
            if (catCounts[cat] > filterThreshold){
                chartData.push(
                    { label: cat, data: graphedData[cat] }
                )
            }
        }
        var totalChartData = new Array();
        for (ts in totalCounts){
            totalChartData.push([parseInt(ts), totalCounts[ts]])
        }
        totalChartData.sort(function(a,b){ return a[0]-b[0]; });

        drawAggChart(chartData);
        drawTotalsChart(totalChartData);
    }

    var getAggregateData = function() {
        $("#loadingMsg").show();
        getCategoryMetadata();
        timeSlice = $("#slice_selection").val();

        // Clear out the current key
        $(".keyRow").remove();

        var handler = $.ajax({
            url: getTimeseriesUrl(),
            success: function(returnedData, httpStatus, xhr){
                timeseriesData = JSON.parse(returnedData);
                totalCounts = new Array();
                catCounts = new Array();

                for (cat in timeseriesData){
                    var temp = new Array();
                    for (var i=0; i < timeseriesData[cat].length; i++){
                        var entry = timeseriesData[cat][i];
                        temp.push([localToGmt(entry[0]), entry[1]])
                    }
                    timeseriesData[cat] = temp;
                }

                for (cat in timeseriesData) {
                    if (!(cat in graphedData) || graphedData[cat].length > 0){
                        graphedData[cat] = timeseriesData[cat];
                    }

                    // Sum total instances per category
                    var catTotal = 0;
                    for (var i=0, arr; arr=timeseriesData[cat][i]; i++) {
                        catTotal += arr[1];
                        var totalKey = arr[0].toString()
                        if (!(totalKey in totalCounts)){
                            totalCounts[totalKey] = 0;
                        }
                        totalCounts[totalKey] += parseInt(arr[1]);
                    }
                    catCounts[cat] = catTotal;

                    // Get human-readable category name
                    getCategoryName(cat, catTotal);
                }
                loadGraphData();
                $('.addSeries').bind('click', addSeries)
                $('.killSeries').bind('click', killSeries)
            }
        });
    }

    var drawAggChart = function(chartData) {
        $("#loadingMsg").hide();
        $("#aggregatePlaceholder").height(400)
        $.plot(
            $("#aggregatePlaceholder"),
            chartData,
            {
                series: {
                    lines: { show: true },
                    points: { show: true }
                },
                xaxis: { mode: "time" },
                yaxis: { min: 1 },
                grid: { hoverable: true, clickable: true },
                legend: {
                    labelFormatter: buildLabel,
                    container: "#legend",
                    noColumns: 3
                }
            }
        );
    }

    var drawTotalsChart = function(chartData) {
        $("#loadingMsg").hide();
        $("#totalsPlaceholder").height(400)
        $.plot(
            $("#totalsPlaceholder"),
            [{label: "Total hits across all categories", data: chartData}],
            {
                series: {
                    lines: { show: true },
                    points: { show: true }
                },
                xaxis: { mode: "time" },
                yaxis: { min: 1 },
                grid: { hoverable: true, clickable: true },
                legend: {
                    container: "#totalsLegend"
                }
            }
        );
    }

    var getCategoryName = function(catId, catTotal) {
        var catName = catData[catId].human_name;
        writeAggKey(catId, catName, catTotal);
    }

    // Write key for aggregate chart
    var writeAggKey = function(catId, catName, catTotal) {
        // Add category name & totals to key
        if ($("tr#key_"+catId).length === 0){
            $("#keyTable").append('<tr class="keyRow" id="key_'+catId+'"></tr>');
        }

        $("#key_"+catId).html(
            [
                '<td><a href="/category/'+catId+'/?time_slice='+timeSlice+'">'+catName+'</a></td>',
                '<td>' + catTotal + '</td>'
            ].join("")
        );
    }

    function showTooltip(div_id, x, y, contents) {
        $('<div id="'+ div_id +'">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
    $("#aggregatePlaceholder").bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (item) {
            if (previousPoint != item.dataIndex) {
                previousPoint = item.dataIndex;

                $("#tooltip").remove();
                var x = item.datapoint[0].toFixed(2),
                    y = item.datapoint[1].toFixed(2);

                var date = new Date(gmtToLocal(Math.floor(x)));
                for(var cat in catData){
                    if (item.series.label == cat){
                        cat_name = catData[cat]["human_name"];
                    }
                }
                var tooltip_msg = (
                    "At " + date.toLocaleDateString() +
                    " " + date.toLocaleTimeString() +
                    " " + " category " + cat_name  +
                    " got " + y + " hits"
                );

                showTooltip(
                    "tooltip", item.pageX, item.pageY, tooltip_msg
                );
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    });

    var totalsPreviousPoint = null;
    $("#totalsPlaceholder").bind("plothover", function (event, pos, item) {
        $("#totalsX").text(pos.x.toFixed(2));
        $("#totalsY").text(pos.y.toFixed(2));

        if (item) {
            if (totalsPreviousPoint != item.dataIndex) {
                totalsPreviousPoint = item.dataIndex;

                $("#totalsTooltip").remove();
                var x = item.datapoint[0].toFixed(2),
                    y = item.datapoint[1].toFixed(2);

                var date = new Date(gmtToLocal(Math.floor(x)));
                for(var cat in catData){
                    if (item.series.label == cat){
                        cat_name = catData[cat]["human_name"];
                    }
                }
                var tooltip_msg = (
                    "At " + date.toLocaleDateString() +
                    " " + date.toLocaleTimeString() +
                    " " + " we had " + y + " errors."
                );

                showTooltip("totalsTooltip", item.pageX, item.pageY,
                    tooltip_msg
                );
            }
        }
        else {
            $("#totalsTooltip").remove();
            previousPoint = null;
        }
    });

    $("#aggregatePlaceholder").bind("plotclick", function (event, pos, item) {
        if (item) {
            window.open('/category/' + item.series.label + "/?time_slice=" + timeSlice)
        }
    });

    var init = function(){
        // Get default timeseries data for all categories
        // & draw chart
        getAggregateData();


        $("#filter_threshold").bind("keyup", loadGraphData)
        $("#last_x_minutes").bind("keyup", getAggregateData)
        $("#slice_selection").bind("change", getAggregateData)

        setInterval(function() {
            var reload_check = $("#reload_check");
            if (reload_check.is(':checked')){
                var reload_input = $("#reload_input");
                reloadEvery = parseInt(reload_input.val())
                if (reloadEvery < timeSinceReload){
                    timeSinceReload = 0;
                    getAggregateData();
                }
                else {
                    timeSinceReload += 1;
                    $("#last_reload").html(timeSinceReload);
                }
            }
            else{
                $("#last_reload").html("-");
            }
        }, 1000);
    }

    return init;
}());
