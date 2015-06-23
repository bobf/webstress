from __future__ import unicode_literals

from webstress.util.helpers import hash_dict

import urlparse
import urllib

class Target(object):
    def __init__(self, owner, target):
        self._target = target
        # Keep a back ref to which config I came from
        self.owner = owner
        self.success = None
        self.status_code = None
        self.params = [Param(x) for x in target.get("params", [])]
        self.hits = target["hits"]
        self.name = target.get("name")
        self.base_url = target["base_url"]
        self.uid = hash_dict(self._to_dict())

    @property
    def url(self):
        url = self.base_url
        parsed = urlparse.urlparse(url)
        params = [(x.key, x.value) for x in self.params]
        if params and parsed.query:
            return "%s&%s" % (url, urllib.urlencode(params))
        elif params:
            return "%s?%s" % (url, urllib.urlencode(params))
        else:
            return url

    def _to_dict(self):
        attribs = ["owner",
                   "hits", "name", "base_url"]
        obj = dict(
            (x, getattr(self, x))
            for x in attribs)

        obj["params"] = [x.to_json() for x in self.params]

        return obj

    def to_json(self):
        d = self._to_dict()
        d["uid"] = self.uid
        return d

class Param(object):
    def __init__(self, param):
        self._param = param
        self.key = param["key"]

    @property
    def value(self):
        return self._param["value_func"]()

    def to_json(self):
        if isinstance(self._param["value"], dict):
            if "fake" in self._param["value"]:
                return {"key": self.key,
                        "value": "Fake: " + self._param["value"]["fake"]}
        else:
            return {"key": self.key, "value": self.value}


class Result(object):
    def __repr__(self):
        attribs = ["url", "success", "status_code", "duration"]
        template = "Result: <%s>" % (', '.join("%s: %%(%s)s" % (x.title(), x) for x in attribs),)
        return template % dict((k, getattr(self, k, "Unknown")) for k in attribs)

    def __init__(self, target, **kwargs):
        self.target = target
        self.success = kwargs["success"]
        self.start_time = kwargs["start_time"]
        self.end_time = kwargs["end_time"]
        self.url = kwargs["url"]
        self.status_code = kwargs["status_code"]
        self.stats = {}

    @property
    def duration(self):
        return (self.end_time - self.start_time).total_seconds()

    def to_json(self):
        d = dict(
                (x, getattr(self, x))
                for x in ["success", "duration", "url", "status_code", "stats",
                          "start_time", "end_time"])
        d['target'] = self.target.to_json()
        return d

class Response(object):
    def __repr__(self):
        return "delegate: %s, result: %s" % (self.delegate, self.result)

    def __init__(self, delegate, result):
        self.delegate = delegate
        self.result = result

