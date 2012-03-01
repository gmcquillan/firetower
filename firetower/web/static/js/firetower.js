var firetower = function() {
    var previousPoint = null;
    var totalsPreviousPoint = null;
    var timeSinceReload = 0;

    var tsConfig = {
        reloadEvery: 30,
        // Categories with counts lower than this won't be graphed
        filterThreshold: 10,
        timeSlice:  "minute",
        autoReload: false,
        graphMinutes: 0
    }

    var tsData = (function(){
        var totalData = {};
        var catData = {};
        var catMeta = {};

        var getCategoryMetadata = function(){
            $.ajax({
                url: "/categories/",
                async: false,
                success: function(jsonData, httpStatus, xhr){
                    for (catId in jsonData){
                        catMeta[catId] = jsonData[catId];
                    }
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
            var url_args = "?time_slice=" + tsConfig.timeSlice
            if (tsConfig.graphMinutes !== 0){
                var start = new Date();
                start.setMinutes(start.getMinutes() - tsConfig.graphMinutes)
                var end = new Date();
                url_args = (
                    url_args +
                    "&start=" + encodeURIComponent(start.toUTCString()) +
                    "&end=" + encodeURIComponent(end.toUTCString())
                )
            }

            return "/categories/timeseries/" + url_args;
        }

        var processCatTs = function(catId, tsList){
            catData[catId] = {
                ts: new Array(),
                total: 0
            };

            for (var i = 0; i < tsList.length; i++){
                date = localToGmt(tsList[i][0]);
                count = parseInt(tsList[i][1]);
                catData[catId]["total"] += count

                if (!(date in totalData)){
                    totalData[date] = 0;
                }
                totalData[date] += count;
                catData[catId]["ts"].push([date, count]);
            }
        }

        var getCatData = function(catProcessor, callback){
            var ts_url = getTimeseriesUrl();
            for (date in totalData){
                delete totalData[date];
            }
            for (catId in catData){
                delete catData[catId];
            }

            $.ajax({
                url: ts_url,
                success: function(returnedData, httpStatus, xhr){
                    for (catId in returnedData){
                        catProcessor(catId, returnedData[catId]);
                    }
                    callback();

                }
            });
        }

        return {
            totalData: totalData,
            catData: catData,
            catMeta: catMeta,
            getCategoryMetadata: getCategoryMetadata,
            getCatData: getCatData,
            processCatTs: processCatTs,
            gmtToLocal: gmtToLocal
        }
    }());

    var tsGraphing = (function(){
        var graphedCats = new Array();

        var toggleSeries = function(){
            var link = $(this);
            var catId = $(this).attr("id").replace("_link", "")
            var idx = graphedCats.indexOf(catId);

            if (idx > -1){
                // Removing a category
                graphedCats.splice(idx, 1);
            } else {
                // Re-displaying a category
                graphedCats.push(catId);
            }
            link.html(idx > -1 ? "+" : "-");
            $("#tooltip").remove();
            prepareGraphs();
            return false;

        }

        var buildLabel = function(catId) {
            var human_name = tsData.catMeta[catId]["human_name"];
            var holder = $("<span><a href='#'></a></span>");
            var link = holder.find("a")

            link.attr("id", catId + "_link");
            link.text(graphedCats.indexOf(catId) > -1 ? "+" : "-");
            link.addClass("toggleSeries");

            return tsData.catMeta[catId]["human_name"]+ "&nbsp;" + holder.html();
        }

        var prepareGraphs = function(){
            $("#loadingMsg").show();
            var chartData = new Array();

            for (var catId in tsData.catData){
                var ts = new Array();
                if (graphedCats.indexOf(catId) > -1){
                    ts = tsData.catData[catId]["ts"];
                }
                if (tsData.catData[catId]["total"] > tsConfig.filterThreshold){
                    chartData.push({
                        label: catId,
                        data: ts
                    });
                }
            }
            for (var i = 0; i < graphedCats.length; i++){
                var catId = graphedCats[i];

            }

            var totalChartData = new Array();
            for (date in tsData.totalData){
                totalChartData.push([date, tsData.totalData[date]])
            }

            totalChartData.sort(function(a,b){ return a[0]-b[0]; });
            drawAggChart(chartData);
            drawTotalsChart(totalChartData);
            writeCatTable();
            $(".toggleSeries").unbind("click");
            $(".toggleSeries").bind("click", toggleSeries);
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

        var writeCatTable = function() {
            for (catId in tsData.catData){
                if ($("tr#key_"+catId).length === 0){
                    var rowStr = '<tr class="keyRow" id="key_'+catId+'"></tr>';
                    $("#keyTable").append(rowStr);
                }
                var catName = tsData.catMeta[catId]["human_name"];
                var catTotal = tsData.catData[catId]["total"];

                var rowContents = [
                    '<td><a href="/category/'+catId+'/">'+catName+'</a></td>',
                    '<td>' + catTotal + '</td>'
                ].join("")
                $("#key_" + catId).html(rowContents);
            }
        }

        var handleConfig = function(){
            var numericFields = [
                "reloadEvery", "filterThreshold", "graphMinutes"
            ];
            for (var i = 0; i < numericFields.length; i++){
                var fieldId = numericFields[i];
                var fieldVal = $("#" + fieldId).val()
                tsConfig[fieldId] = fieldVal.length > 0 ? parseInt(fieldVal) : 0;
            }
            tsConfig["autoReload"] = $('#autoReload').is(':checked') ? true : false;
            tsConfig["timeSlice"] = $("#timeSlice").val();

            var info = [
                {
                    display: tsConfig.autoReload,
                    fieldId: "reload_status",
                    msg: "Firetower is reloading every "+tsConfig.reloadEvery+" seconds. It's been <span id='last_reload'></span> seconds since the last reload.",
                    notMsg: "Firetower is not automatically reloading."
                },
                {
                    display: tsConfig.filterThreshold > 0,
                    fieldId: "filterThreshold_status",
                    msg: "Firetower is filtering out any categories with fewer than "+tsConfig.filterThreshold+" hits.",
                    notMsg: "Firetower is not filtering out categories."
                },
                {
                    display: tsConfig.graphMinutes > 0,
                    fieldId: "graphMinutes_status",
                    msg: "Firetower is displaying the last "+tsConfig.graphMinutes+" minutes of hits.",
                    notMsg: "Firetower is displaying all the hits."
                },
                {
                    display: tsConfig.timeSlice.length > 0,
                    fieldId: "timeSlice_status",
                    msg: "Firetower is graphing hits in "+tsConfig.timeSlice+" chunks.",
                    notMsg: "Firetower."
                }

            ];

            for (var i = 0; i < info.length; i++){
                var infoObj = info[i];
                var elem = $("#" + infoObj.fieldId);
                if (infoObj.display){
                    elem.html(infoObj.msg);
                } else {
                    elem.html(infoObj.notMsg);
                }
            }
            tsData.getCatData(tsData.processCatTs, tsGraphing.prepareGraphs);

            return false;
        }

        var initialFormSetup = function() {
            var simpleIds = [
                "reloadEvery", "filterThreshold", "graphMinutes", "timeSlice"
            ];
            for (var i = 0; i < simpleIds.length; i++){
                $("#" + simpleIds[i]).val(tsConfig[simpleIds[i]]);
            }
            $("#autoReload").prop("checked", tsConfig["autoReload"]);
            handleConfig();
        }

        return {
            graphedCats: graphedCats,
            drawTotalsChart: drawTotalsChart,
            drawAggChart: drawAggChart,
            prepareGraphs: prepareGraphs,
            buildLabel: buildLabel,
            toggleSeries: toggleSeries,
            writeCatTable: writeCatTable,
            handleConfig: handleConfig,
            initialFormSetup: initialFormSetup
        }
    }());

    var showTooltip = function(div_id, x, y, contents) {
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

    var init = function(){
        $("#aggregatePlaceholder").bind("plotclick", function (event, pos, item) {
            if (item) {
                window.open('/category/' + item.series.label + "/?time_slice=" + timeSlice)
            }
        });

        $("#aggregatePlaceholder").bind("plothover", function (event, pos, item) {
            $("#x").text(pos.x.toFixed(2));
            $("#y").text(pos.y.toFixed(2));

            if (item) {
                if (previousPoint != item.dataIndex) {
                    previousPoint = item.dataIndex;

                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    var date = new Date(tsData.gmtToLocal(Math.floor(x)));
                    for(var cat in tsData.catData){
                        if (item.series.label == cat){
                            cat_name = tsData.catMeta[cat]["human_name"];
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


        $("#totalsPlaceholder").bind("plothover", function (event, pos, item) {
            $("#totalsX").text(pos.x.toFixed(2));
            $("#totalsY").text(pos.y.toFixed(2));

            if (item) {
                if (totalsPreviousPoint != item.dataIndex) {
                    totalsPreviousPoint = item.dataIndex;

                    $("#totalsTooltip").remove();
                    var x = item.datapoint[0].toFixed(2),
                        y = item.datapoint[1].toFixed(2);

                    var date = new Date(tsData.gmtToLocal(Math.floor(x)));
                    for(var cat in tsData.catData){
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

        tsData.getCategoryMetadata();
        for (catId in firetower.tsData.catMeta){
            tsGraphing.graphedCats.push(catId);
        }
        tsData.getCatData(tsData.processCatTs, tsGraphing.prepareGraphs);
        tsGraphing.initialFormSetup();

        setInterval(function() {
            if (tsConfig.autoReload){
                if (tsConfig.reloadEvery <= timeSinceReload){
                    timeSinceReload = 0;
                    tsData.getCategoryMetadata();
                    tsData.getCatData(tsData.processCatTs, tsGraphing.prepareGraphs);
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

    return {
        tsData: tsData,
        tsGraphing: tsGraphing,
        tsConfig: tsConfig,
        init: init
    }
}();
