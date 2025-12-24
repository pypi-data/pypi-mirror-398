ifndef APPPY_CLIENTS_MK_INCLUDED
APPPY_CLIENTS_MK_INCLUDED := 1
CLIENTS_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: clients clients-dev clients/build clients/clean clients/install clients/install-dev

clients: clients/clean clients/install

clients-dev: clients/clean clients/install-dev

clients/build:
	cd $(CLIENTS_PKG_DIR) && uvx --from build pyproject-build

clients/clean:
	cd $(CLIENTS_PKG_DIR) && rm -rf dist/ *.egg-info .venv

clients/install: clients/build
	cd $(CLIENTS_PKG_DIR) && uv pip install dist/*.whl

clients/install-dev:
	cd $(CLIENTS_PKG_DIR) && uv pip install -e .

clients/publish: clients/clean clients/install
	twine upload $(CLIENTS_PKG_DIR)/dist/* || exit 1

endif # APPPY_CLIENTS_MK_INCLUDED