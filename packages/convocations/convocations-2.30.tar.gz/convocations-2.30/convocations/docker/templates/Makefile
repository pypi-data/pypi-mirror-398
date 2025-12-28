SHELL := /bin/bash

BUMP=minor
export BUMP
.PHONY: help

help:  ## help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build:  ## builds the docker image using convoke
	source .venv/bin/activate \
	  && convoke build
uv:  ## installs uv
	@if [[ ! -f ~/.local/bin/uv ]] ; then \
		curl -LsSf https://astral.sh/uv/install.sh | sh \
	fi
	@export PATH="~/.local/bin:$$PATH"
	@echo "uv is installed at: $(which uv)"
	@~/.local/bin/uv python install cpython3.12
setup:  ## sets up the local environment for the build process
	@if [[ ! -d .venv/bin/python ]] ; then ~/.local/bin/uv venv --python 3.12 ; fi
	source .venv/bin/activate \
	  && ~/.local/bin/uv pip install -U wheel \
	  && ~/.local/bin/uv pip install -r requirements.txt
publish:  ## publishes the docker image using convoke
	source .venv/bin/activate \
	  && convoke publish
