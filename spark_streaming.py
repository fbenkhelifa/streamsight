# spark_streaming.py
# STREAMSIGHT — Real-Time Crypto Market Anomaly Detection
# Spark Structured Streaming job: Kafka -> Windowed VWAP + Z-Score -> Elasticsearch + Console
#
# Run with:
#   C:\spark\spark-3.5.7-bin-hadoop3\bin\spark-submit ^
#     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.elasticsearch:elasticsearch-spark-30_2.12:8.11.4 ^
#     spark_streaming.py

import os
import signal
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, sum as spark_sum, avg, stddev, lit, when, abs as spark_abs,
    concat_ws, date_format
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType, TimestampType
)

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "crypto_trades"
ES_HOST = "localhost"
ES_PORT = "9200"
ES_INDEX = "streamsight-trades"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")

WINDOW_DURATION = "10 seconds"
WATERMARK_DELAY = "5 seconds"
ZSCORE_THRESHOLD = 2.0

spark = (
    SparkSession.builder
    .appName("STREAMSIGHT-Kafka-Spark-Streaming")
    .master("local[*]")
    .config("spark.es.nodes", ES_HOST)
    .config("spark.es.port", ES_PORT)
    .config("spark.es.index.auto.create", "true")
    .config("spark.es.nodes.wan.only", "true")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

streaming_query = None

def signal_handler(sig, frame):
    print("\n[STREAMSIGHT] Received shutdown signal. Stopping streaming query...")
    if streaming_query is not None:
        streaming_query.stop()
    spark.stop()
    print("[STREAMSIGHT] Shutdown complete.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BROKER)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

raw_df = kafka_df.selectExpr("CAST(value AS STRING) AS json_str")

trade_schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("quantity", DoubleType(), True),
    StructField("event_time", LongType(), True)
])

parsed_df = (
    raw_df
    .select(from_json(col("json_str"), trade_schema, {"mode": "PERMISSIVE"}).alias("data"))
    .select("data.*")
    .filter(col("symbol").isNotNull())
)

trades_df = (
    parsed_df
    .withColumn("event_ts", (col("event_time") / 1000).cast(TimestampType()))
    .withColumn("price_qty", col("price") * col("quantity"))
    .drop("event_time")
)

windowed_df = (
    trades_df
    .withWatermark("event_ts", WATERMARK_DELAY)
    .groupBy(window(col("event_ts"), WINDOW_DURATION), col("symbol"))
    .agg(
        spark_sum("price_qty").alias("sum_price_qty"),
        spark_sum("quantity").alias("total_volume"),
        spark_sum(lit(1)).alias("trade_count"),
        avg("price").alias("avg_price"),
        stddev("price").alias("price_stddev"),
    )
)

vwap_df = (
    windowed_df
    .withColumn("vwap", when(col("total_volume") > 0, col("sum_price_qty") / col("total_volume")).otherwise(lit(0.0)))
    .withColumn("window_start", col("window.start"))
    .withColumn("window_end", col("window.end"))
    .drop("window", "sum_price_qty")
)

anomaly_df = (
    vwap_df
    .withColumn(
        "zscore",
        when((col("price_stddev").isNotNull()) & (col("price_stddev") > 0), (col("vwap") - col("avg_price")) / col("price_stddev")).otherwise(lit(0.0))
    )
    .withColumn("is_anomaly", when(spark_abs(col("zscore")) > ZSCORE_THRESHOLD, lit(True)).otherwise(lit(False)))
    .withColumn(
        "anomaly_type",
        when(col("zscore") > ZSCORE_THRESHOLD, lit("HIGH_VWAP"))
        .when(col("zscore") < -ZSCORE_THRESHOLD, lit("LOW_VWAP"))
        .otherwise(lit("NORMAL"))
    )
)

output_df = (
    anomaly_df
    .select(
        col("symbol"),
        col("window_start"),
        col("window_end"),
        col("total_volume"),
        col("trade_count"),
        col("avg_price"),
        col("vwap"),
        col("price_stddev"),
        col("zscore"),
        col("is_anomaly"),
        col("anomaly_type"),
        concat_ws("_", col("symbol"), date_format(col("window_start"), "yyyyMMddHHmmss")).alias("doc_id")
    )
)

console_query = (
    output_df
    .writeStream
    .outputMode("append")
    .format("console")
    .option("truncate", "false")
    .option("checkpointLocation", os.path.join(CHECKPOINT_DIR, "console"))
    .trigger(processingTime="10 seconds")
    .start()
)

def write_to_elasticsearch(batch_df, batch_id):
    batch_count = batch_df.count()
    if batch_count == 0:
        return

    try:
        (
            batch_df
            .write
            .format("org.elasticsearch.spark.sql")
            .option("es.resource", ES_INDEX)
            .option("es.mapping.id", "doc_id")
            .option("es.write.operation", "upsert")
            .option("es.nodes", ES_HOST)
            .option("es.port", ES_PORT)
            .option("es.nodes.wan.only", "true")
            .mode("append")
            .save()
        )
        print(f"[STREAMSIGHT] Batch {batch_id}: Wrote {batch_count} records to Elasticsearch")
    except Exception as e:
        print(f"[STREAMSIGHT] Batch {batch_id}: ES write failed - {e}")

es_query = (
    output_df
    .writeStream
    .outputMode("append")
    .foreachBatch(write_to_elasticsearch)
    .option("checkpointLocation", os.path.join(CHECKPOINT_DIR, "elasticsearch"))
    .trigger(processingTime="10 seconds")
    .start()
)

print("[STREAMSIGHT] Streaming started. Press Ctrl+C to stop.")
print(f"[STREAMSIGHT] Checkpoints: {CHECKPOINT_DIR}")
print(f"[STREAMSIGHT] Elasticsearch: http://{ES_HOST}:{ES_PORT}/{ES_INDEX}")
print(f"[STREAMSIGHT] Anomaly threshold: |Z| > {ZSCORE_THRESHOLD}")

streaming_query = console_query

try:
    spark.streams.awaitAnyTermination()
except KeyboardInterrupt:
    print("\n[STREAMSIGHT] Interrupted. Shutting down...")
finally:
    for q in spark.streams.active:
        q.stop()
    spark.stop()
    print("[STREAMSIGHT] All streams stopped.")
