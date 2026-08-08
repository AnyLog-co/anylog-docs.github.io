COMPOSE_FILE := ./docker-compose.yaml
CONTAINER    := anylog-docs

# Directory to mount as the documentation source.
# Override on the command line, e.g.:
#   make up LOCAL_DOCS=/path/to/docs
LOCAL_DOCS ?= .

.PHONY: up logs down clean check-dir help

.DEFAULT_GOAL := help

help:
	@echo "Usage: make [target] [LOCAL_DOCS=/path/to/docs]"
	@echo ""
	@echo "Targets:"
	@echo "  up      Start the docs container (docker compose up -d)"
	@echo "  logs    Follow logs for the $(CONTAINER) container"
	@echo "  down    Stop the docs container (docker compose down)"
	@echo "  clean   Stop and remove containers, volumes, and images"
	@echo "  help    Show this message"
	@echo ""
	@echo "LOCAL_DOCS defaults to '.' and sets the mounted documentation directory."

# Validate LOCAL_DOCS exists before doing anything, unless it's "."
check-dir:
	@if [ "$(LOCAL_DOCS)" != "." ] && [ ! -d "$(LOCAL_DOCS)" ]; then \
		echo "Failed to locate Docker directory: $(LOCAL_DOCS)"; \
		exit 1; \
	fi

up: check-dir
	LOCAL_DOCS=$(LOCAL_DOCS) docker compose -f $(COMPOSE_FILE) up --build -d

logs:
	docker logs -f $(CONTAINER)

down: check-dir
	LOCAL_DOCS=$(LOCAL_DOCS) docker compose -f $(COMPOSE_FILE) down

clean: check-dir
	LOCAL_DOCS=$(LOCAL_DOCS) docker compose -f $(COMPOSE_FILE) down -v --rmi all

# Catch-all: anything that isn't a defined target is an invalid option
%:
	@echo "Invalid option: $@"
	@$(MAKE) --no-print-directory help
	@exit 1