
# Simple makefile to help manage the project

.PHONY: pypi help test_pypi clean check test lint type profile

PYTEST_EXTRA_FLAGS ?= 

# The stuff below implements an auto help feature
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:   ## Show help for avaiable targets
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

lint:   ## Run linter on project
	uv run pylint src/fast_tx

test:   ## Run tests
	uv run py.test -s -vvv --doctest-modules --doctest-glob='*.md' \
            ${PYTEST_EXTRA_FLAGS} README.md src

check:  ## Run linting, tests, etc.
	${MAKE} lint
	${MAKE} test
	${MAKE} cov


clean:  ## Clean out generated files.
	rm -rf -- dist *.egg-info src/*.egg-info
	rm -rf -- `find . -name '__pycache__' -print`

test_pypi:  check dist  ## Test pypi upload
	uv run python3 -m twine upload --verbose --repository testpypi dist/*

pypi:   check dist  ## Upload to pypi
	uv run python3 -m twine upload --verbose dist/*

dist:   ## Build distribution
	uv run python3 -m build 

profile_basic:  ## Run basics profiling (try w/ + w/o NUMBA_DISABLE_JIT=1).
	PYTHONPATH=${PYTHONPATH}:src uv run src/fast_tx_tests/test_basics.py

profile_ewm:  ## Run basics profiling (try w/ + w/o NUMBA_DISABLE_JIT=1).
	export fixme=cython,apply_closure,apply_cls && \
          export fast_modes=fast_tx_closure,fast_tx,fast_tx_clean && \
          PYTHONPATH=${PYTHONPATH}:src \
            FAST_TX_PROFILE_MODE=timeit \
            FAST_TX_ENGINE=${fixme},${fast_modes} \
            echo uv run src/fast_tx_tests/test_prof_ewm.py

cov:  ## Run tests with code coverage (without numba).
	export NUMBA_DISABLE_JIT=1 && ${MAKE} test \
          PYTEST_EXTRA_FLAGS="--cov=src \
              --cov-report term-missing --cov-fail-under=98"

update_dev:  ## Install/update tools required for development/packaging
	./.venv/bin/uv pip install setuptools wheel twine build packaging \
              ruff flake8 pylint pytest coverage pytest-cov
	./.venv/bin/pip3 install -e .
