/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9871428571428571, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "PERF-02 Abrir inicio de sesión"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-03 Reservar el mismo horario"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-02 Registrar reservación"], "isController": false}, {"data": [0.5, 500, 1500, "PERF-03 Iniciar sesión"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-03 Abrir formulario"], "isController": false}, {"data": [0.9833333333333333, 500, 1500, "PERF-02 Iniciar sesión"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-02 Abrir formulario"], "isController": false}, {"data": [0.88, 500, 1500, "PERF-01 Iniciar sesión"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-01 Abrir inicio de sesión"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-01 Consultar mis reservaciones"], "isController": false}, {"data": [1.0, 500, 1500, "PERF-03 Abrir inicio de sesión"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 700, 0, 0.0, 70.26000000000002, 2, 980, 10.0, 417.0, 429.0, 778.8700000000001, 11.398794984530207, 111.21218106273409, 3.4625748045920863], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["PERF-02 Abrir inicio de sesión", 30, 0, 0.0, 5.3, 2, 22, 4.5, 8.900000000000002, 14.84999999999999, 22.0, 1.0369858278603525, 1.4369950095057034, 0.1326612729001037], "isController": false}, {"data": ["PERF-03 Reservar el mismo horario", 50, 0, 0.0, 44.28, 16, 92, 42.5, 71.6, 82.94999999999996, 92.0, 60.60606060606061, 139.90885416666669, 30.65814393939394], "isController": false}, {"data": ["PERF-02 Registrar reservación", 90, 0, 0.0, 10.522222222222226, 9, 30, 10.0, 11.0, 12.0, 30.0, 3.1642231832085224, 1.6748134426748233, 1.5975619001160215], "isController": false}, {"data": ["PERF-03 Iniciar sesión", 5, 0, 0.0, 831.0, 686, 980, 792.0, 980.0, 980.0, 980.0, 5.076142131979695, 3.5592480964467006, 1.9204076776649746], "isController": false}, {"data": ["PERF-03 Abrir formulario", 50, 0, 0.0, 8.5, 4, 30, 7.0, 17.0, 20.449999999999996, 30.0, 47.214353163361665, 122.04633646128424, 12.170606114258735], "isController": false}, {"data": ["PERF-02 Iniciar sesión", 30, 0, 0.0, 441.2333333333333, 407, 919, 425.0, 441.70000000000005, 662.6999999999997, 919.0, 1.0229132569558101, 0.7172380063420623, 0.3870887569046645], "isController": false}, {"data": ["PERF-02 Abrir formulario", 90, 0, 0.0, 5.522222222222223, 5, 9, 5.0, 6.0, 7.0, 9.0, 3.1642231832085224, 8.527025267640544, 1.0743114518510706], "isController": false}, {"data": ["PERF-01 Iniciar sesión", 50, 0, 0.0, 492.96, 410, 823, 429.0, 718.0, 787.5999999999998, 823.0, 1.6598061346434736, 1.1638093795644668, 0.6281004659905723], "isController": false}, {"data": ["PERF-01 Abrir inicio de sesión", 50, 0, 0.0, 5.219999999999999, 2, 9, 5.0, 8.0, 9.0, 9.0, 1.700564587443031, 2.356544091388341, 0.2175526962451534], "isController": false}, {"data": ["PERF-01 Consultar mis reservaciones", 250, 0, 0.0, 10.395999999999995, 9, 21, 10.0, 11.0, 13.899999999999977, 18.49000000000001, 8.407883231317683, 205.7344982280386, 1.863856927254994], "isController": false}, {"data": ["PERF-03 Abrir inicio de sesión", 5, 0, 0.0, 8.0, 4, 12, 8.0, 12.0, 12.0, 12.0, 384.61538461538464, 532.9777644230769, 49.20372596153847], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 700, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
