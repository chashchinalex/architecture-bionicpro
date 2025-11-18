from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import csv

# Аргументы по умолчанию
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 12, 1),
}

# Функция генерации SQL из crm.csv
def generate_insert_queries():
    # В docker-compose ./data примонтирован как /opt/airflow/sample_files
    CSV_FILE_PATH = '/opt/airflow/sample_files/crm.csv'
    OUTPUT_SQL_PATH = '/opt/airflow/dags/sql/insert_queries_crm.sql'

    with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    if not rows:
        # Пустой файл — просто выходим
        return

    columns = list(rows[0].keys())

    insert_statements = []
    for row in rows:
        values = []
        for col in columns:
            val = row.get(col, '')
            if val is None:
                val = ''
            # Экранируем одинарные кавычки
            val = str(val).replace("'", "''")
            values.append(f"'{val}'")

        statement = (
            f"INSERT INTO sample.crm  ({', '.join(columns)}) "
            f"VALUES ({', '.join(values)});"
        )
        insert_statements.append(statement)

    with open(OUTPUT_SQL_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(insert_statements))


# Глобальный объект DAG — ВАЖНО, без условий / функций
dag = DAG(
    dag_id='crm_csv_loader',
    default_args=default_args,
    schedule_interval=None,  # запускаете вручную
    catchup=False,
)

# 1. Создаём таблицу под структуру crm.csv
create_table = PostgresOperator(
    task_id='create_crm_table',
    postgres_conn_id='write_to_pg',
    sql="""
    CREATE TABLE IF NOT EXISTS sample.crm (
        id      INTEGER,
        name    TEXT,
        email   TEXT,
        age     INTEGER,
        gender  TEXT,
        country TEXT,
        address TEXT,
        phone   TEXT
    );
    """,
    dag=dag,
)

# 2. Генерируем файл sql/insert_queries_crm.sql из crm.csv
generate_queries = PythonOperator(
    task_id='generate_crm_insert_queries',
    python_callable=generate_insert_queries,
    dag=dag,
)

# 3. Выполняем сгенерированные INSERT'ы
run_insert_queries = PostgresOperator(
    task_id='run_crm_insert_queries',
    postgres_conn_id='write_to_pg',
    sql='sql/insert_queries_crm.sql',  # путь относительно /opt/airflow/dags
    dag=dag,
)

# Задаём зависимости — тоже на глобальном уровне
create_table >> generate_queries >> run_insert_queries
