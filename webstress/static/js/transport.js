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

    WS.average_response_time = function (results) {
        var i, total, average;
        total = 0;
        for (i = 0; i < results.length; i ++) {
            total += results[i].duration;
        }
        average = total / results.length;

        return average;
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
                    average: WS.average_response_time(all_results)
                });
                target.setState({
                    results: results,
                    average: WS.average_response_time(results)
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
