# STREAMSIGHT — Restart Runbook (Windows)

## Prerequisites

- Docker Desktop running
- Python venv created (`venv`)
- Spark 3.5.x + Java 17 + Hadoop winutils configured

## Start sequence

1. Start infra:
   - `docker compose up -d`
   - wait ~30–60s, then `docker compose ps`
2. Create/reset ES index:
   - `./create_es_index.ps1`
3. Clear old checkpoints (optional on restart):
   - remove `checkpoints/`
4. Start producer (`binance_to_kafka.py`)
5. Start Spark job (`spark_streaming.py`)

## Verification

- ES count: `http://localhost:9200/streamsight-trades/_count`
- Kibana: `http://localhost:5601`

## Stop sequence

1. Stop Spark (Ctrl+C)
2. Stop producer (Ctrl+C)
3. `docker compose down`
