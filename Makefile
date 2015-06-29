.PHONY: test
test:
	kill `cat testserver.pid 2> /dev/null` >/dev/null 2>&1 || true
	rm -rf tests/*.pyc
	bin/twistd --pidfile testserver.pid --logfile testserver.log web -p 8000 --path . &&  bin/trial tests
	kill `cat testserver.pid`

.PHONY: test-monitor
test-monitor:
	# Needs fswatch, only tested on OS X
	fswatch -r -o -e ".pyc$$" -e ".swp$$" webstress tests twisted/plugins | xargs -n1 -I{} make test

.PHONY: install-virtualenv
install-virtualenv:
	virtualenv .
	bin/pip install .

.PHONY: run-web
run-web:
	kill `cat twistd.pid 2> /dev/null` >/dev/null 2>&1 || true
	if [ -f "bin/twistd" ]; then bin/twistd -n webstress --config-dir tests/support/configs; else twistd -n webstress; fi

.PHONY: run-web-daemonize
run-web-daemonize:
	kill `cat twistd.pid 2> /dev/null` >/dev/null 2>&1 || true
	if [ -f "bin/twistd" ]; then bin/twistd webstress --config-dir tests/support/configs; else twistd webstress; fi

