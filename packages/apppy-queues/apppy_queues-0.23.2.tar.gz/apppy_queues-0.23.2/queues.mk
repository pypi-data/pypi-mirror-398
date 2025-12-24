ifndef APPPY_QUEUES_MK_INCLUDED
APPPY_QUEUES_MK_INCLUDED := 1
QUEUES_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: queues queues-dev queues/build queues/clean queues/install queues/install-dev

queues: queues/clean queues/install

queues-dev: queues/clean queues/install-dev

queues/build:
	cd $(QUEUES_PKG_DIR) && uvx --from build pyproject-build

queues/clean:
	cd $(QUEUES_PKG_DIR) && rm -rf dist/ *.egg-info .venv

queues/install: queues/build
	cd $(QUEUES_PKG_DIR) && uv pip install dist/*.whl

queues/install-dev:
	cd $(QUEUES_PKG_DIR) && uv pip install -e .

queues/publish: queues/clean queues/install
	twine upload $(QUEUES_PKG_DIR)/dist/* || exit 1

endif # APPPY_QUEUES_MK_INCLUDED