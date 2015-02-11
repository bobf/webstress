from twisted.internet.defer import inlineCallbacks
import twisted.trial.unittest
from twisted.web.client import getPage

import webstress.interfaces.web

class TestWeb(twisted.trial.unittest.TestCase):
    def test_is_accessible(self):
        pass
