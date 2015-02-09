from datetime import datetime

from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.task import react
from twisted.internet.defer import Deferred
from twisted.internet import defer

class Fetcher(object):
    def __init__(self):
        self.agent = Agent(reactor)
        self.targets = []

    def add_targets(self, targets):
        self.targets.extend([dict(x) for x in targets]) # Deep copy

    def get(self, target, method="GET", headers={}):
        target["_start_time"] = datetime.now()
        d = self.agent.request(
            'GET',
            target["url"],
            Headers(headers),
            None)
        success_callback, complete_callback = self.get_callbacks(target)

        d.addCallback(success_callback)
        d.addBoth(complete_callback)

        return d

    def get_callbacks(self, target):
        def success(response):
            if response.code == 200:
                target["success"] = True
            target["status_code"] = response.code

        def complete(*a, **kw):
            if not target.get("success"):
                target["success"] = False
            target["complete"] = True
            target["duration"] = (datetime.now() - target.pop("_start_time")).total_seconds()

            if all(x.get("complete") for x in self.targets):
                self.complete()

        return success, complete

    def complete(self):
        self.complete_callback(self.targets)

    def gather_deferreds(self, reactor):
        d = Deferred()
        d = defer.gatherResults(self.get(target) for target in self.targets)
        return d

    def set_complete_callback(self, callback):
        self.complete_callback = callback

    def run(self):
        react(self.gather_deferreds)

