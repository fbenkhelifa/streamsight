# STREAMSIGHT — Presentation Guide

## Suggested flow (15–20 min)

1. Problem statement: real-time crypto anomaly detection
2. Architecture walkthrough: Binance → Kafka → Spark → ES → Kibana
3. Live demo:
   - producer output
   - Spark windowed output
   - ES count growth
   - Kibana dashboard
4. Math:
   - VWAP: $\sum(p\times q)/\sum(q)$
   - Z-score: $(VWAP-\mu)/\sigma$
5. Trade-offs and limitations

## Common jury questions

- Why Kafka vs Redis Pub/Sub? (durability/replay)
- Why Spark vs Flink? (PySpark maturity + ecosystem)
- How is exactly-once approached? (checkpoint + idempotent upsert)
