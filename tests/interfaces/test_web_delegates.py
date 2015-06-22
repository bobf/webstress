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

    @inlineCallbacks
    def test_launch_basic_test(self):
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

        response = (yield gatherResults(self.transport.build_and_execute_responses(json)))[0]

        self.assertTrue(self.delegate.called)
        self.assertTrue(response.result['uid'] == 9999)
        self.assertTrue(response.delegate is self.delegate)

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
