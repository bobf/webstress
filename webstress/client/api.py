from twisted.python import log

import webstress.config.parser
import webstress.client.http

def reload_config():
    raise NotImplementedError("Must be set by whichever interface is used")

def launch_test(config, targets, batch_callback=None):
    http = webstress.client.http.HTTP(webstress.configuration.encoding)
    for target in targets:
        http.add_target(target)

    return http.hit(batch_callback=batch_callback, config=config)

def stop_test(uid):
    for config in webstress.configuration.configs.values():
        if config.uid == uid:
            config._fetcher.stop()
            break
    else:
        log.msg("Stop failed, couldn't find config UID: %s" % (uid,))


def update_config(configs):
    # Takes a list of dicts, each dict is one config
    webstress.configuration = webstress.config.parser.Config(configs)
