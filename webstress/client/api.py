import webstress.config.parser
import webstress.client.http

def reload_config():
    raise NotImplementedError("Must be set by whichever interface is used")

def run(configs, each_callback=None):
    update_config(configs)

    return launch_tests(each_callback, all=True)

def launch_tests(each_callback, targets=None, all=False):
    if not bool(targets) ^ bool(all):
        raise TypeError("Must pass *either* `all=True` or `targets=['target1', 'target2']")

    if targets is None:
        targets = []
        for config in webstress.configuration.configs.values():
            targets.extend(config["targets"])

    http = webstress.client.http.HTTP(webstress.configuration.encoding)
    for target in targets:
        http.add_target(target)

    return http.hit(each_callback=each_callback)

def update_config(configs):
    # Takes a list of dicts, each dict is one config
    webstress.configuration = webstress.config.parser.Config(configs)
