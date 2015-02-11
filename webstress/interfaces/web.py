from twisted.application import service, internet
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from nevow import athena, loaders, tags as T

import webstress


class MyElement(athena.LiveElement):
    jsClass = u'MyModule.MyWidget'
    docFactory = loaders.stan(T.div(render=T.directive('liveElement')))

    def __init__(self, *a, **kw):
        super(MyElement, self).__init__(*a, **kw)
        reactor.callLater(5, self.myEvent)

    def myEvent(self):
        print 'My Event Firing'
        self.callRemote('echo', 12345)

class MyPage(athena.LivePage):
    docFactory = loaders.stan(T.html[
        T.head(render=T.directive('liveglue')),
        T.body(render=T.directive('myElement'))])

    def render_myElement(self, ctx, data):
        f = MyElement()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def child_(self, ctx):
        return MyPage()


