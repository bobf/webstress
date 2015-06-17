from __future__ import unicode_literals

from datetime import datetime
import random

from twisted.internet import reactor, task
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet import defer

from webstress.common.types import Result


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
        success_callback, complete_callback = self.get_callbacks(target)

        d.addCallback(success_callback)
        d.addBoth(complete_callback, url)

        return d

    def get_callbacks(self, target):
        def success(response):
            if response.code == 200:
                target.success = True
            target.status_code = response.code

        def complete(_response, url):
            if not getattr(target, "success", None):
                target.success = False
            duration = (datetime.now() - target.start_time).total_seconds()

            result = Result(target=target,
                          success=target.success,
                          duration=duration,
                          url=url,
                          status_code=target.status_code)

            if self.each_callback is not None:
                self.each_callback(result)

            return result

        return success, complete

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
