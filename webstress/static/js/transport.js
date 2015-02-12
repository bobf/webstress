// import Nevow.Athena

Transport.Dispatch = Nevow.Athena.Widget.subclass('Transport.Dispatch');

Transport.Dispatch.methods(
    function result(self, argument) {
        document.getElementById('athena:1').innerHTML += "<br/>Duration: " + argument[0].duration
        return argument;
    },
    function all_results(self, argument) {
        return argument;
    }
    );

Transport.Dispatch.method(
    'clicked',
    function(self) {
        self.callRemote('receive',
            JSON.stringify({
                method: 'launch_test',
                args: [],
                kwargs: {targets: ["target_from_config_file"]}
            }));
    });
