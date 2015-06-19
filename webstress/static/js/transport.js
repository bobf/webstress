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
