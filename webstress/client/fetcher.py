from datetime import datetime

from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.task import react
from twisted.internet.defer import Deferred
from twisted.internet import defer

from webstress.common.types import Result


class Fetcher(object):
    def __init__(self):
        self.agent = Agent(reactor)
        self.each_callback = None
        self.targets = []

    def add_targets(self, targets):
        for target in targets:
            for _ in xrange(target.hits):
                self.targets.append(target)

    def get(self, target, method="GET", headers={}):
        target._start_time = datetime.now()
        url = target.url
        d = self.agent.request(
            method,
            url,
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

        def complete(response, url):
            if not getattr(target, "success", None):
                target.success = False
            duration = (datetime.now() - target._start_time).total_seconds()

            result = Result(target=target,
                          success=target.success,
                          duration=duration,
                          url=url,
                          status_code=target.status_code)

            if self.each_callback is not None:
                self.each_callback(result)

            return result

        return success, complete

    def results(self):
        d = defer.gatherResults(self.get(target) for target in self.targets)
        return d

    def set_complete_callback(self, callback):
        self.complete_callback = callback
