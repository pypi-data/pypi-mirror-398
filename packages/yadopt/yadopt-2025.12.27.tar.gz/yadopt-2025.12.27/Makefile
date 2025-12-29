# Makefile

SOFTWARE := yadopt

help:
	@echo "Usage:"
	@echo "    make <command>"
	@echo ""
	@echo "Build commands:"
	@echo "    build         Build package"
	@echo "    testpypi      Upload package to TestPyPi"
	@echo "    pypi          Upload package to PyPi"
	@echo "    install-test  Install from TestPyPi"
	@echo ""
	@echo "Test and code check commands:"
	@echo "    check         Check the code quality"
	@echo "    count         Count the lines of code"
	@echo "    coverage      Measure code coverage"
	@echo "    test          Run test on this device"
	@echo "    testall       Run all tests on Docker"
	@echo ""
	@echo "Other commands:"
	@echo "    clean         Cleanup cache files"
	@echo "    help          Show this message"

check:
	pyflakes yadopt
	mypy yadopt
	pylint --max-line-length=120 --generated-members=__dict__ yadopt

count:
	cloc --by-file yadopt/*.py

coverage:
	rm -rf .coverage
	coverage run --source yadopt tests/run_tests.py
	coverage html

test:
	python3 tests/run_tests.py --local --verbose

testall:
	bash tests/run_tests_on_docker.bash

build:
	python3 -m build

testpypi:
	twine upload --repository pypitest dist/*

pypi:
	twine upload --repository pypi dist/*

install-test:
	python3 -m pip install --index-url https://test.pypi.org/simple/ $(SOFTWARE)

clean:
	rm -rf dist .coverage .mypy_cache htmlcov `find -type d | grep __pycache__`

# vim: noexpandtab tabstop=4 shiftwidth=4
