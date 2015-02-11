import urllib

from yaml import load, dump
from faker import Faker


fake = Faker()

def parse(source):
    return callify_param_values(load(source))

def callify(param):
    # Make all param values callable, whether faker-generated or not, for
    # consintent # API

    if isinstance(param["value"], dict) and "fake" in param["value"]:
        param["value_func"] = getattr(fake, param["value"]["fake"])
    else:
        param["value_func"] = lambda *_, **__: param["value"]

    return param

def callify_param_values(config):
    for target in config["targets"]:
        for i, param in enumerate(target.get("params", [])):
            param = callify(param)
    return config


class Config(object):
    def __init__(self, source):
        self._config = parse(source)
        self.targets = [Target(x) for x in self._config["targets"]]


class Target(object):
    def __repr__(self):
        return "Target: <success: %(success)s, status: %(status)s>" % dict(
            success=self.success,
            status=self.status_code
        )
    def __init__(self, target):
        self._target = target
        self.success = None
        self.status_code = None
        self.params = [Param(x) for x in target["params"]]
        self.hits = target["hits"]

    @property
    def url(self):
        url = self._target["url"]
        params = [(x.key, x.value) for x in self.params]
        if params:
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
