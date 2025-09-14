from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import os

# Аргументы по умолчанию
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 12, 1),
    'retries': 0,  # Отключаем retry для упрощения
    'retry_delay': timedelta(minutes=5),
}

# Функция для загрузки данных из CSV в PostgreSQL
def load_crm_data():
    """Загружает данные клиентов из CRM в базу данных"""
    CSV_FILE_PATH = '/opt/airflow/data/crm_customers.csv'
    
    # Читаем CSV файл
    df = pd.read_csv(CSV_FILE_PATH)
    
    # Подключаемся к базе данных
    postgres_hook = PostgresHook(postgres_conn_id='reports_postgres')
    
    # Очищаем таблицу перед загрузкой
    postgres_hook.run("DELETE FROM crm_customers")
    
    # Загружаем данные
    for index, row in df.iterrows():
        insert_query = f"""
        INSERT INTO crm_customers (customer_id, name, email, phone, registration_date, prosthesis_type, status)
        VALUES ({row['customer_id']}, '{row['name']}', '{row['email']}', '{row['phone']}', 
                '{row['registration_date']}', '{row['prosthesis_type']}', '{row['status']}')
        """
        postgres_hook.run(insert_query)
    
    print(f"Загружено {len(df)} записей клиентов из CRM")

def load_telemetry_data():
    """Загружает данные телеметрии в базу данных"""
    CSV_FILE_PATH = '/opt/airflow/data/telemetry_data.csv'
    
    # Читаем CSV файл
    df = pd.read_csv(CSV_FILE_PATH)
    
    # Подключаемся к базе данных
    postgres_hook = PostgresHook(postgres_conn_id='reports_postgres')
    
    # Очищаем таблицу перед загрузкой
    postgres_hook.run("DELETE FROM telemetry_data")
    
    # Загружаем данные
    for index, row in df.iterrows():
        insert_query = f"""
        INSERT INTO telemetry_data (customer_id, timestamp, device_id, sensor_type, value, unit, activity_type)
        VALUES ({row['customer_id']}, '{row['timestamp']}', '{row['device_id']}', 
                '{row['sensor_type']}', {row['value']}, '{row['unit']}', '{row['activity_type']}')
        """
        postgres_hook.run(insert_query)
    
    print(f"Загружено {len(df)} записей телеметрии")

def create_reports_mart():
    """Создает витрину данных для отчётов"""
    postgres_hook = PostgresHook(postgres_conn_id='reports_postgres')
    
    # Очищаем витрину
    postgres_hook.run("DELETE FROM reports_data_mart")
    
    # Создаем агрегированные данные
    mart_query = """
    INSERT INTO reports_data_mart (
        customer_id, customer_name, customer_email, prosthesis_type, report_date,
        total_sessions, avg_muscle_signal, max_muscle_signal, min_muscle_signal,
        avg_position, total_activities, most_common_activity
    )
    SELECT 
        c.customer_id,
        c.name as customer_name,
        c.email as customer_email,
        c.prosthesis_type,
        CURRENT_DATE as report_date,
        COUNT(DISTINCT DATE(t.timestamp)) as total_sessions,
        AVG(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as avg_muscle_signal,
        MAX(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as max_muscle_signal,
        MIN(CASE WHEN t.sensor_type = 'muscle_signal' THEN t.value END) as min_muscle_signal,
        AVG(CASE WHEN t.sensor_type = 'position' THEN t.value END) as avg_position,
        COUNT(t.telemetry_id) as total_activities,
        (SELECT activity_type FROM telemetry_data t2 
         WHERE t2.customer_id = c.customer_id 
         GROUP BY activity_type 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as most_common_activity
    FROM crm_customers c
    LEFT JOIN telemetry_data t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.name, c.email, c.prosthesis_type
    """
    
    postgres_hook.run(mart_query)
    print("Витрина отчётности обновлена")

# Определяем DAG
with DAG('reports_etl_dag',
         default_args=default_args,
         schedule_interval='0 2 * * *',  # Запуск каждый день в 2:00
         catchup=False,
         max_active_runs=1,  # Ограничиваем количество одновременных запусков
         description='ETL процесс для загрузки данных в витрину отчётности') as dag:

    # Создание таблиц
    create_tables = PostgresOperator(
        task_id='create_tables',
        postgres_conn_id='reports_postgres',
        sql='sql/create_tables.sql'
    )

    # Загрузка данных CRM
    load_crm = PythonOperator(
        task_id='load_crm_data',
        python_callable=load_crm_data
    )

    # Загрузка данных телеметрии
    load_telemetry = PythonOperator(
        task_id='load_telemetry_data',
        python_callable=load_telemetry_data
    )

    # Создание витрины данных
    create_mart = PythonOperator(
        task_id='create_reports_mart',
        python_callable=create_reports_mart
    )

    # Определяем зависимости - последовательное выполнение
    create_tables >> load_crm >> load_telemetry >> create_mart
