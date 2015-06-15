// import Nevow.Athena

if (typeof window.WS === 'undefined') window.WS = {};

(function () {
    TransportMaker.Dispatch = Nevow.Athena.Widget.subclass('TransportMaker.Dispatch');
    // We call this by invoking a `click` element on an athena element. The
    // only purpose of this is to create the transport widget and store it
    // somewhere we can use it. There is almost definitely a better way to do
    // this than invoking the event ourselves.
    TransportMaker.Dispatch.method(
        'init',
        function (self) {
            var d;
            d = self.callRemote('get_transport');

            d.addCallback(
                function (le) {
                    var d2;
                    d2 = self.addChildWidgetFromWidgetInfo(le);
                    d2.addCallback(function (widget) {
                        WS.transport = widget;
                    });
                }
            );
            WS.transport = self;
        }
    );

    $(function () {
        $(".transport-init").click();
    });
})();
