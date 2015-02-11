from twisted.internet.defer import inlineCallbacks
import twisted.trial.unittest

from ..support.config import standard

import webstress.client.api

class TestAPI(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.noop = lambda *_, **__: None

    @inlineCallbacks
    def test_yields_results_to_callback(self):
        fired, fired['fired'] = {}, False
        def each_callback(result):
            fired['fired'] = True

        results = yield webstress.client.cli.run(standard, each_callback=each_callback)

        self.assertTrue(fired['fired'])

    @inlineCallbacks
    def test_results_have_actual_url(self):
        results = yield webstress.client.cli.run(
            standard, each_callback=self.noop)

        # Confirm fake-generated data is stored against individual result
        self.assertTrue(results[0].url != results[1].url)
        self.assertTrue(results[0].url == results[0].url)
