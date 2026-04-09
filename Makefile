.PHONY: install dev test lint clean serve deploy fetch-model

# Create venv and install deps
install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Install with dev deps (pytest, mypy, ruff)
dev:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

# Run tests
test:
	.venv/bin/pytest tests/ -v

# Lint + type check
lint:
	.venv/bin/ruff check src/ tests/
	.venv/bin/mypy src/

# Remove all Python artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/

# Run MCP server locally
serve:
	.venv/bin/python -m src.server

# Deploy to Vercel
deploy:
	vercel --prod

# Download EyeQ model weights
fetch-model:
	mkdir -p src/ml/weights
	.venv/bin/python -c "from src.ml.eyeq import download_weights; download_weights()"
