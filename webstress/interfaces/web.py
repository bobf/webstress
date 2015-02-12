# Most of the boilerplate taken from
# https://divmod.readthedocs.org/en/latest/products/nevow/athena/index.html
import json

from twisted.application import service, internet
from twisted.internet.defer import Deferred, maybeDeferred
from twisted.internet import reactor
from twisted.python import log

from nevow import athena, loaders, tags as T

from webstress.interfaces.web_delegates import StressTestDelegate
from webstress.common.types import Response

delegates = [
    StressTestDelegate(),
]

class TransportElement(athena.LiveElement):
    jsClass = u'MyModule.MyWidget'
    docFactory = loaders.stan(T.div(render=T.directive('liveElement'))[
        T.input(type='submit', value='Push me',
            onclick='Nevow.Athena.Widget.get(this).clicked()')])

    def __init__(self, *args, **kwargs):
        super(TransportElement, self).__init__(*args, **kwargs)
        self._delegates = []

    def register_delegate(self, delegate):
        self._delegates.append(delegate)
        delegate._transport = self

    def send(self, method, *args, **kwargs):
        log.msg("Athena send: %s, %s, %s" % (method, args, kwargs))

        self.callRemote(method, args, kwargs)

    @athena.expose
    def receive(self, argument):
        self.build_responses(argument)

    def build_responses(self, argument):
        params = json.loads(argument)
        # We expect strict API compatibility:
        method = params["method"]
        args = params["args"]
        kwargs = params["kwargs"]

        log.msg("Athena receive: %s, %s, %s" % (method, args, kwargs))

        responses = []

        for delegate in self._delegates:
            try:
                d = maybeDeferred(delegate._call, method, args, kwargs)
                def make_response(result):
                    return Response(delegate, result)

                d.addCallback(make_response)
                responses.append(d)

            except AttributeError:
                continue
            except TypeError, e:
                log.msg("Ignoring TypeError for method `%s`, args: %s, "
                        "kwargs: %s" % (method, args, kwargs))
                log.msg(e)

        # We only really need this for testing
        return responses


class MyPage(athena.LivePage):
    docFactory = loaders.stan(T.html[
        T.head(render=T.directive('liveglue')),
        T.body(render=T.directive('myElement'))])

    def render_myElement(self, ctx, data):
        f = TransportElement()
        for delegate in delegates:
            f.register_delegate(delegate)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def child_(self, ctx):
        return MyPage()


