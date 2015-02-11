import twisted.trial.unittest
from twisted.internet.defer import inlineCallbacks
import unittest

import webstress.client.http
from webstress.config.parser import Config

from ..support import webserver

config = """
targets:
  - url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
      - key: arg2
        value:
          fake: name
  - url: http://localhost:8000/
    hits: 10
    params:
      - key: arg1
        value: 10
      - key: arg1
        value: 10
"""

class TestHTTPClient(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.client = webstress.client.http.HTTP()

        # Local webserver spawned by `make test`
        self.url = "http://localhost:8000/"

        self.config = Config(config)

        for target in self.config.targets:
            self.client.add_target(target)

    @inlineCallbacks
    def test_records_request_duration(self):
        result = yield self.client.hit()

        self.assertTrue(
            hasattr(result[-1], 'duration')
        )

    @inlineCallbacks
    def test_records_status_code(self):
        result = yield self.client.hit()

        self.assertTrue(
            result[-1].status_code, 200
        )

    @inlineCallbacks
    def test_gives_correct_number_of_results(self):
        result = yield self.client.hit()

        self.assertEquals(
            len(result), 20
        )
