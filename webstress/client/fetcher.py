from __future__ import unicode_literals

from datetime import datetime
import random

from twisted.internet import reactor, task
from twisted.web.client import Agent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.web.http import HTTPClient
from twisted.internet import defer

from webstress.common.types import Result

class Client(HTTPClient):
    def __init__(self, deferred, target, url, each_callback=None):
        self._each_callback = each_callback
        self._deferred = deferred
        self._target = target
        self._url = url

    def dataReceived(self, data):
        # We don't care about the response body, we just want to consume it
        pass

    def connectionLost(self, reason):
        duration = (datetime.now() - self._target.start_time).total_seconds()

        result = Result(target=self._target,
                      success=self._target.success and reason.type == ResponseDone,
                      duration=duration,
                      url=self._url,
                      status_code=self._target.status_code)

        if self._each_callback is not None:
            self._each_callback(result)

        self._deferred.callback(result)

class Fetcher(object):
    def __init__(self, encoding):
        self.agent = Agent(reactor)
        self.each_callback = None
        self.targets = []
        self.encoding = encoding

    def add_targets(self, targets):
        for target in targets:
            for _ in xrange(target.hits):
                self.targets.append(target)
        # Order shouldn't matter ?
        random.shuffle(self.targets)

    def get(self, target, method="GET", headers=None):
        if headers is None:
            headers = dict()
        target.start_time = datetime.now()
        url = target.url
        d = self.agent.request(
            method.encode(self.encoding),
            url.encode(self.encoding),
            Headers(headers),
            None)
        complete_callback, complete_errback = self.get_callbacks(target)

        d.addCallback(complete_callback, url)
        d.addErrback(complete_errback, url)

        return d

    def get_callbacks(self, target):
        def callback(response, url):
            target.success = (response.code == 200)

            target.status_code = response.code

            d = defer.Deferred()
            client = Client(d, target, url, self.each_callback)
            response.deliverBody(client)

            return d

        def errback(_response, url):
            target.success = False

            duration = (datetime.now() - target.start_time).total_seconds()
            result = Result(
                target=target,
                success=False,
                duration=duration,
                url=url,
                status_code=target.status_code)
            return result

        return callback, errback

    def results(self, tps=None):
        if tps is not None:
            # Throttle transactions per second
            delay = 1.0 / tps
            deferreds = []
            for i, target in enumerate(self.targets):
                def get(target, i):
                    def closure():
                       return task.deferLater(reactor, delay * i, self.get, target)
                    return closure()
                deferreds.append(get(target, i))
            d = defer.gatherResults(deferreds)
        else:
            d = defer.gatherResults(self.get(target) for target in self.targets)
        return d
