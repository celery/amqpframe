export VENV_DIR?=./venv

BIN=$(VENV_DIR)/bin

PIP=$(BIN)/pip
ISORT=$(BIN)/isort
FLAKE8=$(BIN)/flake8
PYLINT=$(BIN)/pylint
PYFORMAT=$(BIN)/pyformat


codestyle-check: codestyle
	git diff --exit-code

codestyle: codestyle-deps
	$(ISORT) -p amqpframe -ls -sl -rc amqpframe
	$(PYFORMAT) --exclude methods.py --exclude errors.py -r -i amqpframe

codestyle-deps:
	$(PIP) install -U -r requirements/codestyle.txt
