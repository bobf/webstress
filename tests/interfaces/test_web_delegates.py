from json import dumps
from mock import MagicMock

import twisted.trial.unittest
from twisted.internet.defer import inlineCallbacks, gatherResults, fail

from webstress.interfaces.web_delegates import StressTestDelegate, Delegate, expose
import webstress.interfaces.web
import webstress.client.api

from ..support.config import std_sample_config, std_sample_config_2

class TestWebDelegates(twisted.trial.unittest.TestCase):
    def setUp(self):
        webstress.client.api.update_config([
            dict(name="test_config", body=std_sample_config),
            dict(name="test_config_2", body=std_sample_config_2)
        ])


        self.delegate = StressTestDelegate()
        self.transport = webstress.interfaces.web.Transport()
        self.transport.register_delegate(self.delegate)

    def _basic_test(self):
        self.transport.send = MagicMock(return_value=None)

        json = dumps(
            {"method": "launch_test",
             "args": [],
             "kwargs": {
                'uid': 9999,
                'config_name': 'test_config',
                'requested_targets': [
                    {"name": "test1", "uid": 1234}
                    ]
                }
            }
        )

        self.transport.callRemote = MagicMock()

        return gatherResults(self.transport.build_and_execute_responses(json))


    @inlineCallbacks
    def test_launch_basic_test(self):
        responses = yield self._basic_test()
        self.assertTrue(self.delegate.called)
        self.assertTrue(responses[0].result['uid'] == 9999)
        self.assertTrue(responses[0].delegate is self.delegate)

    @inlineCallbacks
    def test_list_available_tests(self):
        json = dumps(
            {"method": "list_configs"}
        )

        self.transport.callRemote = MagicMock()

        responses = yield gatherResults(self.transport.build_and_execute_responses(json))

        (method, params, _), __ = self.transport.callRemote.call_args

        self.assertTrue(method == 'configs')
        self.assertTrue(params[0]['name'] == 'test_config')
        self.assertTrue(params[1]['name'] == 'test_config_2')

    @inlineCallbacks
    def test_stop_test(self):
        test_d = self._basic_test()

        json = dumps(
            {"method": "stop_test",
             "kwargs": {
                'uid': webstress.configuration.configs['test_config'].uid
             }
            }
        )

        responses = yield gatherResults(self.transport.build_and_execute_responses(json))
        test_results = yield test_d

        result = test_results[0].result

        self.assertTrue(result['action'] == 'stopped_test')
        self.assertTrue(result['kwargs'] == 9999)

        # I don't know how else to be 100% sure that a test has stopped
        self.assertTrue(webstress.configuration.configs['test_config']._fetcher.cancelled)
