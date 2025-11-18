from datetime import datetime
import csv

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator


default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 12, 1),
}

CSV_FILE_PATH = "/opt/airflow/sample_files/olap.csv"
OUTPUT_SQL_PATH = "/opt/airflow/dags/sql/insert_queries_olap.sql"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sample.telemetry (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER,
    prosthesis_type  TEXT,
    muscle_group     TEXT,
    signal_frequency INTEGER,
    signal_duration  INTEGER,
    signal_amplitude NUMERIC(10,4),
    signal_time      TIMESTAMP
);
"""


def generate_insert_queries():
    """Читает CSV и генерирует INSERT-запросы в файл OUTPUT_SQL_PATH для таблицы telemetry."""
    with open(CSV_FILE_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        with open(OUTPUT_SQL_PATH, "w", encoding="utf-8") as sqlfile:
            for row in reader:
                cols = [
                    "user_id",
                    "prosthesis_type",
                    "muscle_group",
                    "signal_frequency",
                    "signal_duration",
                    "signal_amplitude",
                    "signal_time",
                ]

                values = []
                for col in cols:
                    v = row.get(col)

                    if v is None or v == "":
                        values.append("NULL")
                        continue

                    if col in ["user_id", "signal_frequency", "signal_duration"]:
                        values.append(str(int(v)))
                    elif col in ["signal_amplitude"]:
                        values.append(str(float(v)))
                    elif col == "signal_time":
                        values.append(f"'{v}'")
                    else:
                        v_escaped = v.replace("'", "''")
                        values.append(f"'{v_escaped}'")

                sql = (
                    "INSERT INTO sample.telemetry "
                    "(user_id, prosthesis_type, muscle_group, "
                    "signal_frequency, signal_duration, signal_amplitude, signal_time) "
                    f"VALUES ({', '.join(values)});\n"
                )
                sqlfile.write(sql)


with DAG(
    dag_id="telemetry_olap_dag",
    default_args=default_args,
    schedule_interval=None,  
    catchup=False,
) as dag:

    create_table = PostgresOperator(
        task_id="create_telemetry_table",
        postgres_conn_id="write_to_pg",
        sql=CREATE_TABLE_SQL,
    )

    generate_queries = PythonOperator(
        task_id="generate_olap_insert_queries",
        python_callable=generate_insert_queries,
    )

    run_insert_queries = PostgresOperator(
        task_id="run_olap_insert_queries",
        postgres_conn_id="write_to_pg",
        sql="sql/insert_queries_olap.sql",
    )

    create_table >> generate_queries >> run_insert_queries
