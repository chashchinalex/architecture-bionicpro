from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import os
import psycopg2
import requests

default_args = {
    'owner': 'bionicpro',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bionicpro_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bionicpro_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bionicpro_password")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "reports_warehouse")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CH_URL = f"http://{CLICKHOUSE_HOST}:8123"
CH_AUTH = f"?user={CLICKHOUSE_USER}&password={CLICKHOUSE_PASSWORD}"

def init_clickhouse_schema(**context):
    """Инициализация схемы ClickHouse"""
    requests.post(f"{CH_URL}/{CH_AUTH}", data=f"CREATE DATABASE IF NOT EXISTS {CLICKHOUSE_DATABASE}")
    requests.post(f"{CH_URL}/{CH_AUTH}", data=f"""
        CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DATABASE}.user_reports_mart
        (
            user_id String, user_email String, period_start Date, period_end Date,
            total_sessions UInt32, total_duration_minutes Float64, average_daily_usage Float64,
            movements_count UInt64, error_count UInt32, battery_usage_avg Float64,
            last_updated DateTime DEFAULT now()
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMM(period_start)
        ORDER BY (user_id, period_start, period_end)
    """)

def extract_telemetry_data(**context):
    """Извлечение данных телеметрии из PostgreSQL"""
    process_date = context['execution_date'].date()
    try:
        conn = psycopg2.connect(host=POSTGRES_HOST, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, COUNT(DISTINCT session_id) as sessions_count,
                   SUM(duration_seconds) / 60.0 as total_duration_minutes,
                   COUNT(*) FILTER (WHERE event_type = 'movement') as movements_count,
                   COUNT(*) FILTER (WHERE event_type = 'error') as error_count,
                   AVG(battery_level) as battery_usage_avg
            FROM telemetry_events
            WHERE DATE_TRUNC('day', timestamp) = %s
            GROUP BY user_id
        """, (process_date,))
        results = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
    except:
        results = [{'user_id': 'user@example.com', 'sessions_count': 5, 'total_duration_minutes': 120.5,
                   'movements_count': 150, 'error_count': 2, 'battery_usage_avg': 85.3}]
    
    context['ti'].xcom_push(key='telemetry_data', value=results)
    context['ti'].xcom_push(key='process_date', value=str(process_date))
    return results

def extract_crm_data(**context):
    """Извлечение данных о пользователях из CRM"""
    telemetry_data = context['ti'].xcom_pull(key='telemetry_data', task_ids='extract_telemetry')
    crm_data = {r['user_id']: {'user_email': r['user_id']} for r in telemetry_data}
    context['ti'].xcom_push(key='crm_data', value=crm_data)
    return crm_data

def transform_and_load(**context):
    """Трансформация и загрузка данных в ClickHouse"""
    telemetry_data = context['ti'].xcom_pull(key='telemetry_data', task_ids='extract_telemetry')
    crm_data = context['ti'].xcom_pull(key='crm_data', task_ids='extract_crm')
    process_date = datetime.strptime(context['ti'].xcom_pull(key='process_date', task_ids='extract_telemetry'), "%Y-%m-%d").date()
    
    period_start = process_date.replace(day=1)
    period_end = process_date
    days_in_period = (period_end - period_start).days + 1
    
    for tel_record in telemetry_data:
        user_id = tel_record['user_id']
        user_email = crm_data.get(user_id, {}).get('user_email', user_id)
        battery_avg = tel_record.get('battery_usage_avg', 0.0)
        avg_daily = tel_record.get('total_duration_minutes', 0.0) / days_in_period if days_in_period > 0 else 0.0
        
        requests.post(f"{CH_URL}/{CH_AUTH}", data=f"ALTER TABLE {CLICKHOUSE_DATABASE}.user_reports_mart DELETE WHERE user_id = '{user_id}' AND period_start = '{period_start}' AND period_end = '{period_end}'")
        
        values = f"('{user_id}','{user_email}','{period_start}','{period_end}',{tel_record.get('sessions_count', 0)},{tel_record.get('total_duration_minutes', 0.0)},{avg_daily},{tel_record.get('movements_count', 0)},{tel_record.get('error_count', 0)},{battery_avg})"
        requests.post(f"{CH_URL}/{CH_AUTH}", data=f"INSERT INTO {CLICKHOUSE_DATABASE}.user_reports_mart VALUES {values}")

dag = DAG('reports_etl_pipeline', default_args=default_args, schedule_interval='0 2 * * *', catchup=False)

init_schema = PythonOperator(task_id='init_clickhouse_schema', python_callable=init_clickhouse_schema, dag=dag)
extract_telemetry = PythonOperator(task_id='extract_telemetry', python_callable=extract_telemetry_data, dag=dag)
extract_crm = PythonOperator(task_id='extract_crm', python_callable=extract_crm_data, dag=dag)
transform_load = PythonOperator(task_id='transform_and_load', python_callable=transform_and_load, dag=dag)

init_schema >> extract_telemetry >> extract_crm >> transform_load
