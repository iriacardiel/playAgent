.PHONY: help dev-frontend dev-backend dev

help:
	@echo "Available commands:"
	@echo "  make dev-frontend    - Starts the frontend development server (Vite)"
	@echo "  make dev-backend     - Starts the backend development server (Uvicorn with reload)"
	@echo "  make dev             - Starts both frontend and backend development servers"

dev-frontend:
	@echo "Starting frontend development server..."
	@cd frontend && pnpm dev

dev-backend:
	@echo "Starting backend development server..."
	@cd backend && exec langgraph dev --config ./langgraph.json --allow-blocking --no-browser --no-reload

dev-backend-multi:
	@echo "Starting backend development server..."
	@cd backend && exec langgraph dev --config ./langgraph.multi.json --allow-blocking --no-browser

# Run frontend and backend concurrently
dev:
	@echo "Starting both frontend and backend development servers..."
	@make dev-frontend & make dev-backend 

# curl http://localhost:2024/api/transcribe/test