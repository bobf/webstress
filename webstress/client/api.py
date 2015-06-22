import webstress.config.parser
import webstress.client.http

def reload_config():
    raise NotImplementedError("Must be set by whichever interface is used")

def run(configs, batch_callback=None):
    update_config(configs)

    return launch_all_tests(batch_callback)

def launch_all_tests(batch_callback):
    targets = []
    for config in webstress.configuration.configs.values():
        targets.extend(config["targets"])

    http = webstress.client.http.HTTP(webstress.configuration.encoding)
    for target in targets:
        http.add_target(target)

    return http.hit(batch_callback=batch_callback)

def launch_test(config, targets, batch_callback=None):
    http = webstress.client.http.HTTP(webstress.configuration.encoding)
    for target in targets:
        http.add_target(target)

    return http.hit(batch_callback=batch_callback, tps=config["tps"])

def update_config(configs):
    # Takes a list of dicts, each dict is one config
    webstress.configuration = webstress.config.parser.Config(configs)
