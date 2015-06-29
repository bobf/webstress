// import Nevow.Athena

if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    WS.COMPLETE = 1;
    WS.PENDING = 2;
    WS.WAITING = 3;
    WS.INACTIVE = 4;
    WS.STOPPED = 5;
    WS.targets = {};
    WS.active_tests = {};
    WS._count = 0;

    WS.util = {
        format: function (value, precision) {
            if (typeof value !== 'number') {
                return '';
            }
            return value.toPrecision(precision) || '';
        },
        format_bytes: function(bytes, si) {
            // Borrowed from: http://stackoverflow.com/a/14919494
            var thresh = si ? 1000 : 1024;
            if(Math.abs(bytes) < thresh) {
                return bytes + ' B';
            }
            var units = si
                ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
                : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
            var u = -1;
            do {
                bytes /= thresh;
                ++u;
            } while(Math.abs(bytes) >= thresh && u < units.length - 1);
            return bytes.toFixed(1)+' '+units[u];
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

                                if (points.tps_values && owner.series.length === 1) {
                                    owner.addAxis({
                                        labels: {
                                            style: {
                                                color: 'rgba(235, 47, 47, 1)'
                                            }
                                        },
                                        title: {
                                            style: {
                                                color: 'rgba(235, 47, 47, 1)'
                                            },
                                            text: 'Reported TPS'
                                        },
                                        opposite: true,
                                        max: 20,
                                        min: 0
                                    }, false);

                                    owner.addSeries({
                                        type: 'spline',
                                        name: 'Reported TPS',
                                        enableMouseTracking: false,
                                        marker: {
                                            enabled: true,
                                            fillColor: 'rgba(200, 25, 25, 0.2)',
                                            symbol: 'circle',
                                            radius: 3
                                        },
                                        yAxis: 1,
                                        xAxis: 0,
                                        lineWidth: 2,
                                        color: 'rgba(235, 47, 47, 0.4)',
                                        fillColor: 'rgba(235, 47, 47, 0.05)',
                                        dashStyle: 'Solid',
                                        zIndex: 3,
                                    });
                                }
                                if (points.tps_values) {
                                    owner.series[1].setData(points.tps_values.slice(), true);
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
                text: 'Successful Responses'
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
                    lineColor: 'rgba(100, 100, 100, 0.4)',
                    lineWidth: 1,
                    marker: {
                        enabled: false
                    }
                }
            },
            series: [{
                type: 'areaspline',
                name: 'Response time',
                enableMouseTracking: false,
                data: [{marker: {enabled: false}}],
                zIndex: 2
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
        },
        function stopped_test(self, args, kwargs) {
            var uid = kwargs.uid;
            if (WS.active_tests[uid]) {
                WS.active_tests[uid].config.setState({state: WS.STOPPED});
            }
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
