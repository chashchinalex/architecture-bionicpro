CREATE DATABASE IF NOT EXISTS olap;

CREATE TABLE IF NOT EXISTS default.crm_cdc_kafka
(
    value String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list   = 'kafka:9092',
    kafka_topic_list    = 'crm.sample.crm',
    kafka_group_name    = 'clickhouse_cdc',
    kafka_format        = 'JSONAsString',
    kafka_row_delimiter = '\n',
    kafka_num_consumers = 1;

CREATE TABLE IF NOT EXISTS olap.crm_olap
(
    id         Int32,
    name       String,
    email      String,
    age        Nullable(Int32),
    gender     Nullable(String),
    country    Nullable(String),
    address    Nullable(String),
    phone      Nullable(String),
    ts         DateTime64(3),
    is_deleted UInt8 DEFAULT 0
)
ENGINE = ReplacingMergeTree(ts)
PARTITION BY toYYYYMM(ts)
ORDER BY (id);

CREATE MATERIALIZED VIEW IF NOT EXISTS olap.mv_crm
TO olap.crm_olap
AS
SELECT
    toInt32(JSONExtractInt(payload, 'id'))                         AS id,
    JSONExtractString(payload, 'name')                             AS name,
    JSONExtractString(payload, 'email')                            AS email,
    JSONExtractInt(payload, 'age')                                 AS age,
    JSONExtractString(payload, 'gender')                           AS gender,
    JSONExtractString(payload, 'country')                          AS country,
    JSONExtractString(payload, 'address')                          AS address,
    JSONExtractString(payload, 'phone')                            AS phone,
    toDateTime64(JSONExtractInt(payload, '__ts_ms') / 1000.0, 3)   AS ts,
    toUInt8(
        JSONExtractString(payload, '__deleted') = 'true'
        OR JSONExtractString(payload, '__op') = 'd'
    )                                                              AS is_deleted
FROM
(
    SELECT
        JSONExtractRaw(value, 'payload') AS payload
    FROM default.crm_cdc_kafka
);
