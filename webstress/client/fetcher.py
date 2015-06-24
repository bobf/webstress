from __future__ import unicode_literals

from datetime import datetime
import random
import collections
import weakref
from Queue import Queue, Empty as QueueEmpty

from twisted.internet import reactor, task
from twisted.web.client import Agent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.web.http import HTTPClient
from twisted.internet import defer
from twisted.python import log

from webstress.common.types import Result
from webstress.util import stats

class Client(HTTPClient):
    def __init__(self, deferred, target, url, stats_callback, each_callback=None):
        self._each_callback = each_callback
        self._deferred = deferred
        self._target = target
        self._url = url
        self._stats_callback = stats_callback

    def dataReceived(self, data):
        # We don't care about the response body, we just want to consume it
        pass

    def connectionLost(self, reason):
        end = datetime.now()

        success = self._target.success and reason.type == ResponseDone

        result = Result(target=self._target,
                      success=self._target.success and reason.type == ResponseDone,
                      start_time=self._target.start_time,
                      end_time=end,
                      url=self._url,
                      # Let's not treat status codes as numeric values
                      status_code=unicode(self._target.status_code))

        if reason.type != ResponseDone:
            stat_category = 'Failure'
        else:
            stat_category = unicode(result.status_code)

        self._stats_callback(stat_category, result)

        if self._each_callback is not None:
            self._each_callback(result)

        self._deferred.callback(result)

class Worker(object):
    def __init__(self, queue):
        self.queue = queue

    @defer.inlineCallbacks
    def start(self):
        while True:
            job = yield self.queue.get()
            if job is None:
                # I was asked to die
                break
            ready = yield job()

class Fetcher(object):
    def __init__(self, encoding):
        self.agent = Agent(reactor)
        self.batch_callback = None
        self.targets = []
        self.encoding = encoding
        self.timings = {}
        self._deque = collections.deque()
        self._batcher = None
        self._active_jobs = weakref.WeakSet()
        self._queue = defer.DeferredQueue()

    def add_targets(self, targets):
        """
        Add targets to test
        """
        for target in targets:
            for _ in xrange(target.hits):
                self.targets.append(target)
        # Order shouldn't matter ?
        random.shuffle(self.targets)


    def results(self, tps=None, max_active_jobs=None):
        """
        This is where everything is initiated and gathered when running a test
        """
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

        # Send results to clients in batches every one second
        self._batcher = task.LoopingCall(self.batch_results)
        self._batcher_d = self._batcher.start(1)

        d.addCallback(self.compile_results)

        d.addBoth(self.cleanup)

        self.create_workers(max_active_jobs)
        for worker in self.workers:
            worker.start()

        return d

    def update_stats(self, category, result):
        """
        Calculate statistics for each individual target and each individual
        category, i.e. 200 OK, Failure
        """
        self.timings.setdefault(result.target.name, {}
            ).setdefault(category, []
            ).append((result.start_time, result.end_time))

        self.timings.setdefault('__all__', {}
            ).setdefault(category, []
            ).append((result.start_time, result.end_time))

        result.stats = {}
        for target in self.timings:
            result.stats.setdefault(target, {})
            all_time_spans = []
            for key in self.timings[target]:
                time_spans = self.timings[target][key]
                result.stats[target][key] = stats.generate(time_spans)
                all_time_spans.extend(time_spans)

            result.stats[target]["__all__"] = stats.generate(all_time_spans)

    def create_workers(self, n):
        """
        Create `n` workers to run concurrent requests, consuming each job from
        a DeferredQueue `self.queue`

        This effectively limits the number of concurrent transactions
        """
        default = 5
        if n is None:
            log.msg("No max active jobs specified, defaulting to %s" % (default,))
            n = default
        log.msg("Spawning %s workers" % (n,))
        self.workers = [Worker(self._queue) for _ in xrange(n)]

    @property
    def active_job_count(self):
        return len([x for x in self._active_jobs if not x.called])

    def get(self, target, method="GET", headers=None):
        """
        Return a deferred that will be fired when the HTTP request has been
        picked up from the queue and finished processing by one of the workers
        """
        response_d = defer.Deferred()

        def closure():
            target.start_time = datetime.now()
            url = target.url
            d = self.agent.request(
                method.encode(self.encoding),
                url.encode(self.encoding),
                Headers(headers or dict()),
                None)
            complete_callback, complete_errback = self.get_callbacks(target)

            d.addCallback(complete_callback, url
                ).addErrback(complete_errback, url)

            self._active_jobs.add(d)

            def cb(result):
                response_d.callback(result)
                return result
            d.addCallback(cb)
            return d

        self._queue.put(closure)
        return response_d

    def get_callbacks(self, target):
        def callback(response, url):
            target.success = (response.code == 200)

            target.status_code = response.code

            d = defer.Deferred()
            client = Client(d, target, url, self.update_stats,
                            self.each_callback)
            response.deliverBody(client)

            return d

        def errback(_response, url):
            target.success = False

            end = datetime.now()
            result = Result(
                target=target,
                success=False,
                start_time=target.start_time,
                end_time=end,
                url=url,
                status_code=target.status_code)
            return result

        return callback, errback

    def each_callback(self, result):
        self._deque.appendleft(result)

    def batch_results(self):
        results = list(self._deque)

        if results:
            try:
                if self.batch_callback is not None:
                    result = max(
                        results,
                        key=(lambda x: x.stats['__all__']['__all__']['count']))
                    return self.batch_callback(results, result.stats)
            finally:
                self._deque.clear()

    def compile_results(self, results):
        return max(results, key=lambda x: x.stats['__all__']['__all__']['count']).stats

    def cleanup(self, results):
        # Make sure we at least send one batch before we stop
        self.batch_results()
        if self._batcher is not None:
            self._batcher.stop()

        for _ in xrange(len(self.workers)):
            # Ask all workers to die
            self._queue.put(None)

        return results
