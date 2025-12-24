ifndef APPPY_AUTH_MK_INCLUDED
APPPY_AUTH_MK_INCLUDED := 1
AUTH_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: auth auth-dev auth/build auth/clean auth/install auth/install-dev

auth: auth/clean auth/install

auth-dev: auth/clean auth/install-dev

auth/build:
	cd $(AUTH_PKG_DIR) && uvx --from build pyproject-build

auth/clean:
	cd $(AUTH_PKG_DIR) && rm -rf dist/ *.egg-info .venv

auth/install: auth/build
	cd $(AUTH_PKG_DIR) && uv pip install dist/*.whl

auth/install-dev:
	cd $(AUTH_PKG_DIR) && uv pip install -e .

auth/publish: auth/clean auth/install
	twine upload $(AUTH_PKG_DIR)/dist/* || exit 1

endif # APPPY_AUTH_MK_INCLUDED