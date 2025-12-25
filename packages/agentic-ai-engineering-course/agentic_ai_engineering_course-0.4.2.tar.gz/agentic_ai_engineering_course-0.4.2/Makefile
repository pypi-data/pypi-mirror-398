# --- Deploying Python Package ---

VERSION_BUMP ?= patch

build:
	uv version --bump $(VERSION_BUMP) # or minor/major
	uv build

publish:
	uv publish --token $(PYPI_TOKEN)

clean:
	rm -rf ./dist


# --- Tests & QA ---

QA_FOLDERS := lessons/research_agent_part_2/ lessons/writing_workflow/ lessons/utils/

format-fix: # Auto-format Python code using ruff formatter.
	uv run ruff format $(QA_FOLDERS)

lint-fix: # Auto-fix linting issues using ruff linter.
	uv run ruff check --fix $(QA_FOLDERS)

format-check: # Check code formatting without making changes using ruff formatter.
	uv run ruff format --check $(QA_FOLDERS) 

lint-check: # Check code for linting issues without fixing them using ruff linter.
	uv run ruff check $(QA_FOLDERS)