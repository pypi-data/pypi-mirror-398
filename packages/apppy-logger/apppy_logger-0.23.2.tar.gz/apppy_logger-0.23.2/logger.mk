ifndef APPPY_LOGGER_MK_INCLUDED
APPPY_LOGGER_MK_INCLUDED := 1
LOGGER_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: logger logger-dev logger/build logger/clean logger/install logger/install-dev

logger: logger/clean logger/install

logger-dev: logger/clean logger/install-dev

logger/build:
	cd $(LOGGER_PKG_DIR) && uvx --from build pyproject-build

logger/clean:
	cd $(LOGGER_PKG_DIR) && rm -rf dist/ *.egg-info .venv

logger/install: logger/build
	cd $(LOGGER_PKG_DIR) && uv pip install dist/*.whl

logger/install-dev:
	cd $(LOGGER_PKG_DIR) && uv pip install -e .

logger/publish: logger/clean logger/install
	twine upload $(LOGGER_PKG_DIR)/dist/* || exit 1

endif # APPPY_LOGGER_MK_INCLUDED