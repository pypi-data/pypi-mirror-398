# Copyright 2025 PageKey Solutions, LLC

.PHONY: all build clean publish
all: build


# Variables.
DIST := dist
PACKAGE := dist/unit_sdk.tar.gz
SRC := $(shell find . -type f -name '*.py')


# Targets.
$(DIST):
	mkdir -p $(DIST)

$(PACKAGE): $(DIST) pyproject.toml $(SRC)
	uv build
	cp dist/unit_sdk-*.tar.gz $(PACKAGE)


# Phony Targets.
build: $(PACKAGE)

clean:
	rm -rf $(DIST) *.egg-info

publish: build
	uv run --with twine twine upload --repository-url $(TWINE_REPOSITORY) dist/*
