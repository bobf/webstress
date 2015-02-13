import os.path

import twisted.trial.unittest

import twisted.plugins
from twisted.application.service import IServiceMaker
from twisted.plugin import getPlugins
list(getPlugins(IServiceMaker))

import webstress

class TestWebstressWebServerPlugin(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.config_dir = os.path.dirname(__file__) + "/support/configs"

    def test_loads_multiple_configs(self):
        twisted.plugins.webstress_webserver_plugin.serviceMaker.update_config(config_dir=self.config_dir)

        self.assertEqual(
            webstress.configuration.targets[0].name, "target_from_config_file")

