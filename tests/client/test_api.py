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
        webstress.client.api.update_config(self.configs)

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
        all_results = []
        def batch_callback(results, stats):
            all_results.extend(results)

        stats = yield webstress.client.api.run(
            self.configs, batch_callback=batch_callback)

        self.assertEquals(len(all_results), 20)
        # Confirm fake-generated data is stored against individual result
        # We have to hope that we don't get four of the exact same
        # random-generated value :)
        self.assertTrue(all_results[0].url != all_results[1].url or
                        all_results[1].url != all_results[2].url or
                        all_results[2].url != all_results[3].url
                        )
        # Make sure .url isn't re-generated each time
        self.assertTrue(all_results[0].url == all_results[0].url)

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
        stats = yield webstress.client.api.run(
            self.configs, batch_callback=self.noop)

        # Not really sure what useful tests we can run on this. Let's just make
        # sure they exist and have at least some amount of coherence
        self.assertTrue(stats["test1"]["200"]["nadir"] <= stats["test1"]["200"]["peak"])
        self.assertTrue(stats["test1"]["200"]["count"] == 10)
