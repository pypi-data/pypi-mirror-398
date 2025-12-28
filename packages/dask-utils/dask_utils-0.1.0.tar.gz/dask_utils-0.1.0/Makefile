CURRENT_DIR = $(shell pwd)
REPORT_OUTPUT_DIR = ./report
all: info

info:  ## Show this infomation
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install:  ## Create virtualenv
	uv sync --all-extras

update:   ## Update dependencies
	uv lock

test:  ## Run tests
	uv run pytest

coverage:
	uv run pytest \
		--cov=dask_utils \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=80

reports: ## Generate unit test report / coverage report
	uv run pytest --html=$(REPORT_OUTPUT_DIR)/test/pytests.html --self-contained-html
	uv run coverage html -d $(REPORT_OUTPUT_DIR)/coverage_html

docs: ## Generate API documents
	export DASK_UTILS_ROOT_CONFIG=$(CURRENT_DIR)/tests/data/mlb_with_client.cfg && uv run  sphinx-apidoc -T -M --separate -o docs src && uv run make -C docs html

.PHONY: info all install update test docs
