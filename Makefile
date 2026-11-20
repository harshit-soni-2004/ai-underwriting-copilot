# Makefile for AI Underwriting Copilot

.PHONY: up down build test test-core test-ai eval seed lint clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

test: test-core test-ai

test-core:
	cd core-service && mvn clean test

test-ai:
	cd ai-service && pytest

eval:
	python evals/run_all.py

seed:
	python data-gen/generate_data.py --applicants 100 --seed 42

clean:
	cd core-service && mvn clean
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
