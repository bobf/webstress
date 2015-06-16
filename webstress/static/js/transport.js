// import Nevow.Athena

if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    WS.COMPLETE = 1;
    WS.INCOMPLETE = 2;
    WS.WAITING = 3;
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
        function result(self, args, kwargs) {
            var target = WS.active_tests[kwargs._uid].target,
                results = target.state.results.slice();

            results.push(args[0]);
            target.setState({results: results,
                             average: WS.average_response_time(results),
                             status: WS.INCOMPLETE
                            });
        },
        function all_results(self, args, kwargs) {
            var target = WS.active_tests[kwargs._uid].target;
            target.setState({results: args[0],
                             average: WS.average_response_time(args[0]),
                             status: WS.COMPLETE
                            });
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
