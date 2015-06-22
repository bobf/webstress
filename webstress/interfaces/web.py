# Most of the boilerplate taken from
# https://divmod.readthedocs.org/en/latest/products/nevow/athena/index.html
import json

from twisted.internet.defer import maybeDeferred
from twisted.python import log

from nevow import athena, loaders, static, tags as T

from webstress.interfaces.web_delegates import StressTestDelegate
from webstress.common.types import Response

delegates = [
    StressTestDelegate(),
]

class TransportMaker(athena.LiveElement):
    jsClass = u'TransportMaker.Dispatch'
    docFactory = loaders.xmlfile('webstress/templates/dashboard.xml')

    @athena.expose
    def get_transport(self):
        t = Transport()
        for delegate in delegates:
            t.register_delegate(delegate)
        t.setFragmentParent(self)
        return t

class Transport(athena.LiveElement):
    jsClass = u'Transport.Dispatch'
    docFactory = loaders.xmlfile('webstress/templates/transport.xml')
    _all_transports =[]

    def __init__(self, *args, **kwargs):
        super(Transport, self).__init__(*args, **kwargs)
        self._delegates = []
        self._all_transports.append(self)

    def register_delegate(self, delegate):
        self._delegates.append(delegate)
        delegate._transport = self

    def send(self, method, *args, **kwargs):
        self.callRemote(method, args, kwargs)

    def send_to_all(self, method, *args, **kwargs):
        to_remove = []
        for transport in self._all_transports:
            if transport.page is not None:
                transport.callRemote(method, args, kwargs)
            else:
                to_remove.append(transport)

        for transport in to_remove:
            # Remove stale transports
            self._all_transports.remove(transport)

    @athena.expose
    def receive(self, argument):
        self.build_and_execute_responses(argument)

        # Let delegates handle dispatch
        return None

    def build_and_execute_responses(self, argument):
        params = json.loads(argument)

        method = params["method"]
        args = params.get("args", [])
        kwargs = params.get("kwargs", {})

        responses = []

        for delegate in self._delegates:
            d = maybeDeferred(delegate._call, method, args, kwargs)
            def make_response(result):
                return Response(delegate, result)

            d.addCallback(make_response)
            responses.append(d)

        # We only really need this for testing
        return responses


class MyPage(athena.LivePage):
    docFactory = loaders.stan(T.html[
        T.head(render=T.directive('liveglue')),
        T.body(render=T.directive('transport_maker'))])

    child_js = static.File('webstress/static/js/')
    child_css = static.File('webstress/static/css/')

    def render_transport_maker(self, ctx, _data):
        f = TransportMaker()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def child_(self, ctx):
        return MyPage()
