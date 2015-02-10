import subprocess
import os
import time

class WebServer(object):
    def __init__(self):
        devnull = open(os.devnull, 'w')
        devnull = open("/tmp/twistd-log", "a")
        path = ["./bin/twistd",
                "-n",
                "web",
                "-p",
                "8000",
                "--path",
                "."]
        self.process = subprocess.Popen(
            path,
            stdout=devnull,
            stderr=devnull)

        time.sleep(2)

    def kill(self):
        self.process.kill()
