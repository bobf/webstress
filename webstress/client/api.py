import sys

import webstress.config.parser
import webstress.client.http

def run(config_string, each_callback=None):
    webstress.configuration = webstress.config.parser.Config(config_string)

    http = webstress.client.http.HTTP()
    for target in webstress.configuration.targets:
        http.add_target(target)

    return http.hit(each_callback=each_callback)
