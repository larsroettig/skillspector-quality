# skillspector-quality — developer tasks
#
# skillspector is not on PyPI; it is installed from a local checkout.
# Override its location with SKILLSPECTOR_SRC if it is not at ../SkillRater.

IMAGE            ?= skillspector-quality
TAG              ?= latest
SKILLSPECTOR_SRC ?= ../SkillRater
STAGE            := .docker-build/skillspector

.PHONY: help install test lint docker-build docker-run clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Set up the local venv (uv) with skillspector + this package
	./scripts/install.sh "$(SKILLSPECTOR_SRC)"

test: ## Run the test suite
	. .venv/bin/activate && python -m pytest -q

lint: ## Lint with ruff
	. .venv/bin/activate && ruff check src tests

docker-build: ## Build the Docker image (stages skillspector into the context)
	@test -f "$(SKILLSPECTOR_SRC)/pyproject.toml" \
		|| { echo "ERROR: no skillspector checkout at '$(SKILLSPECTOR_SRC)' (set SKILLSPECTOR_SRC)"; exit 1; }
	@echo ">> Staging skillspector from $(SKILLSPECTOR_SRC)"
	@rm -rf "$(STAGE)" && mkdir -p "$(STAGE)"
	@bash -c 'trap "rm -rf $(STAGE)" EXIT; \
		rsync -a --delete \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude "*.egg-info" \
		"$(SKILLSPECTOR_SRC)/" "$(STAGE)/"; \
		docker build -t "$(IMAGE):$(TAG)" .'
	@echo ">> Built $(IMAGE):$(TAG)"

docker-run: ## Scan the bundled fixture skill inside the image (no LLM)
	docker run --rm -v "$(CURDIR)/tests/fixtures/good-skill:/work/skill:ro" \
		"$(IMAGE):$(TAG)" scan /work/skill --no-llm

clean: ## Remove the Docker staging dir
	rm -rf .docker-build
