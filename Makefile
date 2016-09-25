export VIRTUAL_ENV?=./venv

BIN=$(VIRTUAL_ENV)/bin

PIP=$(BIN)/pip
ISORT=$(BIN)/isort
PYFORMAT=$(BIN)/pyformat
FLAKE8=$(BIN)/flake8
PYLINT=$(BIN)/pylint
PYTEST=$(BIN)/pytest


codestyle-check: codestyle-autoformat
	$(FLAKE8) --count amqpframe
	$(PYLINT) amqpframe
	git diff --exit-code amqpframe
	echo "Your code is perfectly styled, congratz! :)"

codestyle-autoformat: codestyle-deps
	$(ISORT) -p amqpframe -ls -sl -rc amqpframe
	$(PYFORMAT) --exclude methods.py --exclude errors.py -r -i amqpframe

codestyle-deps:
	$(PIP) install -r requirements/codestyle.txt

unittest:
	$(PYTEST) -v -l --cov=amqpframe --cov-report=term-missing:skip-covered tests
