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
        },

        calculate_stops: function (points) {
            var stops = [],
                peak = _.max(_.map(points, function (x) { return x[1]; }));
            stops.push.apply(stops, [
                peak >= 5 ? [1 - (5 / peak), '#ed5365'] : null,
                peak >= 1 ? [1 - (1 / peak), '#e8a633'] : null,
                [1, '#4c8f39']
            ]);

            return _.compact(stops);
        }
    };

    WS.get_uid = function () {
        return "" + ++WS._count;
    };

    WS.init_chart = function (chart_node, points_getter) {
        $(chart_node).highcharts({
            chart: {
                animation: true,
                events: {
                    load: function () {
                        var series = this.series[0],
                            chart = this,
                            that = this,
                            update;
                        update = (function (owner) {
                            return function () {
                                var points = points_getter(),
                                    stops = WS.util.calculate_stops(points.values),
                                    x_axis;

                                if (!owner.series) {
                                    // The chart got re-initialised
                                    clearInterval(that.interval);
                                    return;
                                }

                                if (!points.values) {
                                    return;
                                }

                                series.update({
                                    fillColor: {
                                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
                                        stops: stops
                                    }
                                });

                                x_axis = owner.xAxis[0];
                                if (x_axis.type !== points.type) {
                                    x_axis.update({type: points.type,
                                                   title: points.title}, true);
                                }

                                if (points.tps && owner.series.length === 1) {
                                    owner.addAxis({
                                        labels: {
                                            style: {
                                                color: 'rgba(252, 23, 65, 0.6)'
                                            }
                                        },
                                        title: {
                                            text: 'TPS'
                                        },
                                        opposite: true,
                                        max: 50
                                    }, false);

                                    owner.addSeries({
                                        type: 'line',
                                        name: 'TPS - Transactions [Launched] Per Second',
                                        yAxis: 1,
                                        color: 'rgba(252, 23, 65, 0.6)',
                                        dashStyle: 'ShortDot'
                                    });
                                }
                                if (points.tps) {
                                    owner.series[1].setData(points.tps.slice(), true);
                                }
                                owner.series[0].setData(points.values.slice());
                            }
                        })(that)

                        that.interval = setInterval(update, 3000);
                        // Fire a single update quickly after starting to give
                        // quicker feedback
                        setTimeout(update, 500);
                    }
                }
            },
            title: {
                text: 'Peak [successful] response times'
            },
            yAxis: {
                title: {
                    text: 'Response time'
                }
            },
            xAxis: {
                type: 'linear',
                title: {
                    text: ''
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                areaspline: {
                    lineColor: '#c2c2c2',
                    lineWidth: 1,
                    marker: {
                        enabled: false
                    }
                }
            },
            series: [{
                type: 'areaspline',
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
        function results(self, _arguments, kwargs) {
            var uid = kwargs.uid,
                stats = kwargs.stats,
                config;

                if (!WS.active_tests[uid]) {
                    // Pragmatism
                    return;
                }
                config = WS.active_tests[uid].config;

                config.setState({
                    state: WS.PENDING,
                    stats: stats
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
