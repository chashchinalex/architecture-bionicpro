curl -X POST http://localhost:8083/connectors \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "crm-postgres-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",

      "database.hostname": "postgres",
      "database.port": "5432",
      "database.user": "airflow",
      "database.password": "airflow",
      "database.dbname": "sample",

      "topic.prefix": "crm",

      "schema.include.list": "sample",
      "table.include.list": "sample.crm",

      "plugin.name": "pgoutput",
      "publication.autocreate.mode": "filtered",

      "slot.name": "crm_slot",

      "tombstones.on.delete": "false",

      "transforms": "unwrap",
      "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
      "transforms.unwrap.drop.tombstones": "true",
      "transforms.unwrap.delete.handling.mode": "rewrite",
      "transforms.unwrap.add.fields": "op,ts_ms"
    }
  }'
