from __future__ import unicode_literals

import yaml
from faker import Factory

from webstress.common.types import Target, UIDDict
from webstress.common.exceptions import (NonUniqueConfigNames,
                                         NonUniqueTargetNames,
                                         TargetNotFound)
from webstress.util.helpers import hash_dict

fake = Factory.create('en_GB')

# http://stackoverflow.com/a/2967461
from yaml import Loader, SafeLoader
def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


def parse(source, encoding):
    return callify_param_values(yaml.load(source.decode(encoding)))

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

DEFAULT_FILTER_PARAMS = [
    "password",
    "auth_token",
    "authentication_token",
    "token",
    ]

class Config(object):
    """
    The main configuration object which is usually found at
    webstress.configuration

    Typically this is a collection of .yaml files loaded as a list of dicts
    passed to __init__:

    [
        {"name": "test_name_1",
         "body": "<yaml config for test>},
        {"name": "test_name_2",
         "body": "<yaml config for test>},
    ]
    """
    # For reading from a filesystem - is there any sane way to do this ?
    encoding = 'utf8'

    def __init__(self, sources):
        self.configs = {}
        non_unique_names = []
        for source in sources:
            parsed = parse(source["body"], self.encoding)

            name = source["name"].decode(self.encoding)

            config = UIDDict()
            config["filter_params"] = parsed.get("filter_params")
            if config["filter_params"] is None:
                # Only use defaults on None - allow config to specify an empty
                # list to override defaults
                config["filter_params"] = DEFAULT_FILTER_PARAMS

            config["name"] = name
            config["tps"] = parsed.get("tps")
            config["max_active_jobs"] = parsed.get("max_active_jobs")
            config["targets"] = [Target(config, x) for x in parsed["targets"]]

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

    def list_configs(self, to_json=True):
        configs = []

        if to_json:
            for config in [self.configs[x] for x in self.configs]:
                config_dict = dict(config)
                config_dict["targets"] = [x.to_json() for x in config["targets"]]
                config_dict["uid"] = config.uid
                configs.append(config_dict)
        else:
            configs = [self.configs[x] for x in self.configs]

        return configs

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
