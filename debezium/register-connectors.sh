#!/bin/sh

sleep 10
curl -s -X DELETE http://debezium:8083/connectors/crm-connector || true
curl -s -X POST http://debezium:8083/connectors \
  -H 'Content-Type: application/json' \
  --data @/debezium/crm-connector.json || true
