#!make
-include .env
export $(shell sed 's/=.*//' .env)
SHELL := /bin/bash

IMAGE_NAME = docker.io/icewreck/searxng-mcp-server:latest

.PHONY: *

pex: build
	uvx pex -r requirements.txt . -o ./build/searxng-mcp-server -e searxng_mcp_server:main --python python3

build:
	# build python package
	rm -rf dist/
	rm -rf searxng_mcp_server.egg-info
	uv pip compile pyproject.toml > requirements.txt
	uv build
	podman build -t $(IMAGE_NAME) .

publish: build
	podman push $(IMAGE_NAME)
	uv publish

develop:
	uv venv ./.venv
	uv sync
	uv pip install -e .
	touch .env

format:
	uv tool run ruff format ./src

lint:
	uv tool run ruff check --fix src/
	uv tool run ruff check

mypy:
	uv run mypy ./src

run:
	uv run searxng-mcp-server

run-container:
	podman run --rm -it \
		--name searxng-mcp-server \
		$(IMAGE_NAME)

inspector:
	npx @modelcontextprotocol/inspector uv run searxng-mcp-server
