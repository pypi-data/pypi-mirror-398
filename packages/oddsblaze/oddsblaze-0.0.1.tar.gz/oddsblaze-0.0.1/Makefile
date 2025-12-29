.PHONY: docs docs-live docs-clean

docs:
	JUPYTER_PLATFORM_DIRS=1 uv run --group docs mkdocs build --clean

docs-live:
	JUPYTER_PLATFORM_DIRS=1 uv run --group docs mkdocs serve --dev-addr 0.0.0.0:8000

docs-clean:
	rm -rf site