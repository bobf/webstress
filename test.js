// import Nevow.Athena

MyModule.MyWidget = Nevow.Athena.Widget.subclass('MyModule.MyWidget');

MyModule.MyWidget.methods(
    function echo(self, argument) {
        alert('Echoing ' + argument);
        return argument;
    });

MyModule.MyWidget.method(
    'clicked',
    function(self) {
        self.callRemote('echo', 'hello, world');
    });
