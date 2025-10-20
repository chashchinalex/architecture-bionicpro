docker compose build airflow-init airflow-webserver airflow-scheduler airflow-triggerer

docker compose up -d postgres postgres-crm postgres-telemetry postgres-olap

docker compose exec postgres-olap psql -U olap_user -d olap_db -c "create extension if not exists dblink;"

docker compose run --rm airflow-init

docker compose up airflow-webserver airflow-scheduler airflow-triggerer
