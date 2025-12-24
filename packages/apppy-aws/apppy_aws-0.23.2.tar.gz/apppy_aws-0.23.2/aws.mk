ifndef APPPY_AWS_MK_INCLUDED
APPPY_AWS_MK_INCLUDED := 1
AWS_PKG_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.PHONY: aws aws-dev aws/build aws/clean aws/install aws/install-dev

aws: aws/clean aws/install

aws-dev: aws/clean aws/install-dev

aws/build:
	cd $(AWS_PKG_DIR) && uvx --from build pyproject-build

aws/clean:
	cd $(AWS_PKG_DIR) && rm -rf dist/ *.egg-info .venv

aws/install: aws/build
	cd $(AWS_PKG_DIR) && uv pip install dist/*.whl

aws/install-dev:
	cd $(AWS_PKG_DIR) && uv pip install -e .

aws/publish: aws/clean aws/install
	twine upload $(AWS_PKG_DIR)/dist/* || exit 1

endif # APPPY_AWS_MK_INCLUDED