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
    def test_batching_callbacks(self):
        fired, fired['fired'] = {}, False
        def batch_callback(results, stats):
            fired['fired'] = True
            self.assertTrue(isinstance(results, list))

        results = yield webstress.client.api.run(
            self.configs, batch_callback=batch_callback)

        self.assertTrue(fired['fired'])

    @inlineCallbacks
    def test_results_have_actual_url(self):
        results = yield webstress.client.api.run(
            self.configs, batch_callback=self.noop)

        # Confirm fake-generated data is stored against individual result
        # We have to hope that we don't get four of the exact same
        # random-generated value :)
        self.assertTrue(results[0].url != results[1].url or
                        results[1].url != results[2].url or
                        results[2].url != results[3].url
                        )
        # Make sure .url isn't re-generated each time
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

    @inlineCallbacks
    def test_statistics(self):
        results = yield webstress.client.api.run(
            self.configs, batch_callback=self.noop)

        result = results[0]

        # Not really sure what useful tests we can run on this. Let's just make
        # sure they exist and have at least some amount of coherence
        self.assertTrue(result.stats["200"]["nadir"] <= result.stats["200"]["peak"])
