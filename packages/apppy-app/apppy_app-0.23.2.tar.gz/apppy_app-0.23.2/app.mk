ifndef APPPY_APP_MK_INCLUDED
APPPY_APP_MK_INCLUDED := 1
APP_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: app app-dev app/build app/clean app/install app/install-dev

app: app/clean app/install

app-dev: app/clean app/install-dev

app/build:
	cd $(APP_PKG_DIR) && uvx --from build pyproject-build

app/clean:
	cd $(APP_PKG_DIR) && rm -rf dist/ *.egg-info .venv

app/install: app/build
	cd $(APP_PKG_DIR) && uv pip install dist/*.whl

app/install-dev:
	cd $(APP_PKG_DIR) && uv pip install -e .

app/publish: app/clean app/install
	twine upload $(APP_PKG_DIR)/dist/* || exit 1

endif # APPPY_APP_MK_INCLUDED