CREATE DATABASE sample;
GRANT ALL PRIVILEGES ON DATABASE sample TO airflow;
\connect sample;

CREATE SCHEMA IF NOT EXISTS sample AUTHORIZATION airflow;


CREATE TABLE sample.crm (
    id      int4  NULL,
    "name"  text  NULL,
    email   text  NULL,
    age     int4  NULL,
    gender  text  NULL,
    country text  NULL,
    address text  NULL,
    phone   text  NULL
);