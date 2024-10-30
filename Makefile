# Makefile for Network Protocol Testing Framework

.PHONY: install lock pytest clean flake isort black lint update-reports up down restart test

# Install dependencies using Poetry
install:
	poetry install

# Lock dependencies
lock:
	poetry lock

# Run all tests using our CLI runner
test-runner:
	@poetry run python -m src.cli.runner

# Run specific test module(s)
test-%:
	@poetry run python -m src.cli.runner $*

# Run pytest tests (for backward compatibility)
pytest:
	@poetry run pytest src/tests/

# Clean up pycache and temporary files
clean:
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +

.PHONY: isort
isort:
	@poetry run isort .

.PHONY: flake
flake:
	@poetry run flake8 .

.PHONY: black
black:
	@poetry run black .

# Lint: Run isort, flake8, and black in sequence
lint: isort black

# Bring up Docker containers
up:
	docker-compose up -d

# Bring down Docker containers
down:
	docker-compose down

.PHONY: update-reports
update-reports:
	bash src/helpers/reporting/update_symlinks.sh

# Restart Docker containers
restart: down up

test: test-runner update-reports
