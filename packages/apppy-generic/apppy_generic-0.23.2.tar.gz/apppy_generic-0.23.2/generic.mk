ifndef APPPY_GENERIC_MK_INCLUDED
APPPY_GENERIC_MK_INCLUDED := 1
GENERIC_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: generic generic-dev generic/build generic/clean generic/install generic/install-dev

generic: generic/clean generic/install

generic-dev: generic/clean generic/install-dev

generic/build:
	cd $(GENERIC_PKG_DIR) && uvx --from build pyproject-build

generic/clean:
	cd $(GENERIC_PKG_DIR) && rm -rf dist/ *.egg-info .venv

generic/install: generic/build
	cd $(GENERIC_PKG_DIR) && uv pip install dist/*.whl

generic/install-dev:
	cd $(GENERIC_PKG_DIR) && uv pip install -e .

generic/publish: generic/clean generic/install
	twine upload $(GENERIC_PKG_DIR)/dist/* || exit 1

endif # APPPY_GENERIC_MK_INCLUDED