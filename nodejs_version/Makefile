# Makefile for Node.js Tool Calling API
# Similar to the Python version's Makefile

.ONESHELL:
.DEFAULT_GOAL := help

# Color definitions
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "${GREEN}Installing dependencies...${NC}"
	npm install

dev: ## Run in development mode with hot reload
	@echo "${GREEN}Starting development server...${NC}"
	npm run dev

start: ## Run in production mode
	@echo "${GREEN}Starting production server...${NC}"
	npm start

test: ## Run tests
	@echo "${GREEN}Running tests...${NC}"
	npm test

test-watch: ## Run tests in watch mode
	@echo "${GREEN}Running tests in watch mode...${NC}"
	npm run test:watch

lint: ## Run linter
	@echo "${GREEN}Running linter...${NC}"
	npm run lint

lint-fix: ## Fix linting issues
	@echo "${GREEN}Fixing linting issues...${NC}"
	npm run lint:fix

format: ## Format code
	@echo "${GREEN}Formatting code...${NC}"
	npm run format

format-check: ## Check code formatting
	@echo "${GREEN}Checking code formatting...${NC}"
	npm run format:check

clean: ## Clean generated files
	@echo "${YELLOW}Cleaning generated files...${NC}"
	rm -rf node_modules
	rm -rf coverage
	rm -rf *.log
	rm -rf logs
	@echo "${GREEN}Clean complete${NC}"

check: lint format-check test ## Run all checks (lint, format-check, test)
	@echo "${GREEN}All checks passed!${NC}"

setup: install ## Setup the project
	@echo "${GREEN}Setting up project...${NC}"
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Creating .env file from .env.example...${NC}"; \
		cp .env.example .env; \
		echo "${YELLOW}Please edit .env and add your credentials${NC}"; \
	else \
		echo "${GREEN}.env file already exists${NC}"; \
	fi
	@echo "${GREEN}Setup complete!${NC}"

docker-build: ## Build Docker image
	@echo "${GREEN}Building Docker image...${NC}"
	docker build -t tool-calling-api-nodejs .

docker-run: ## Run Docker container
	@echo "${GREEN}Running Docker container...${NC}"
	docker run -p 3000:3000 --env-file .env tool-calling-api-nodejs

.PHONY: help install dev start test test-watch lint lint-fix format format-check clean check setup docker-build docker-run
