from twisted.internet.defer import inlineCallbacks
import twisted.trial.unittest

from ..support.config import (std_sample_config,
                              tps_config,
                              sensitive_config,
                              sensitive_but_exposed_config)

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

        config = webstress.configuration.configs["test"]
        stats = yield webstress.client.api.launch_test(
            config, config["targets"], batch_callback=batch_callback,
            batch_delay=0.5)

        self.assertTrue(fired['fired'])

    @inlineCallbacks
    def test_results_have_actual_url(self):
        all_results = []
        def batch_callback(results, stats):
            all_results.extend(results)

        config = webstress.configuration.configs["test"]
        stats = yield webstress.client.api.launch_test(
            config, config["targets"], batch_callback=batch_callback,
            batch_delay=0.5)

        self.assertEquals(len(all_results), 20)

        # Make sure that the same URL isn't being generated with our faked data
        # There is a chance that all URLs will be the same by coincidence, so
        # re-run this test if it fails - chances should be very slim !
        self.assertTrue(len(set(x.url for x in all_results)) > 1)

        # Make sure .url isn't re-generated each time
        self.assertTrue(all_results[0].url == all_results[0].url)

    @inlineCallbacks
    def test_transactions_per_second(self):
        configuration = Config([{"name": "tps_test", "body": tps_config}])

        config = configuration.configs["tps_test"]
        targets = config["targets"]

        start = datetime.datetime.now()

        results = yield webstress.client.api.launch_test(config, targets,
                        batch_delay=0.5)

        self.assertTrue(
            (datetime.datetime.now() - start).total_seconds() >= 2
        )

    @inlineCallbacks
    def test_statistics(self):
        config = webstress.configuration.configs["test"]
        all_stats = yield webstress.client.api.launch_test(config,
                          config["targets"], batch_delay=0.5)

        stats = all_stats.for_target("test1").for_code("200")

        # Not really sure what useful tests we can run on this. Let's just make
        # sure they exist and have at least some amount of coherence
        self.assertTrue(stats["nadir"] <= stats["peak"])
        self.assertTrue(stats["count"] == 10)
        self.assertTrue(stats["tps_mean"])
        self.assertTrue(all_stats.run_time)

    def test_sensitive_params_are_filtered_by_default(self):
        configs = [{"name": "test", "body": sensitive_config}]
        webstress.client.api.update_config(configs)

        all_configs = webstress.client.api.list_configs()
        self.assertNotEqual(
            all_configs[0]['targets'][0]['params'][0]['value'],
            'classified'
        )

    def test_only_specified_filter_params_are_applied(self):
        configs = [{"name": "test", "body": sensitive_but_exposed_config}]
        webstress.client.api.update_config(configs)

        all_configs = webstress.client.api.list_configs()
        params = all_configs[0]['targets'][0]['params']
        self.assertEqual(
            # Password not filtered as we specify our own filter param list
            params[0]['value'],
            'exposed'
        )
        self.assertNotEqual(
            # Name filtered as it is specified in filter param list
            params[1]['value'],
            'classified'
        )

    @inlineCallbacks
    def test_content_length_returned(self):
        config = webstress.configuration.configs["test"]
        all_stats = yield webstress.client.api.launch_test(
            config, config["targets"], batch_callback=self.noop)

        stats = all_stats.for_all_targets.for_all_codes

        self.assertTrue(stats["total_content_length"] > 0)
