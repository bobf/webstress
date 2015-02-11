from yaml import load, dump
from faker import Faker

from webstress.common.types import Target, Param

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
