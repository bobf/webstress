.PHONY: test
test:
	rm -rf tests/*.pyc
	bin/python -m unittest discover -p 'test_*.py'
