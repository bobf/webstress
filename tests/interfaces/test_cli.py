import sys
from StringIO import StringIO

import twisted.trial.unittest

import webstress.interfaces.cli

from ..support.config import std_sample_config

from twisted.internet.defer import inlineCallbacks, gatherResults, fail

class TestCli(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.config_file = StringIO(std_sample_config)
        sys.stdout = self.stdout = StringIO()

    def test_run(self):
        # twisted.internet.task.react finishing up
        self.assertRaises(SystemExit, webstress.interfaces.cli.run, config_file=self.config_file)

        self.stdout.seek(0)
        output = self.stdout.read()

        # Let's just make sure that something useful was output to the terminal
        self.assertTrue('...' in output)
        self.assertTrue('Nadir' in output)
        self.assertTrue('Count' in output)
        self.assertTrue('Mean' in output)
