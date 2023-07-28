format:
	docker compose run dev sh -c \
		"isort $(if $(check),--check,) src tests && black $(if $(check),--check,) src tests"

check-types:
	docker compose run dev mypy src tests

test:
	docker compose run dev pytest tests
