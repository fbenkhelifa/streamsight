# STREAMSIGHT — Project Explanation

STREAMSIGHT is a real-time analytics pipeline that ingests BTC/USDT trade data from Binance and computes anomaly indicators using Spark Structured Streaming.

## Core responsibilities

- `binance_to_kafka.py`: collect and publish trades to Kafka
- `spark_streaming.py`: parse stream, apply windows/watermark, compute VWAP + Z-score, write to Elasticsearch
- `setup_kibana.py`: create dashboard/data view assets

## Output

Per time window, the system stores:

- symbol
- window boundaries
- total volume + trade count
- average price + VWAP
- zscore + anomaly flags
