ifndef APPPY_ENV_MK_INCLUDED
APPPY_ENV_MK_INCLUDED := 1
ENV_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: env env-dev env/build env/clean env/install env/install-dev

env: env/clean env/install

env-dev: env/clean env/install-dev

env/build:
	cd $(ENV_PKG_DIR) && uvx --from build pyproject-build

env/clean:
	cd $(ENV_PKG_DIR) && rm -rf dist/ *.egg-info .venv

env/install: env/build
	cd $(ENV_PKG_DIR) && uv pip install dist/*.whl

env/install-dev:
	cd $(ENV_PKG_DIR) && uv pip install -e .

env/publish: env/clean env/install
	twine upload $(ENV_PKG_DIR)/dist/* || exit 1

endif # APPPY_ENV_MK_INCLUDED