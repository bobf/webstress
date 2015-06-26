from twisted.internet.defer import inlineCallbacks, Deferred
import twisted.trial.unittest

import webstress.util.helpers

class MyException(Exception):
    pass

class Test(object):
    @webstress.util.helpers.traps(MyException)
    def errback(self, failure):
        return "should never see me"

class TestHelpers(twisted.trial.unittest.TestCase):
    @inlineCallbacks
    def test_traps_decorator(self):
        @webstress.util.helpers.traps(MyException)
        def errback(failure): return "all good"
        def callback(result): return result
        d = Deferred()
        d.addCallbacks(callback, errback)
        d.errback(MyException())
        result = yield d
        self.assertTrue(result == "all good")

    def test_traps_decorator_raises_unhandled_exceptions(self):
        @webstress.util.helpers.traps(MyException)
        def errback(failure): return failure
        def callback(result): return "all good"
        d = Deferred()
        d.addCallbacks(callback, errback)

        self.assertFailure(d, ValueError)

        d.errback(ValueError())

    def test_deals_with_instance_methods(self):
        t = Test()
        d = Deferred()
        d.addErrback(t.errback)

        self.assertFailure(d, ValueError)

        d.errback(ValueError())
