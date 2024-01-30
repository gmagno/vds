#!/usr/bin/env make

#--- SETUP --------------------------------#

SHELL := /bin/bash

VENV?=.venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip
BUILD_DIR=build
TESTS_DIR=tests
SRC_DIR=src

#--- PYTHON -------------------------------#

$(VENV):
	python3 -m venv $(VENV)
	${PIP} install -U pip
	${PIP} install pip-tools wheel

.PHONY: install
install: $(VENV) requirements.txt
	$(VENV)/bin/pip-sync

.PHONY: install-dev
install-dev: $(VENV) requirements-dev.txt
	$(VENV)/bin/pip-sync requirements-dev.txt
	$(VENV)/bin/pre-commit install

requirements.txt: pyproject.toml
	$(VENV)/bin/pip-compile -o requirements.txt pyproject.toml

requirements-dev.txt: pyproject.toml
	$(VENV)/bin/pip-compile -o requirements-dev.txt --extra dev pyproject.toml


#--- LINT -------------------------------#

.PHONY: lint
lint:
	${VENV}/bin/ruff check --fix --config pyproject.toml ${SRC_DIR} ${TESTS_DIR}
	${VENV}/bin/mypy ${SRC_DIR} ${TESTS_DIR}


#--- TEST -------------------------------#

.PHONY: run-debug
run-debug: ${VENV}
	PYDEVD_DISABLE_FILE_VALIDATION=1 ${VENV}/bin/watchmedo auto-restart --recursive -p '*.py' \
		-- python -m debugpy --listen 0.0.0.0:5678 --wait-for-client \
		-m uvicorn --factory vidoso.main:create_app --host 0.0.0.0 --port 8000 --app-dir src/



#--- INFRA -------------------------------#

.PHONY: infra-build
infra-build:
	docker compose -f docker/docker-compose.yml build

.PHONY: infra-run
infra-run:
	docker compose -f docker/docker-compose.yml up -d

.PHONY: infra-exec-sh
infra-exec-sh:
	docker compose -f docker/docker-compose.yml exec localstack /bin/sh

.PHONY: infra-logs
infra-logs:
	docker compose -f docker/docker-compose.yml logs -f

.PHONY: infra-stop
infra-stop:
	docker compose -f docker/docker-compose.yml down

.PHONY: localstack-status
localstack-status:
	localstack status services

.PHONY: db-local-admin-create-tables
db-local-admin-create-tables:
	dy admin create table jobs \
		--keys job_id,S created_at,N \
		--region local --port 4566 \
		--table jobs
	dy admin create table segments \
		--keys transcript_id,S segment_id,N \
		--region local --port 4566 \
		--table segments


.PHONY: db-local-admin-create-indexes
db-local-admin-create-indexes:
	dy admin create index \
		--region local --port 4566 \
		--table jobs user-index \
		--keys user,S created_at,N
	dy admin create index \
		--region local --port 4566 \
		--table segments user-index \
		--keys user,S created_at,N


#--- CLEANUP -----------------------------#

.PHONY: clean-build
clean-build:
	rm -rf ${BUILD_DIR}

.PHONY: clean-files
clean-files:
	find . \( \
		-name __pycache__ \
		-o -name "*.pyc" \
		-o -name .pytest_cache \
		-o -name .mypy_cache \
		-o -name "*.egg-info" \
		-o -name "build" \
		-o -name ".ruff_cache" \
	\) -exec rm -rf {} +

.PHONY: clean
clean: clean-build clean-files
