import twisted.trial.unittest

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

        self.url = "http://localhost:8000/"
        self.config = Config(config)

        self.webserver = webserver.WebServer()

    def tearDown(self):
        self.webserver.kill()

    def test_everything_at_once_because_i_hate_twisted(self):
        for target in self.config.targets:
            self.client.add_target(target)

        def callback(results):
            self.assertTrue(
                hasattr(results[-1], 'duration')
            )

            self.assertIsInstance(
                results[-1].success, bool
            )

            self.assertEquals(
                results[-1].status_code, 200
            )

        self.assertRaises(
            SystemExit,
            lambda: self.client.hit(5, callback=callback)
        )
