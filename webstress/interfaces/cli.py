import sys

from twisted.internet import reactor
import twisted.internet.task

import webstress.client.api

def each_callback(result):
    sys.stdout.write(".")
    sys.stdout.flush()

def display_results(results):
    sys.stdout.write("\n\n")
    for result in sorted(results, key=lambda x: (x.success, x.duration)):
        sys.stdout.write("%s\n" % (repr(result),))

def run():
    f = open(sys.argv[1])

    twisted.internet.task.react(
        lambda _: webstress.client.api.run(
                    f.read(),
                    each_callback=each_callback
            ).addCallback(display_results)
        )