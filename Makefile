.PHONY: test
test:
	kill `cat twistd.pid 2> /dev/null` >/dev/null 2>&1 || true
	rm -rf tests/*.pyc
	(bin/twistd web -p 8000 --path . &&  bin/trial tests) || kill `cat twistd.pid`
