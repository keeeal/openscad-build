build:
	docker compose build $(service)

format:
	docker compose run dev sh -c \
		"isort src && black src && isort tests && black tests"

test:
	docker compose run dev pytest tests
