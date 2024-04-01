.PHONY: all init create

all:
	@echo "Specify a command to run"

init:
	python3 -m venv .venv; \
	until [ -f .venv/bin/python3 ]; do sleep 1; done; \
	until [ -f .venv/bin/activate ]; do sleep 1; done;
	. .venv/bin/activate; \
	pip install PyYAML xia-framework keyring setuptools wheel jinja2; \
    pip install keyrings.google-artifactregistry-auth; \

init-module: init
	@if [ -z "$(module_name)" ]; then \
	  echo "Module name not specified. Usage: make init-module module_name=<module_name>"; \
	else \
	  . .venv/bin/activate; \
	  python main.py init-module -n $(module_name); \
	fi
