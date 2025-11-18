import logging
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator

logging.basicConfig(level=logging.INFO)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

CREATE_OLAP_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sample.olap_table (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    user_name TEXT,
    email TEXT,
    prosthesis_type TEXT,
    muscle_group TEXT,
    avg_signal_frequency NUMERIC(10, 4),
    avg_signal_duration NUMERIC(10, 4),
    avg_signal_amplitude NUMERIC(10, 4),
    last_signal_time TIMESTAMP
);
"""

def extract_data():
    try:
        pg_hook = PostgresHook(postgres_conn_id="write_to_pg")

        query = """
        SELECT 
            c.id AS user_id,
            max(c.name) AS user_name,
            max(c.email) AS email,
            t.prosthesis_type,
            t.muscle_group,
            avg(t.signal_frequency) AS avg_signal_frequency,
            avg(t.signal_duration) AS avg_signal_duration,
            avg(t.signal_amplitude) AS avg_signal_amplitude,
            max(t.signal_time) AS last_signal_time
        FROM sample.crm c
        LEFT JOIN sample.telemetry t ON c.id = t.user_id
        GROUP BY 
            c.id, t.prosthesis_type, t.muscle_group
        """

        connection = pg_hook.get_conn()
        cursor = connection.cursor()
        cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        connection.close()

        df = pd.DataFrame(results, columns=columns)
        df["last_signal_time"] = pd.to_datetime(df["last_signal_time"], errors="coerce")

        for col in ["avg_signal_frequency", "avg_signal_duration", "avg_signal_amplitude"]:
            df[col] = df[col].astype(float)

        df["last_signal_time"] = df["last_signal_time"].apply(
            lambda x: x.isoformat() if pd.notnull(x) else None
        )

        return df.to_dict(orient="records")

    except Exception as e:
        logging.error(f"Error extracting data: {str(e)}")
        raise


def transform_data(**kwargs):
    ti = kwargs["ti"]
    records = ti.xcom_pull(task_ids="extract_data")

    if not records:
        return []

    df = pd.DataFrame(records)

    df["avg_signal_frequency"] = pd.to_numeric(df["avg_signal_frequency"], errors="coerce")
    df["avg_signal_duration"] = pd.to_numeric(df["avg_signal_duration"], errors="coerce")
    df["avg_signal_amplitude"] = pd.to_numeric(df["avg_signal_amplitude"], errors="coerce")

    df["last_signal_time"] = pd.to_datetime(df["last_signal_time"], errors="coerce")
    df["last_signal_time"] = df["last_signal_time"].apply(
        lambda x: x.isoformat() if pd.notnull(x) else None
    )

    df = df.dropna(subset=["user_id"])

    df.fillna({
        "avg_signal_frequency": 0,
        "avg_signal_duration": 0,
        "avg_signal_amplitude": 0
    }, inplace=True)

    return df.to_dict(orient="records")


def load_to_olap(**kwargs):
    ti = kwargs["ti"]
    records = ti.xcom_pull(task_ids="transform_data")

    if not records:
        return

    try:
        pg_hook = PostgresHook(postgres_conn_id="write_to_pg")
        connection = pg_hook.get_conn()
        cursor = connection.cursor()

        insert_sql = """
        INSERT INTO sample.olap_table (
            user_id,
            user_name,
            email,
            prosthesis_type,
            muscle_group,
            avg_signal_frequency,
            avg_signal_duration,
            avg_signal_amplitude,
            last_signal_time
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        rows = []
        for row in records:
            record = (
                row["user_id"],
                row.get("user_name"),
                row.get("email"),
                row.get("prosthesis_type"),
                row.get("muscle_group"),
                row.get("avg_signal_frequency"),
                row.get("avg_signal_duration"),
                row.get("avg_signal_amplitude"),
                row.get("last_signal_time"),
            )
            rows.append(record)

        cursor.executemany(insert_sql, rows)
        connection.commit()

        cursor.close()
        connection.close()

    except Exception as e:
        logging.error(f"Error loading data to OLAP: {str(e)}")
        raise


with DAG(
    "olap_pipeline",
    default_args=default_args,
    schedule_interval="0 0 * * *",
    tags=["olap", "prosthesis", "etl"],
    catchup=False,
) as dag:

    create_olap_table = PostgresOperator(
        task_id="create_olap_table",
        postgres_conn_id="write_to_pg",
        sql=CREATE_OLAP_TABLE_SQL,
    )

    extract_task = PythonOperator(
        task_id="extract_data",
        python_callable=extract_data,
    )

    transform_task = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
    )

    load_task = PythonOperator(
        task_id="load_to_olap",
        python_callable=load_to_olap,
    )

    create_olap_table >> extract_task >> transform_task >> load_task
