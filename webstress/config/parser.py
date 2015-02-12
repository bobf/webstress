from yaml import load, dump
from faker import Faker

from webstress.common.types import Target, Param
from webstress.common.exceptions import NonUniqueTargetNames, TargetNotFound

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

        self._check_unique()

    def by_name(self, name):
        for target in self.targets:
            if target.name == name:
                return target

        raise TargetNotFound

    def _check_unique(self):
        name_set = dict()
        all_names = []
        for target in self.targets:
            all_names.append(target.name)
            name_set[target.name] = name_set.get(target.name, 0) + 1

        if len(name_set) == len(self.targets):
            return

        key = lambda x: all_names.index(x[0])
        non_unique = [k
                      for k, v in sorted(name_set.items(), key=key)
                      if v > 1]

        if non_unique:
            raise NonUniqueTargetNames("Non-unique targets: %s" % (non_unique))
