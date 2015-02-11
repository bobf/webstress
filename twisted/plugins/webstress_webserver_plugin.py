from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from nevow import appserver

import webstress.interfaces.web

class Options(usage.Options):
    optParameters = [["port", "p", 1235, "The port number to listen on."]]


class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "webstress"
    description = "HTTP stress tester - web interface"
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in myproject.
        """
        site = appserver.NevowSite(webstress.interfaces.web.MyPage())
        port = webstress.configuration["http_server"]["port"]
        return internet.TCPServer(port, site)


serviceMaker = MyServiceMaker()
