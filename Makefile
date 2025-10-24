.PHONY: build 

build:
	docker compose down -v
	docker compose up -d --build api

.PHONY: test

test:
	docker compose run tests