ifndef APPPY_SB_MK_INCLUDED
APPPY_SB_MK_INCLUDED := 1
SB_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: sb sb-dev sb/build sb/clean sb/install sb/install-dev

sb: sb/clean sb/install

sb-dev: sb/clean sb/install-dev

sb/build:
	cd $(SB_PKG_DIR) && uvx --from build pyproject-build

sb/clean:
	cd $(SB_PKG_DIR) && rm -rf dist/ *.egg-info .venv

sb/install: sb/build
	cd $(SB_PKG_DIR) && uv pip install dist/*.whl

sb/install-dev:
	cd $(SB_PKG_DIR) && uv pip install -e .

sb/publish: sb/clean sb/install
	twine upload $(SB_PKG_DIR)/dist/* || exit 1

endif # APPPY_SB_MK_INCLUDED