import urlparse

import unittest

import webstress.config.parser

sample = """\
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
class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = webstress.config.Config(sample)

    def test_parse(self):
        self.assertEquals(
            self.config.targets[0].hits,
            10
        )

    def test_create_fake_values(self):
        value1 = self.config.targets[0].params[2].value
        value2 = self.config.targets[0].params[2].value
        self.assertNotEqual(
            value1,
            value2
        )

    def test_get_url(self):
        parsed = urlparse.urlparse(self.config.targets[1].url)
        self.assertEquals(
            urlparse.parse_qs(parsed.query),
            {'arg1': ['10', '10']}
        )
