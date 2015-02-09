import urlparse

from . import fetcher

class HTTP(object):
    def __init__(self):
        self.targets = []
        self._fetcher = fetcher.Fetcher()

    def add_url(self, url):
        self.targets.append({"url": url})

    def hit(self, times, callback=None):
        self._fetcher.set_complete_callback(callback)

        for _ in xrange(times):
            self._fetcher.add_targets(self.targets)

        self._fetcher.run()
