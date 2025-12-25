# Invalid target with = sign
target=value: prerequisites
	recipe

# Invalid target with .RECIPEPREFIX character
.RECIPEPREFIX := >
>invalid: prerequisites
	recipe

VARIABLE = http://www.github.com
VARIABLE = http://www.github.com

## Run ollama in cpu mode
ollama/run/cpu: DOCKER_IMAGE_NAME = ollama-wrapper
ollama/run/cpu: DOCKER_UID ?= $(shell id -u)
ollama/run/cpu: DOCKER_GID ?= $(shell id -g)
ollama/run/cpu: MODEL ?= llama3.1
ollama/run/cpu: .make/ollama-docker FORCE
	docker container rm ollama ; true
	docker run \
		--detach \
		--name ollama \
		--publish 11434:11434 \
		--user $(DOCKER_UID):$(DOCKER_GID) \
		--volume $(CURDIR)/data/ollama:/home/ollama/.ollama \
		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(MODEL)
