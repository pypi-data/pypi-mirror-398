.PHONY: help install run test clean docker-build docker-run

# Default target - show help
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run the development server"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Remove cache files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"

# Install dependencies
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

# Run development server with auto-reload
run:
	uvicorn app.main:app --reload

# Run tests
test:
	PYTHONPATH=. pytest -v tests/

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Build Docker image
docker-build:
	docker build -t fastapi-starter .

# Run Docker container
docker-run:
	docker run --rm -p 8000:8000 fastapi-starter
