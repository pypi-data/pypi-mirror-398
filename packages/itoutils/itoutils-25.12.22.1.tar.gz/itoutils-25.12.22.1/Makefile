# Delete target on error.
# https://www.gnu.org/software/make/manual/html_node/Errors.html#Errors
# > This is almost always what you want make to do, but it is not historical
# > practice; so for compatibility, you must explicitly request it
.DELETE_ON_ERROR:

# Global tasks.
# =============================================================================
LINTER_CHECKED_DIRS := src tests testproject

VIRTUAL_ENV ?= .venv
export PATH := $(VIRTUAL_ENV)/bin:$(PATH)

.PHONY: venv quality fix test

$(VIRTUAL_ENV): uv.lock
	uv venv
	uv sync --all-groups
	touch $@

venv: $(VIRTUAL_ENV)

quality: $(VIRTUAL_ENV)
	ruff format --check $(LINTER_CHECKED_DIRS)
	ruff check $(LINTER_CHECKED_DIRS)
	# Make sure pytest help is still accessible.
	pytest --help >/dev/null

fix: $(VIRTUAL_ENV)
	ruff format $(LINTER_CHECKED_DIRS)
	ruff check --fix $(LINTER_CHECKED_DIRS)

test: $(VIRTUAL_ENV)
	pytest --create-db $(TARGET)
