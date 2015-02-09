import twisted.trial.unittest

import webstress.client.http

from ..support import webserver

class TestHTTPClient(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.client = webstress.client.http.HTTP()

        self.url = "http://localhost:8000/"

        self.webserver = webserver.WebServer()

    def tearDown(self):
        self.webserver.kill()

    def test_everything_at_once_because_i_hate_twisted(self):
        self.client.add_url(self.url)
        self.client.add_url(self.url)
        self.client.add_url(self.url)
        self.client.add_url(self.url)
        def callback(results):
            self.assertIn('duration', results[-1])

            self.assertIsInstance(
                results[-1]['success'], bool
            )

            self.assertEquals(
                results[-1]['status_code'], 200
            )

        self.assertRaises(
            SystemExit,
            lambda: self.client.hit(5, callback=callback)
        )
