import yaml
from faker import Faker

from webstress.common.types import Target
from webstress.common.exceptions import (NonUniqueConfigNames,
                                         NonUniqueTargetNames,
                                         TargetNotFound)

fake = Faker()


def parse(source):
    return callify_param_values(yaml.load(source))

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
        for param in target.get("params", []):
            param = callify(param)
    return config


class Config(object):
    def __init__(self, sources):
        self.configs = {}
        non_unique_names = []
        for source in sources:
            parsed = parse(source["body"])

            name = source["name"]

            config = dict()
            config["name"] = name
            config["targets"] = [Target(name, x) for x in parsed["targets"]]

            self._check_unique(config)

            if name in self.configs:
                non_unique_names.append(name)
            else:
                self.configs[name] = config

        if non_unique_names:
            raise NonUniqueConfigNames(non_unique_names)

        self.DEBUG = False

    def target_by_name(self, config, name):
        for target in self.configs[config]["targets"]:
            if target.name == name:
                return target

        raise TargetNotFound

    def _check_unique(self, config):
        name_set = dict()
        all_names = []
        for target in config["targets"]:
            all_names.append(target.name)
            name_set[target.name] = name_set.get(target.name, 0) + 1

        if len(name_set) == len(config["targets"]):
            return

        key = lambda x: all_names.index(x[0])
        non_unique = [k
                      for k, v in sorted(name_set.items(), key=key)
                      if v > 1]

        if non_unique:
            raise NonUniqueTargetNames(
                "Non-unique targets in config `%s`: %s" % (
                    config["name"], non_unique))
