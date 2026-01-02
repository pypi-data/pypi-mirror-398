.PHONY: help install-dev build test clean check format lint publish

help:
	@echo "Mirage - Unified Privacy SDK for Solana"
	@echo ""
	@echo "Available targets:"
	@echo "  make install-dev    - Install package in development mode"
	@echo "  make build          - Build release wheel"
	@echo "  make test           - Run all tests"
	@echo "  make check          - Check Rust code"
	@echo "  make format         - Format Python and Rust code"
	@echo "  make lint           - Lint Python code"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make publish        - Publish to PyPI"

install-dev:
	@echo "Installing Mirage in development mode..."
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop --release

build:
	@echo "Building Mirage release wheel..."
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin build --release --interpreter python3.10 python3.11 python3.12 python3.13

test:
	@echo "Running tests..."
	pytest tests/ -v

check:
	@echo "Checking Rust code..."
	cargo check

format:
	@echo "Formatting code..."
	cargo fmt
	black mirage/ tests/ examples/
	ruff check --fix mirage/ tests/ examples/

lint:
	@echo "Linting Python code..."
	ruff check mirage/ tests/ examples/
	mypy mirage/

clean:
	@echo "Cleaning build artifacts..."
	cargo clean
	rm -rf target/
	rm -f mirage/*.so
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned!"

publish:
	@echo "Publishing to PyPI..."
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin publish
