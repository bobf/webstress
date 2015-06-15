from json import dumps
from mock import MagicMock

from twisted.internet.defer import inlineCallbacks, gatherResults, fail
import twisted.trial.unittest
from twisted.web.client import getPage
from twisted.python.failure import Failure

import webstress.interfaces.web
import webstress.client.api
from webstress.interfaces.web_delegates import StressTestDelegate, Delegate, expose

from ..support.config import std_sample_config

class TestWeb(twisted.trial.unittest.TestCase):
    def setUp(self):
        self.received_json = dumps(
            {"method": "test",
             "args": [1, 2, "a", "b"],
             "kwargs": {"foo": {'a': 1, 'b': 2},
                        "bar": [1, 2, [3, 4]]}}
        )

        class Delegate1(Delegate):
            @expose
            def test(self, *args, **kwargs):
                return "message"

        class Delegate2(Delegate):
            @expose
            def test(self, *args, **kwargs):
                pass

        self.delegate_1 = Delegate1()
        self.delegate_2 = Delegate2()

        webstress.client.api.update_config([
            dict(name="test", body=std_sample_config)])

    @inlineCallbacks
    def test_transport_delegates_received_calls(self):
        transport = webstress.interfaces.web.Transport()
        transport.register_delegate(self.delegate_1)
        transport.register_delegate(self.delegate_2)

        responses = yield gatherResults(
            transport.build_and_execute_responses(self.received_json))

        self.assertTrue(self.delegate_2.called)
        self.assertTrue(self.delegate_1.called)
        self.assertEqual(responses[0].result, "message")
        self.assertEqual(responses[1].delegate, self.delegate_2)

    @inlineCallbacks
    def test_cant_execute_unexposed_delegate_methods(self):
        transport = webstress.interfaces.web.Transport()
        transport.register_delegate(self.delegate_1)
        transport.register_delegate(self.delegate_2)

        json = dumps(
            {"method": "i_dont_exist",
             "args": [],
             "kwargs": {'target_names': ['test1']}}
        )

        responses = yield gatherResults(transport.build_and_execute_responses(json))

        self.assertFalse(self.delegate_1.called)
        self.assertFalse(self.delegate_2.called)
