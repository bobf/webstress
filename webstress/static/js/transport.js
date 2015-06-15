// import Nevow.Athena

if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    WS.targets = {};
    WS.active_tests = {};
    WS._count = 0;

    WS.get_uid = function () {
        return "" + ++WS._count;
    };

    Transport.Dispatch = Nevow.Athena.Widget.subclass('Transport.Dispatch');

    Transport.Dispatch.methods(
        function result(self, args, kwargs) {
            var target = WS.active_tests[kwargs._uid].target,
                results = target.state.results.slice();

            results.push(args[0]);
            target.setState({results: results});
        },
        function all_results(self, argument) {
            return argument;
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
