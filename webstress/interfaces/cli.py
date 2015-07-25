import sys

import twisted.internet.task

import webstress.client.api

def batch_callback(results, stats):
    sys.stdout.write("." * len(results))
    sys.stdout.flush()

def display_results(stats):
    sys.stdout.write("\n\n")
    sys.stdout.write(stats.to_string())
    sys.stdout.write("\n\n")

def run(config_file=None):
    """
    Run a test given a configuration, either supplied as an argument as a
    file-like object or as a filename as the first command line argument.
    """
    if config_file is None:
        f = open(sys.argv[1])
    else:
        f = config_file

    webstress.client.api.update_config(
        [{
         "name": '__main__',
         "body": f.read()
        }]
    )

    config = webstress.configuration.configs['__main__']

    twisted.internet.task.react(
        lambda _: webstress.client.api.launch_test(
                    config,
                    config['targets'],
                    batch_callback=batch_callback
            ).addCallback(display_results)
        )
