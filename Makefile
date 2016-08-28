export VENV_DIR?=./venv

BIN=$(VENV_DIR)/bin

PIP=$(BIN)/pip
ISORT=$(BIN)/isort
FLAKE8=$(BIN)/flake8
PYLINT=$(BIN)/pylint
PYFORMAT=$(BIN)/pyformat


codestyle: codestyle-deps
	$(ISORT) -p amqpframe -ls -m 2 -rc amqpframe
	$(PYFORMAT) --exclude methods.py --exclude errors.py -r -i amqpframe

check-codestyle: codestyle
	git diff --exit-code

codestyle-deps:
	$(PIP) install -U -r requirements/codestyle.txt
