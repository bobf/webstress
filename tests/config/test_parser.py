import urlparse

import unittest

import webstress.config.parser
from webstress.common.exceptions import NonUniqueTargetNames, NonUniqueConfigNames

from ..support.config import (std_sample_config,
                              non_unique_sample_config,
                              params_in_url_and_specified_config)

class TestConfig(unittest.TestCase):
    def setUp(self):
        configuration = webstress.config.Config([
            {"name": "test", "body": std_sample_config}])
        self.test_config = configuration.configs["test"]

    def test_parse(self):
        self.assertEquals(
            self.test_config["targets"][0].hits,
            10
        )

    def test_create_fake_values(self):
        value1 = self.test_config["targets"][0].params[2].value
        value2 = self.test_config["targets"][0].params[2].value
        self.assertNotEqual(
            value1,
            value2
        )

    def test_get_url(self):
        parsed = urlparse.urlparse(self.test_config["targets"][1].url)
        self.assertEquals(
            urlparse.parse_qs(parsed.query),
            {'arg1': ['10', '10']}
        )

    def test_unique_target_names(self):
        self.assertRaises(
            NonUniqueTargetNames,
            lambda: webstress.config.Config(
                [{"name": "test", "body": non_unique_sample_config}])
        )

    def test_unique_config_names(self):
        self.assertRaises(
            NonUniqueConfigNames,
            lambda: webstress.config.Config(
                [{"name": "test", "body": std_sample_config},
                 {"name": "test", "body": std_sample_config}])
        )

    def test_url_generation_correctly_concatenates_params(self):
        config = webstress.config.Config([
            {"name": "test", "body": params_in_url_and_specified_config}])
        self.assertEqual(
            config.configs["test"]["targets"][0].url,
            "http://localhost:8000/?foo=bar&bar=baz&arg1=10&arg2=20")
