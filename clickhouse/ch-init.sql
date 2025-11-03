USE analytic;

CREATE TABLE reports
(
    prosthesis_id UInt64,
    username String,
    email String,
    sensor_type String,
    sensor_name String,
    force_newtons_avg Decimal,
    battery_level_percent_avg Decimal,
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY prosthesis_id
PRIMARY KEY prosthesis_id;

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (1, 'prothetic1', 'prothetic1@example.com', 'sensor', 'sensor_1', 1, 1);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (2, 'prothetic1', 'prothetic1@example.com', 'sensor', 'sensor_2', 2, 2);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (3, 'prothetic1', 'prothetic1@example.com', 'sensor', 'sensor_3', 3, 3);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (4, 'prothetic1', 'prothetic1@example.com', 'sensor', 'sensor_4', 4, 4);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (5, 'prothetic2', 'prothetic2@example.com', 'sensor', 'sensor_1', 1, 1);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (6, 'prothetic2', 'prothetic2@example.com', 'sensor', 'sensor_2', 2, 2);

INSERT INTO reports(prosthesis_id, username, email, sensor_type, sensor_name, force_newtons_avg, battery_level_percent_avg)
VALUES (7, 'prothetic3', 'prothetic3@example.com', 'sensor', 'sensor_1', 1, 1);
