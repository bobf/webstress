import sys

import webstress.config.parser
import webstress.client.http

def reload_config():
    raise  NotImplemented("Must be set by whichever interface is used")

def run(config_string, each_callback=None):
    update_config(config_string)

    return launch_tests(each_callback, all=True)

def launch_tests(each_callback, targets=None, all=False):
    if not bool(targets) ^ bool(all):
        raise TypeError("Must pass *either* `all=True` or `targets=['target1', 'target2']")

    targets = targets or webstress.configuration.targets

    http = webstress.client.http.HTTP()
    for target in targets:
        http.add_target(target)

    return http.hit(each_callback=each_callback)

def update_config(config_string):
    webstress.configuration = webstress.config.parser.Config(config_string)
