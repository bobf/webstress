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

from webstress.common.types import Result, TestPolitelyStopped
from webstress.util import stats, helpers

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

        self._deferred.callback(None)

class Worker(object):
    """
    A worker that consumes closures from a DeferredQueue `queue`.

    When the closure is received it is executed and its result discarded.

    I can be provided with `delay_func` which I will use to get a minimum delay
    time before processing the next job.

    I die slowly when asked to, either when my stop() method is called, or None
    is fed to me by my queue.
    """
    def __init__(self, queue, delay_func=None):
        self.queue = queue
        self._delay_func = delay_func
        self._stopped = False
        self._stop_d = None

    @defer.inlineCallbacks
    def start(self):
        completed_time = datetime.max
        while True:
            job = yield self.queue.get()

            if job is None or self._stopped:
                # I was asked to die
                break

            if self._delay_func is not None:
                delay = self._delay_func() - max(
                    (datetime.now() - completed_time).total_seconds(),
                     0)
            if delay > 0:
                # Don't exceed TPS throttle
                _ = yield task.deferLater(reactor, delay, job)
            else:
                _ = yield job()
            completed_time = datetime.now()

        if self._stop_d is not None:
            # Notify my killer that I am dead
            self._stop_d.callback(None)

    def stop(self):
        """
        Die slowly. Wait until any remaining connections have completed and
        then notify my caller by triggering the returned deferred.
        """
        self._stopped = True
        self._stop_d = defer.Deferred()
        return self._stop_d

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
        self.stats = None
        self.cancelled = False
        self._delay = None

    def add_targets(self, targets):
        """
        Add targets to test
        """
        for target in targets:
            for _ in xrange(target.hits):
                self.targets.append(target)
        # Order shouldn't matter ?
        random.shuffle(self.targets)

    def results(self, config):
        """
        This is where everything is initiated and gathered when running a test
        """
        config._fetcher = self

        self._test_start_time = datetime.now()

        self._tps = config['tps']

        d = defer.gatherResults(self.get(target) for target in self.targets)

        self._gatherer_deferred = d

        d.addErrback(self._polite_stoppage)

        d.addErrback(self._errback)

        # Send results to clients in batches every two seconds
        self._batcher = task.LoopingCall(self.batch_results)
        self._batcher_d = self._batcher.start(2)

        d.addCallback(self.compile_results)

        d.addCallback(self.cleanup)

        self.create_workers(config['max_active_jobs'])
        for worker in self.workers:
            worker.start()

        return d

    @property
    def test_run_time(self):
        seconds = (datetime.now() - self._test_start_time).total_seconds()
        minutes, s = divmod(seconds, 60)
        h, m = divmod(minutes, 60)
        if h:
            return "%dh%2dm%2ds" % (h, m, s)
        elif m:
            return "%2dm%2ds" % (m, s)
        else:
            return "%2ds" % (s,)

    @property
    def test_start_time(self):
        return unicode(self._test_start_time.strftime("%c"))

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

    def _calculate_statistics(self):
        statistics = {}
        for target in self.timings:
            statistics.setdefault(target, {})
            all_time_spans = []
            for key in self.timings[target]:
                time_spans = self.timings[target][key]
                statistics[target][key] = stats.generate(time_spans)
                all_time_spans.extend(time_spans)

            statistics[target]["__all__"] = stats.generate(all_time_spans)

        statistics['__all__']['__all__']['start_time'] = self.test_start_time
        statistics['__all__']['__all__']['run_time'] = self.test_run_time
        return statistics

    @property
    def initial_tps_delay(self):
        """
        Work out the minimum time to delay a request in order to prevent
        passing TPS threshold
        """
        if self._tps is None:
            return 0
        else:
            return (1.0 / self._tps) * len(self.workers)

    def adaptive_delay(self):
        """
        Compare the reported average TPS to our desired TPS and
        increase/decrease the Worker delay time appropriately
        """
        delay = self._delay
        if delay is None:
            delay = self.initial_tps_delay
        if self.stats is not None:
            mean_tps = self.stats['__all__']['__all__']['chart_points']['tps']['mean']
            if mean_tps < self._tps:
                delay -= 0.01
            elif mean_tps > self._tps:
                delay += 0.01
        self._delay = max(delay, 0)
        return self._delay

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
        self.workers = [ Worker(self._queue, self.adaptive_delay)
                         for _ in xrange(n) ]

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
                return None
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

        def errback(failure, url):
            # Trap specific failures here ?
            log.msg(failure)
            target.success = False

            end = datetime.now()
            result = Result(
                target=target,
                success=False,
                start_time=target.start_time,
                end_time=end,
                url=url,
                status_code=target.status_code)
            self.update_stats('Failure', result)
            return result

        return callback, errback

    def each_callback(self, result):
        self._deque.appendleft(result)

    def batch_results(self):
        """
        Called periodically to pick up any results returned and yield
        statistics on them to `batch_callback`

        This is nicer than sending stats per-result which could potentially
        cause huge amounts of traffic
        """
        results = list(self._deque)

        if results:
            # Get the tip of the results as this will have the most up-to-date
            # stats
            self.stats = self._calculate_statistics()
            try:
                if self.batch_callback is not None:
                    return self.batch_callback(results, self.stats)
            finally:
                self._deque.clear()

    def compile_results(self, result):
        """
        Generate the ultimate result from `results()`
        """
        # Make sure we at least batch once to ensure we yield the most recent
        # statistics. Otherwise some unprocessed results could still be in
        # the queue.
        self.batch_results()
        return self.stats

    @defer.inlineCallbacks
    def cleanup(self, result):
        """
        Clean up any outstanding batch/LoopingCall jobs, cleanly kill all
        workers and prevent any further requests from taking place
        """
        # Make sure we at least send one batch before we stop
        self.batch_results()
        if self._batcher is not None and self._batcher.running:
            self._batcher.stop()

        deferreds = [w.stop() for w in self.workers]
        for _ in xrange(len(self.workers)):
            # Make sure any workers waiting for a job can check if they need to
            # die
            self._queue.put(None)
        done_stopping = yield defer.gatherResults(deferreds)

        defer.returnValue(result)

    @defer.inlineCallbacks
    def stop(self):
        """
        I was politely asked to stop
        """
        self.stopping = True
        # Make sure I clean up cleanly before I announce my death
        just_chilling = yield self.cleanup(None)
        self._gatherer_deferred.errback(TestPolitelyStopped())

    @helpers.traps(TestPolitelyStopped)
    def _polite_stoppage(self, failure):
        log.msg("Test stopped successfully, at user's request")
        return failure

    def _errback(self, failure=None):
        """
        I got told to stop or an error happened; attempt to clean up
        """
        self.cancelled = True
        self.cleanup(None)
        self._failure = failure
        if failure.type is not TestPolitelyStopped:
            log.msg('Stopping test abnormally: %s' % (failure,))
        return failure
