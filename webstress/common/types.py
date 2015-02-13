import json
import urlparse
import urllib

class Target(object):
    def __init__(self, target):
        self._target = target
        self.success = None
        self.status_code = None
        self.params = [Param(x) for x in target.get("params", [])]
        self.hits = target["hits"]
        self.name = target.get("name")

    @property
    def url(self):
        url = self._target["url"]
        parsed = urlparse.urlparse(url)
        params = [(x.key, x.value) for x in self.params]
        if params and parsed.query:
            return "%s&%s" % (url, urllib.urlencode(params))
        elif params:
            return "%s?%s" % (url, urllib.urlencode(params))
        else:
            return url


class Param(object):
    def __init__(self, param):
        self._param = param
        self.key = param["key"]

    @property
    def value(self):
        return self._param["value_func"]()


class Result(object):
    def __repr__(self):
        attribs = ["url", "success", "status_code", "duration"]
        template = "Result: <%s>" % (', '.join("%s: %%(%s)s" % (x.title(), x) for x in attribs),)
        return template % dict((k, getattr(self, k, "Unknown")) for k in attribs)

    def __init__(self, target, **kwargs):
        self._target = target
        self.success = kwargs["success"]
        self.duration = kwargs["duration"]
        self.url = kwargs["url"]
        self.status_code = kwargs["status_code"]

    def to_json(self):
        return dict(
                (unicode(x), unicode(getattr(self, x)))
                for x in ["success", "duration", "url", "status_code"])

class Response(object):
    def __repr__(self):
        return "delegate: %s, result: %s" % (self.delegate, self.result)

    def __init__(self, delegate, result):
        self.delegate = delegate
        self.result = result

