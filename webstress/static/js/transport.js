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

    WS.stats = {
        average: function (array) {
            var i, item, total, average;

            if (!array.length) return NaN;

            total = 0;
            for (i = 0; i < array.length; i ++) {
                item = array[i];
                total += item;
            }
            average = total / array.length;

            return average;
        },

        median: function (array) {
            var index;
            switch (array.length) {
                case 0:
                    return NaN;
                case 1:
                    return array[0];
            }

            array.sort(function (x, y) {
                return x - y;
            });

            index = array.length / 2;
            if (index % 1) {
                index = Math.ceil(index);
                return array[index];
            } else {
                return WS.stats.average([
                    array[index - 1],
                    array[index]
                ]);
            }
        },

        peak: function (array) {
            var i, item, peak = NaN;
            for (i = 0; i < array.length; i ++) {
                item = array[i];
                if (i === 0) peak = item;
                if (item > peak) peak = item;
            }
            return peak;
        },

        nadir: function (array) {
            var i, item, nadir = NaN;
            for (i = 0; i < array.length; i ++) {
                item = array[i];
                if (i === 0) nadir = item;
                if (item < nadir) nadir = item;
            }
            return nadir;
        },

        format: function (value, precision) {
            return value.toFixed(precision);
        }
    };

    WS.get_duration_stats = function (results) {
        var relevant = _.filter(results, function (x) {
                return x.success;
            }),
            durations = _.pluck(relevant, "duration");

        if (!durations.length) {
            return null;
        } else {
            return {
                average: WS.stats.average(durations),
                median: WS.stats.median(durations),
                peak: WS.stats.peak(durations),
                nadir: WS.stats.nadir(durations)
            };
        }
    };

    WS.get_uid = function () {
        return "" + ++WS._count;
    };

    Transport.Dispatch = Nevow.Athena.Widget.subclass('Transport.Dispatch');

    Transport.Dispatch.methods(
        function result(self, _, kwargs) {
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
                    duration_stats: WS.get_duration_stats(all_results)
                });
                target.setState({
                    results: results,
                    duration_stats: WS.get_duration_stats(results)
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
