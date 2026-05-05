.PHONY: api dashboard test lint migrate

api:
	scripts/run_api.sh

dashboard:
	scripts/run_dashboard.sh

test:
	scripts/test.sh

lint:
	ruff check .

migrate:
	alembic upgrade head
