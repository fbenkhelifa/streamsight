# STREAMSIGHT — Technical Report (Summary)

## Pipeline

Binance WebSocket -> Kafka -> Spark Structured Streaming -> Elasticsearch -> Kibana.

## Metrics

- VWAP: volume-weighted average price
- Z-score anomaly detection with threshold |Z| > 2

## Reliability

- Spark checkpointing
- idempotent writes via deterministic `doc_id`

## Deployment

Docker Compose services: Zookeeper, Kafka, Elasticsearch, Kibana.
