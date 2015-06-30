import twisted.trial.unittest
from twisted.internet.defer import inlineCallbacks
import unittest
import datetime

import webstress.client.http
from webstress.config.parser import Config

from ..support.config import std_sample_config, tps_config, workers_config

class TestHTTPClient(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.client = webstress.client.http.HTTP(encoding='utf8')

        # Local webserver spawned by `make test`
        self.url = "http://localhost:8000/"

        configuration = Config([{"name": "test", "body": std_sample_config}])
        self.config = configuration.configs["test"]

        for target in self.config["targets"]:
            self.client.add_target(target)

    @inlineCallbacks
    def test_records_request_duration(self):
        outer = {'called': False}
        def batch_callback(results, stats):
            self.assertTrue(hasattr(results[0], 'duration'))
            outer['called'] = True
        stats = yield self.client.hit(self.config, batch_callback=batch_callback)

        self.assertTrue(outer['called'])

    @inlineCallbacks
    def test_records_status_code(self):
        outer = {'called': False}
        def batch_callback(results, stats):
            self.assertTrue(
                results[-1].status_code, 200
            )
            outer['called'] = True

        stats = yield self.client.hit(self.config, batch_callback=batch_callback)

        self.assertTrue(outer['called'])


    @inlineCallbacks
    def test_gives_correct_number_of_results(self):
        stats = yield self.client.hit(self.config)

        self.assertEquals(
            stats.for_all_targets.for_all_codes['count'], 20
        )

    @inlineCallbacks
    def test_respects_worker_configuration(self):
        # This smells like a unit test to me but I can't be bothered writing a
        # web server that tells me how many active requests it has and dealing
        # with how unreliable that whole process will be, so I'm just going to
        # check the number of workers on the fetcher object. :(
        configuration = Config([{"name": "test", "body": workers_config}])
        self.config = configuration.configs["test"]

        stats = yield self.client.hit(self.config)

        self.assertEquals(len(self.client._fetcher.workers), 7)
