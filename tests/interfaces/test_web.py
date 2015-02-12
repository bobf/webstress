from json import dumps
from mock import MagicMock

from twisted.internet.defer import inlineCallbacks, gatherResults
import twisted.trial.unittest
from twisted.web.client import getPage

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

        webstress.client.api.update_config(std_sample_config)

    @inlineCallbacks
    def test_transport_delegates_received_calls(self):
        transport = webstress.interfaces.web.TransportElement()
        transport.register_delegate(self.delegate_1)
        transport.register_delegate(self.delegate_2)

        responses = yield gatherResults(transport.receive(self.received_json))

        self.assertTrue(self.delegate_2.called)
        self.assertTrue(self.delegate_1.called)
        self.assertEqual(responses[0].result, "message")
        self.assertEqual(responses[1].delegate, self.delegate_2)

    @inlineCallbacks
    def test_stress_test_delegate(self):
        delegate = StressTestDelegate()
        transport = webstress.interfaces.web.TransportElement()
        transport.register_delegate(delegate)
        json = dumps(
            {"method": "launch_test",
             "args": [],
             "kwargs": {'targets': ['test1']}}
        )

        delegate._transport.send = MagicMock(return_value=None)

        responses = yield gatherResults(transport.receive(json))

        self.assertTrue(delegate.called)
        self.assertTrue(any(x.delegate is delegate for x in responses))
        self.assertTrue(any(hasattr(x.result[0], "duration") for x in responses))
