import urlparse

from . import fetcher

class HTTP(object):
    def __init__(self):
        self.targets = []
        self._fetcher = fetcher.Fetcher()

    def add_target(self, target):
        self.targets.append(target)

    def hit(self):
        self._fetcher.add_targets(self.targets)

        return self._fetcher.results()
