.PHONY: init-db

init-db: ## Initialize database and load data
	@poetry run airflow db migrate
	@export AIRFLOW__CORE__DAGS_FOLDER=$$(pwd)/dags && poetry run airflow dags test load_data_to_postgres

.PHONY: run-api
run-api: ## Run API server
	@poetry run uvicorn app.main:app --host 127.0.0.1 --port 8010 &
