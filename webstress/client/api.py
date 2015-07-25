from twisted.python import log

import webstress.config.parser
import webstress.client.http

def reload_config():
    raise NotImplementedError("Must be set by whichever interface is used")

def list_configs():
    return webstress.configuration.list_configs(to_json=True)

def launch_test(config, targets, batch_callback=None, batch_delay=2):
    http = webstress.client.http.HTTP(webstress.configuration.encoding)
    for target in targets:
        http.add_target(target)

    return http.hit(batch_callback=batch_callback, config=config,
                    batch_delay=batch_delay)

def stop_test(uid):
    for config in webstress.configuration.configs.values():
        if config.uid == uid:
            config._fetcher.stop()
            break
    else:
        log.msg("Stop failed, couldn't find config UID: %s" % (uid,))


def update_config(configs):
    """
    Take a list of dicts (see webstress.config.parser.Config docstring for
    specification) and update the global configuration.
    """

    # Takes a list of dicts, each dict is one config
    webstress.configuration = webstress.config.parser.Config(configs)
