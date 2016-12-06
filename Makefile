export VIRTUAL_ENV?=./venv

PROJ_NAME=amqpframe

BIN=$(VIRTUAL_ENV)/bin

PIP=$(BIN)/pip
ISORT=$(BIN)/isort
PYFORMAT=$(BIN)/pyformat
FLAKE8=$(BIN)/flake8
PYLINT=$(BIN)/pylint
PYTEST=$(BIN)/pytest
SPHINX_BUILD=$(BIN)/sphinx-build
SPHINX_MAKE=make -f docs/Makefile
SPHINX=$(SPHINX_MAKE) SPHINXBUILD=$(SPHINX_BUILD) SOURCEDIR=docs/ BUILDDIR=docs/_build


.PHONY: codestyle-check
codestyle-check: codestyle-autoformat
	$(FLAKE8) --count $(PROJ_NAME)
	$(PYLINT) $(PROJ_NAME)
	git diff --exit-code $(PROJ_NAME)
	echo "Your code is perfectly styled, congratz! :)"

.PHONY: codestyle-autoformat
codestyle-autoformat: codestyle-deps
	$(ISORT) -p $(PROJ_NAME) -ls -sl -rc $(PROJ_NAME)
	$(PYFORMAT) -r -i $(PROJ_NAME)

.PHONY: codestyle-deps
codestyle-deps:
	$(PIP) install -r requirements/codestyle

.PHONY: unittests
unittests: unittests-deps
	$(PYTEST) -v -l --cov=$(PROJ_NAME) --cov-report=term-missing:skip-covered tests/unit

.PHONY: unittests-deps
unittests-deps:
	$(PIP) install -r requirements/test

.PHONY: devtools
devtools:
	$(PIP) install -r requirements/dev

.PHONY: docs
docs: docs-deps
	$(SPHINX) html
	$(SPHINX) doctest
	$(SPHINX) coverage

.PHONY: docs-deps
docs-deps:
	$(PIP) install -r requirements/docs.txt
