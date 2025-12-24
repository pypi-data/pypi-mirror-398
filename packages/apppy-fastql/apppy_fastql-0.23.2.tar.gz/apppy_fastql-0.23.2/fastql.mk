ifndef APPPY_FASTQL_MK_INCLUDED
APPPY_FASTQL_MK_INCLUDED := 1
FASTQL_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: fastql fastql-dev fastql/build fastql/clean fastql/install fastql/install-dev

fastql: fastql/clean fastql/install

fastql-dev: fastql/clean fastql/install-dev

fastql/build:
	cd $(FASTQL_PKG_DIR) && uvx --from build pyproject-build

fastql/clean:
	cd $(FASTQL_PKG_DIR) && rm -rf dist/ *.egg-info .venv

fastql/install: fastql/build
	cd $(FASTQL_PKG_DIR) && uv pip install dist/*.whl

fastql/install-dev:
	cd $(FASTQL_PKG_DIR) && uv pip install -e .

fastql/publish: fastql/clean fastql/install
	twine upload $(FASTQL_PKG_DIR)/dist/* || exit 1

endif # APPPY_FASTQL_MK_INCLUDED