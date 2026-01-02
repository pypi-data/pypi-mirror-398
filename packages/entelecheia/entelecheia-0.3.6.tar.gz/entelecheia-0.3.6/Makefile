# To do stuff with make, you type `make` in a directory that has a file called
# "Makefile".  You can also type `make -f <makefile>` to use a different filename.
#
# A Makefile is a collection of rules. Each rule is a recipe to do a specific
# thing, sort of like a grunt task or an npm package.json script.
#
# A rule looks like this:
#
# <target>: <prerequisites...>
# 	<commands>
#
# The "target" is required. The prerequisites are optional, and the commands
# are also optional, but you have to have one or the other.
#
# Type `make` to show the available targets and a description of each.
#
.DEFAULT_GOAL := help
.PHONY: help
help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


##@ Clean-up

clean-cov: ## remove coverage reports
	@rm -rf .coverage* tests/htmlcov tests/pytest.xml tests/pytest-coverage.txt

clean-pycache: ## remove __pycache__ directories
	@find . -type d -name __pycache__ -exec rm -rf {} + || true

clean-build: ## remove build/python artifacts
	@rm -rf build dist *.egg-info

clean-docs: ## remove documentation artifacts
	@rm -rf book/_build docs/_build _site

clean: clean-cov clean-pycache clean-build clean-docs ## remove build artifacts and coverage reports

##@ Utilities

large-files: ## show the 20 largest files in the repo
	@find . -printf '%s %p\n'| sort -nr | head -20

disk-usage: ## show the disk usage of the repo
	@du -h -d 2 .

git-sizer: ## run git-sizer
	@git-sizer --verbose

gc-prune: ## garbage collect and prune
	@git gc --prune=now

##@ Setup

install-pipx: ## install pipx (pre-requisite for external tools)
	@command -v pipx &> /dev/null || pip install --user pipx || true

install-uv: install-pipx ## install uv (pre-requisite for install)
	@command -v uv &> /dev/null || pipx install uv || true

install-commitzen: install-pipx ## install commitzen (pre-requisite for commit)
	@command -v cz &> /dev/null || pipx install commitizen || true

install-precommit: install-pipx ## install pre-commit
	@command -v pre-commit &> /dev/null || pipx install pre-commit || true

install-precommit-hooks: install-precommit ## install pre-commit hooks
	@pre-commit install

initialize: install-pipx ## initialize the project environment
	@pipx install copier
	@pipx install commitizen
	@pipx install pre-commit
	@pre-commit install

init-project: initialize remove-template ## initialize the project (Warning: do this only once!)
	@copier copy --trust --data 'code_template_source=gh:entelecheia/hyfi-template' --answers-file .copier-config.yaml gh:entelecheia/hyperfast-python-template .

reinit-project: install-copier ## reinitialize the project (Warning: this may overwrite existing files!)
	@bash -c 'args=(); while IFS= read -r file; do args+=("--skip" "$$file"); done < .copierignore; copier copy --trust "$${args[@]}" --data 'code_template_source=gh:entelecheia/hyfi-template' --answers-file .copier-config.yaml gh:entelecheia/hyperfast-python-template .'

##@ Format

format-black: ## format code with black
	@uv run black .

format-isort: ## sort imports with isort
	@uv run isort .

format: format-black format-isort ## format code with black and isort

##@ Lint

lint-black: ## check code formatting with black
	@uv run black --check --diff .

lint-flake8: ## check code style with flake8
	@uv run flake8 .

lint-isort: ## check import sorting with isort
	@uv run isort --check-only --diff .

lint-mypy: ## check types with mypy
	@uv run mypy --config-file pyproject.toml .

lint-mypy-reports: ## generate an HTML report of the type (mypy) checker
	@uv run mypy --config-file pyproject.toml . --html-report ./tests/mypy-report

lint: lint-black lint-flake8 lint-isort ## check code style with flake8, black, and isort

##@ Testing

tests: ## run tests with pytest
	@uv run pytest --doctest-modules

tests-cov: ## run tests with pytest and generate a coverage report
	@uv run pytest --cov=src --cov-report=xml

tests-cov-fail: ## run tests with pytest and generate a coverage report, fail if coverage is below 50%
	@uv run pytest --cov=src --cov-report=xml --cov-fail-under=50 --junitxml=tests/pytest.xml | tee tests/pytest-coverage.txt

##@ Build & Install

build: ## build the package
	@uv build

install: install-uv ## install dependencies
	@uv sync --no-extra dev

install-dev: install-uv ## install dev dependencies
	@uv sync --extra dev

update: install-uv ## update dependencies
	@uv lock --upgrade
	@uv sync

lock: install-uv ## lock dependencies
	@uv lock

run: ## run the main program
	@uv run entelecheia

##@ Documentation

install-ghp-import: install-pipx ## install ghp-import
	@pipx install ghp-import

install-jupyter-book-pipx: install-pipx ## install jupyter-book with pipx
	@pipx install jupyter-book
	@pipx inject jupyter-book $$(awk '{if(!/^ *#/ && NF) print}' book/requirements.txt)

install-jupyter-book: ## install jupyter-book
	@pip install -r book/requirements.txt

book-build: ## build the book
	@jupyter-book build book

book-build-all: ## build the book with all outputs
	@jupyter-book build book --all

book-publish: install-ghp-import ## publish the book
	@ghp-import -n -p -f book/_build/html

##@ Utilities

codecov-validate: ## Validate codecov.yml
	@curl -X POST --data-binary @codecov.yml https://codecov.io/validate
