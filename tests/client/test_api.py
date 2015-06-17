from twisted.internet.defer import inlineCallbacks
import twisted.trial.unittest

from ..support.config import std_sample_config, tps_config

import webstress.client.api
from webstress.config.parser import Config

import datetime

class TestAPI(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.noop = lambda *_, **__: None
        self.configs = [{"name": "test", "body": std_sample_config}]

    @inlineCallbacks
    def test_yields_results_to_callback(self):
        fired, fired['fired'] = {}, False
        def each_callback(result):
            fired['fired'] = True

        results = yield webstress.client.api.run(
            self.configs, each_callback=each_callback)

        self.assertTrue(fired['fired'])

    @inlineCallbacks
    def test_results_have_actual_url(self):
        results = yield webstress.client.api.run(
            self.configs, each_callback=self.noop)

        # Confirm fake-generated data is stored against individual result
        self.assertTrue(results[0].url != results[1].url)
        self.assertTrue(results[0].url == results[0].url)

    @inlineCallbacks
    def test_transactions_per_second(self):
        configuration = Config([{"name": "tps_test", "body": tps_config}])

        config = configuration.configs["tps_test"]
        targets = config["targets"]

        start = datetime.datetime.now()

        results = yield webstress.client.api.launch_test(config, targets)

        self.assertTrue(
            (datetime.datetime.now() - start).total_seconds() >= 0.5
        )
