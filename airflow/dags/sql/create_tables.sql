-- Создание таблиц для витрины отчётности

-- Удаляем таблицы в правильном порядке (сначала дочерние, потом родительские)
DROP TABLE IF EXISTS reports_data_mart;
DROP TABLE IF EXISTS telemetry_data;
DROP TABLE IF EXISTS crm_customers;

-- Таблица клиентов из CRM
CREATE TABLE crm_customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    registration_date DATE,
    prosthesis_type VARCHAR(50),
    status VARCHAR(50)
);

-- Таблица телеметрии
CREATE TABLE telemetry_data (
    telemetry_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    device_id VARCHAR(50),
    sensor_type VARCHAR(50),
    value DECIMAL(10,3),
    unit VARCHAR(20),
    activity_type VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES crm_customers(customer_id)
);

-- Витрина отчётности - агрегированные данные по клиентам
CREATE TABLE reports_data_mart (
    report_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    prosthesis_type VARCHAR(50),
    report_date DATE,
    total_sessions INTEGER,
    avg_muscle_signal DECIMAL(10,3),
    max_muscle_signal DECIMAL(10,3),
    min_muscle_signal DECIMAL(10,3),
    avg_position DECIMAL(10,3),
    total_activities INTEGER,
    most_common_activity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES crm_customers(customer_id)
);
