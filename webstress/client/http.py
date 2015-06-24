from . import fetcher

class HTTP(object):
    def __init__(self, encoding):
        self.targets = []
        self._fetcher = fetcher.Fetcher(encoding)
        self.encoding = encoding

    def add_target(self, target):
        self.targets.append(target)

    def hit(self, batch_callback=None, tps=None, max_active_jobs=None):
        self._fetcher.add_targets(self.targets)
        self._fetcher.batch_callback = batch_callback

        return self._fetcher.results(tps=tps, max_active_jobs=max_active_jobs)
