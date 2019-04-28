ifneq (,$(wildcard ./bin/twistd))
  executable:=./bin/twistd
else
  executable:=twistd
endif

.PHONY: setup
setup:
	virtualenv --clear --python=python2 .
	bin/python setup.py install
	bin/easy_install -U PyOpenSSL

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
run-web: config ?= tests/support/configs
run-web: kill
	${executable} -n webstress --config-dir '${config}'

.PHONY: run-web-daemonize
run-web-daemonize: config ?= tests/support/configs
run-web-daemonize: kill
	${executable} webstress --config-dir '${config}'

.PHONY: kill
kill:
	kill $$(cat twistd.pid 2>/dev/null) >/dev/null 2>&1 || :
