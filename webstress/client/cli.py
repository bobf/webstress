import sys

import webstress.config.parser
import webstress.client.http

def run(config_string, each_callback=None):
    if each_callback is None:
        each_callback = default_callback

    config = webstress.config.parser.Config(config_string)

    http = webstress.client.http.HTTP()
    for target in config.targets:
        http.add_target(target)

    return http.hit(each_callback=each_callback)

def default_callback(result):
    print result
