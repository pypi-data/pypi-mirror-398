SHELL := /bin/bash
VERSION := $(shell lsb_release -rs)
BUMP=minor
export BUMP
.PHONY: help

help:  ## help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

uv:  ## installs uv
	@if [[ ! -f ~/.local/bin/uv ]] ; then \
		curl -LsSf https://astral.sh/uv/install.sh | sh \
	fi
	@export PATH="~/.local/bin:$$PATH"
	@echo "uv is installed at: $(which uv)"
	@~/.local/bin/uv python install cpython3.13

setup:  ## creates local virtual environment and installs requirements
	@if which uv && [ ! -f .venv/bin/python ] ; then ~/.local/bin/uv python install cpython3.13 ; uv venv --python 3.13 ; fi
	@source .venv/bin/activate \
	  && ~/.local/bin/uv pip install -U wheel \
	  && ~/.local/bin/uv pip install -r requirements.txt

test: FORCE  ## runs unit / integration tests via pytest
	source .venv/bin/activate \
	  && pytest -v -x test --cov {{ name }} --cov-report term-missing

build:  ## builds an sdist bundle
	source .venv/bin/activate \
	  && python -B -O setup.py sdist

lint:  ## performs linting via flake8 and pylint
	source .venv/bin/activate && flake8 {{ name }}
	source .venv/bin/activate && pylint --rcfile .pylintrc {{ name }}

clean:  ## cleans egg-info and dist directory
	source .venv/bin/activate \
	  && python -B -O setup.py clean
	rm -rf dist build
	rm -rf {{ name }}.egg-info

version:  ## bumpversion minor
	source .venv/bin/activate \
	  && bumpversion $(BUMP)
	git push --follow-tags

upload:  ## uploads built sdist bundles to pypi using twine
	source .venv/bin/activate \
	  && twine upload dist/*

publish: clean version build upload  ## performs a clean, version, build, and upload

FORCE:
