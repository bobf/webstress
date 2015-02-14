import os.path
import sys
import fnmatch

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.python import log
from nevow import appserver

import webstress.interfaces.web
import webstress.client.api

class Options(usage.Options):
    port_default = webstress.configuration["http_server"]["port"]
    optParameters = [["port", "p", port_default, "The port number to listen on.", int],
                     ["config-dir", "c", None, "Config directory (will load *.yaml)"]]

    optFlags = [["debug", None, "Debug mode - developer only"]]

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
        port = options["port"]
        if not options["config-dir"]:
            raise usage.UsageError("Must provide --config-dir")

        self.config_dir = options["config-dir"]
        self._debug = options["debug"]
        self.update_config()

        return internet.TCPServer(port, site)

    def update_config(self, config_dir=None):
        config_dir = config_dir or self.config_dir

        webstress.client.api.reload_config = self.update_config # Is this insane

        config_strings = []
        for path in os.listdir(os.path.expanduser(config_dir)):
            if fnmatch.fnmatch(path, "*.yaml"):
                full_path = os.path.join(config_dir, path)
                log.msg("Loading config: `%s`" % (full_path,))
                config_strings.append(open(full_path).read())

        webstress.client.api.update_config(
            config_string='\n'.join(config_strings))

        webstress.configuration.DEBUG = self._debug

serviceMaker = MyServiceMaker()
