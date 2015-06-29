from . import fetcher

class HTTP(object):
    def __init__(self, encoding):
        self.targets = []
        self._fetcher = fetcher.Fetcher(encoding)
        self.encoding = encoding

    def add_target(self, target):
        self.targets.append(target)

    def hit(self, config, batch_callback=None, batch_delay=None):
        if batch_delay is None:
            batch_delay = 2
        self._fetcher.add_targets(self.targets)
        self._fetcher.batch_callback = batch_callback

        return self._fetcher.results(config, batch_delay)
