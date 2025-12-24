ifndef APPPY_FS_MK_INCLUDED
APPPY_FS_MK_INCLUDED := 1
FS_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: fs fs-dev fs/build fs/clean fs/install fs/install-dev

fs: fs/clean fs/install

fs-dev: fs/clean fs/install-dev

fs/build:
	cd $(FS_PKG_DIR) && uvx --from build pyproject-build

fs/clean:
	cd $(FS_PKG_DIR) && rm -rf dist/ *.egg-info .venv

fs/install: fs/build
	cd $(FS_PKG_DIR) && uv pip install dist/*.whl

fs/install-dev:
	cd $(FS_PKG_DIR) && uv pip install -e .

fs/publish: fs/clean fs/install
	twine upload $(FS_PKG_DIR)/dist/* || exit 1

endif # APPPY_FS_MK_INCLUDED