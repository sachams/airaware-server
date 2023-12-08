app_name		= server

shell:
	@echo "---> Starting shell"
	@touch .bash_history
	@COMPOSE_DOCKER_CLI_BUILD=1 \
	 DOCKER_BUILDKIT=1 \
	 docker compose run \
	 --name server$(app_name) --service-ports --rm $(app_name) bash
.PHONY: shell

build:
	@echo "---> Building development image"
	@COMPOSE_DOCKER_CLI_BUILD=1 \
	 DOCKER_BUILDKIT=1 \
	 docker compose build $(app_name)
.PHONY: build

export_reqs:
	poetry export -f requirements.txt --output requirements.txt
.PHONY: export_reqs

export_dev_reqs:
	poetry export -f requirements.txt --only=dev --output dev_requirements.txt
.PHONY: export_dev_reqs