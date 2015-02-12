// import Nevow.Athena

MyModule.MyWidget = Nevow.Athena.Widget.subclass('MyModule.MyWidget');

MyModule.MyWidget.methods(
    function result(self, argument) {
        document.getElementById('athena:1').innerHTML += "<br/>Duration: " + argument[0].duration
        return argument;
    },
    function all_results(self, argument) {
        return argument;
    }
    );

MyModule.MyWidget.method(
    'clicked',
    function(self) {
        self.callRemote('receive',
            JSON.stringify({
                method: 'launch_test',
                args: [],
                kwargs: {targets: ["target_from_config_file"]}
            }));
    });
