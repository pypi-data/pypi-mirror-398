.PHONY: start stop restart build logs clean

# Default ports (can be overridden by environment variables)
DB_PORT ?= 5432
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000

start:
	@echo "Starting project on ports: DB=$(DB_PORT), Backend=$(BACKEND_PORT), Frontend=$(FRONTEND_PORT)"
	DB_PORT=$(DB_PORT) BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) docker compose up -d

stop:
	@echo "Stopping project..."
	docker compose down

restart: stop start

build:
	@echo "Building project..."
	DB_PORT=$(DB_PORT) BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) docker compose up -d --build

logs:
	docker compose logs -f

clean:
	@echo "Cleaning up containers, networks, and volumes..."
	docker compose down -v
