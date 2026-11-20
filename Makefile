VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
CONFIG ?= config/default.json
ENTRYPOINT ?= pac-man.py
MAZE_WHEEL := mazegenerator-00001-py3-none-any.whl
BUILD_DIR := dist
BUILD_ARCHIVE := $(BUILD_DIR)/pacman.tar.gz
BUILD_CONTENTS := README.md Makefile pac-man.py \
	config data/highscores.json src pacman_sprite $(MAZE_WHEEL)

MYPY_FLAGS := --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

.PHONY: install run debug clean lint lint-strict build venv

venv: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install ./$(MAZE_WHEEL) flake8 mypy pygame

run: venv
	$(PYTHON) $(ENTRYPOINT) $(CONFIG)

debug: venv
	$(PYTHON) -m pdb $(ENTRYPOINT) $(CONFIG)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov $(VENV)
	find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".coverage" \) -delete

build:
	mkdir -p $(BUILD_DIR)
	tar \
		--exclude='*/__pycache__' \
		--exclude='*.pyc' \
		--exclude='*.pyo' \
		-czf $(BUILD_ARCHIVE) $(BUILD_CONTENTS)
	@echo "Package created: $(BUILD_ARCHIVE)"

lint: venv
	$(VENV)/bin/flake8 --exclude=$(VENV) .
	$(VENV)/bin/mypy --exclude $(VENV) . $(MYPY_FLAGS)

lint-strict: venv
	$(VENV)/bin/flake8 --exclude=$(VENV) .
	$(VENV)/bin/mypy --exclude $(VENV) . --strict
