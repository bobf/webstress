// import Nevow.Athena

if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    WS.COMPLETE = 1;
    WS.PENDING = 2;
    WS.WAITING = 3;
    WS.INACTIVE = 4;
    WS.targets = {};
    WS.active_tests = {};
    WS._count = 0;

    WS.util = {
        format: function (value, precision) {
            return value.toFixed(precision) || '';
        },

        status_code_class: function (value) {
            if (isNaN(parseInt(value))) {
                switch (value) {
                    case "Failure":
                        return "failure";
                }
            }
            return "code-" + value.substr(0, 1);
        },

        severity: function (value) {
            if (typeof value !== "number") {
                return "";
            }

            if (value < 1) {
                return "low";
            } else if (value < 5) {
                return "medium";
            } else {
                return "high";
            }
        }
    };

    WS.get_uid = function () {
        return "" + ++WS._count;
    };

    WS.init_chart = function (chart_node, points_getter) {
        $(chart_node).highcharts({
            chart: {
                animation: false,
                events: {
                    load: function () {
                        var series = this.series[0],
                            chart = this;

                        setInterval(function () {
                            var points = points_getter();
                            series.setData(points);
                        }, 3000);
                    }
                }
            },
            title: {
                text: 'Peak response times'
            },
            yAxis: {
                title: {
                    text: 'Response time'
                }
            },
            xAxis: {
                title: {
                    text: 'Number of requests'
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    marker: {
                        enabled: false
                    },
                    fillColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
                        stops: [
                            [0, '#ed5365'],
                            [0.8, '#99ff99'],
                            [1, Highcharts.Color('#99ff99').setOpacity(0).get('rgba')]
                        ]
                    }
                }
            },
            series: [{
                type: 'area',
                name: 'Response time',
                data: [{marker: {enabled: false}}]
            }],
            credits: {
                enabled: false
            }
        });
    };

    Transport.Dispatch = Nevow.Athena.Widget.subclass('Transport.Dispatch');

    Transport.Dispatch.methods(
        function result(self, _arguments, kwargs) {
            var uid = kwargs.uid,
                result = kwargs.result,
                config = WS.active_tests[uid].config,
                target = WS.active_tests[uid][result.target.uid].target,
                results = target.state.results.slice();
                // We can probably do this more efficiently than copying arrays
                all_results = config.state.results.slice();

                results.push(result);
                all_results.push(result);

                config.setState({
                    state: WS.PENDING,
                    results: all_results,
                    stats: result.stats
                });
                target.setState({
                    results: results,
                    stats: result.stats
                });
        },
        function all_results(self, args, kwargs) {
            var uid = kwargs.uid,
                config = WS.active_tests[uid].config;

                config.setState({state: WS.COMPLETE});
        },
        function configs(self, argument) {
            WS.config_grid.setState({data: argument});
        }
    );

    WS.call_remote = function (method, parameters) {
        parameters = parameters || {};
        return WS.transport.callRemote(
            'receive',
            JSON.stringify({'method': method,
                            'args': parameters.args || [],
                            'kwargs': parameters.kwargs || {}
                            })
        );
    };

    $(function () {
        setTimeout(
            function () {
                WS.call_remote('list_configs');
            }, 0);
    });
})();
