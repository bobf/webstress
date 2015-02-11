from twisted.application import service, internet
from twisted.internet.defer import Deferred
from nevow import athena, loaders, tags as T

import webstress

class MyElement(athena.LiveElement):
    docFactory = loaders.stan(T.div(render=T.directive('liveElement')))

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

