---
name: data-engineering
description: Design and build data pipelines, ETL/ELT processes, feature engineering, and data quality validation for ML systems
---

# Data Engineering Skill

## Description

This skill handles all aspects of data engineering for ML systems: designing and implementing data pipelines, building ETL/ELT processes, engineering features, ensuring data quality, and optimizing storage. It covers both batch and streaming pipelines, data validation frameworks, feature stores, and data versioning. Use this skill whenever you need to move data from source systems to ML-ready formats, transform raw data into features, or build production data infrastructure.

Good data engineering is critical for ML success. Poor data quality, pipeline failures, or training-serving skew cause more ML failures than bad models. This skill emphasizes reliability, reproducibility, and data quality.

## When to Use

- When user needs to build data pipelines (batch, streaming, or hybrid)
- When transforming raw data into ML-ready features
- When implementing ETL/ELT processes for data ingestion
- When setting up data quality validation and monitoring
- When designing feature engineering pipelines
- When implementing feature stores for consistent training/serving
- When optimizing data storage (formats, partitioning, compression)
- When versioning datasets for reproducibility
- When orchestrating complex data workflows (Airflow, Dagster, Prefect)
- When debugging data quality issues or pipeline failures

## When to Use

- When user needs to build data pipelines (batch, streaming, or hybrid)
- When transforming raw data into ML-ready features
- When implementing ETL/ELT processes for data ingestion
- When setting up data quality validation and monitoring
- When designing feature engineering pipelines
- When implementing feature stores for consistent training/serving
- When optimizing data storage (formats, partitioning, compression)
- When versioning datasets for reproducibility
- When orchestrating complex data workflows (Airflow, Dagster, Prefect)
- When debugging data quality issues or pipeline failures

## How to Use

### Step 1: Understand Data Requirements

**Gather requirements from problem-framing:**
- What data sources are available? (databases, APIs, files, streams)
- What features do we need? (raw vs derived, aggregations, joins)
- What volume and velocity? (GB vs TB, batch vs real-time)
- What quality standards? (completeness, accuracy, freshness)
- What latency requirements? (training: hours/days OK, serving: milliseconds)

**Map out data flow: Source → Ingestion → Transform → Storage → Consumption**

### Step 2: Design the Pipeline Architecture

**Choose appropriate pipeline pattern:**
- **Batch processing:** Scheduled jobs for historical data, model training (Airflow, cron)
- **Stream processing:** Real-time events, online features, live predictions (Kafka, Flink)
- **Lambda architecture:** Batch for accuracy + stream for speed
- **Kappa architecture:** Stream-only with reprocessing capability

**Select tools based on scale and complexity:**
- Small data (<1GB): Python scripts, pandas, local files
- Medium data (1-100GB): Spark, Dask, cloud data warehouses
- Large data (>100GB): Distributed systems (Spark, Flink), data lakes
- Real-time: Kafka, Kinesis, Pub/Sub for streaming

**Use ml-docs skill to fetch documentation for Airflow, Spark, pandas when implementing.**

### Step 3: Implement ETL/ELT Pipeline

**Build robust data ingestion:**
- **Extract:** Connect to sources (APIs, databases, files), handle authentication, implement incremental loading
- **Transform:** Clean data (deduplication, null handling), enrich (joins, lookups), aggregate (groupby, window functions), engineer features
- **Load:** Write to storage (database, data lake, feature store), handle upserts and partitioning
- **Error handling:** Dead letter queues for bad records, retry logic with exponential backoff, alerting on failures

**Key principles:**
- Idempotency: rerunning should give same result
- Incremental processing: process only new/changed data
- Checkpointing: save progress to resume on failure

### Step 4: Implement Data Quality Validation

**Validate data at every stage:**
- **Schema validation:** Column types, nullable constraints, value ranges
- **Statistical validation:** Distribution checks (mean, std within expected range), outlier detection, null rate thresholds
- **Business logic:** Referential integrity, sum constraints, temporal consistency
- **Data freshness:** Alert if data is stale beyond threshold

**Use validation frameworks:**
- Great Expectations: comprehensive data quality testing
- Pandera: schema validation for pandas DataFrames
- Custom validators: implement specific business rules

**Fail fast:** Stop pipeline if critical validation fails. Log and alert for non-critical issues.

### Step 5: Optimize Storage and Performance

**Choose efficient data formats:**
- **Parquet:** Columnar, compressed, fast for analytics (recommended for ML)
- **CSV/JSON:** Human-readable but inefficient
- **Avro:** Row-based, good for streaming with schema evolution
- **Feather/Arrow:** Fast in-memory interchange

**Optimize query performance:**
- **Partition data:** By date, category, or hash for query pruning
- **Compress:** gzip, snappy, or zstd (5-10x size reduction)
- **Index appropriately:** For frequent lookups
- **Materialize views:** Precompute expensive aggregations

**Monitor pipeline performance:** Track execution time, data volume, error rates.

## Best Practices

- **Idempotency is critical:** Same input should always produce same output. Use deterministic operations
- **Validate early and often:** Catch data quality issues before they corrupt downstream models
- **Version datasets:** Use DVC or similar to track data versions linked to model versions
- **Document data lineage:** Track where data comes from and how it's transformed
- **Test pipelines:** Unit test transformations, integration test end-to-end flows
- **Monitor continuously:** Data quality dashboards, alerting on anomalies
- **Incremental processing:** Don't reprocess everything; process only new/changed data
- **Handle schema evolution:** Design for changing schemas (new columns, type changes)
- **Security first:** Encrypt at rest and in transit, handle PII appropriately, implement access controls

## Examples

### Example 1: Batch Feature Engineering Pipeline

**User Request:** "Build a daily pipeline to create features from user activity logs for a churn prediction model. We have 1M users and 10GB of daily logs."

**Approach:**
1. **Understand requirements:** Daily batch job, transform logs into user-level features (activity counts, engagement metrics), store in feature store
2. **Design architecture:** Airflow DAG with tasks: Extract logs from S3 → Transform with Spark → Validate → Load to feature store
3. **Implement pipeline:**
   - Extract: Read Parquet files from S3 for yesterday's date
   - Transform: Aggregate per user (login count, session duration, actions), join with user metadata, create time-windowed features (7-day, 30-day rolling)
   - Validate: Check null rates, distribution shifts, expected row counts
   - Load: Write to feature store partitioned by date
4. **Optimize:** Partition by date, compress with snappy, cache intermediate results
5. **Monitor:** Track pipeline runtime, data quality metrics, alert on failures

**Key code pattern:**
```python
# Airflow DAG structure
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('feature_pipeline', schedule='@daily')

extract_task = PythonOperator(task_id='extract', python_callable=extract_logs)
transform_task = PythonOperator(task_id='transform', python_callable=transform_features)
validate_task = PythonOperator(task_id='validate', python_callable=validate_data)
load_task = PythonOperator(task_id='load', python_callable=load_to_feature_store)

extract_task >> transform_task >> validate_task >> load_task

# Use pandas for medium data, Spark for large data
# Store as Parquet with date partitioning
```

### Example 2: Real-Time Feature Pipeline

**User Request:** "We need real-time features for fraud detection. When a transaction happens, we need to compute features like 'transactions in last hour' within 100ms."

**Approach:**
1. **Understand requirements:** Streaming pipeline, sub-second latency, aggregate features over time windows
2. **Design architecture:** Kafka for event stream → Flink for stateful processing → Redis for online feature storage
3. **Implement pipeline:**
   - Ingest: Transaction events from Kafka topic
   - Process: Maintain sliding windows (1 hour, 24 hour), compute aggregates (count, sum, avg)
   - Store: Write to Redis with TTL for fast lookup
   - Serve: API reads from Redis at inference time
4. **Handle challenges:**
   - Late arrivals: Use watermarks and allowed lateness
   - State management: Checkpoint state to recover from failures
   - Scalability: Partition by user_id for parallel processing
5. **Monitor:** Track processing lag, throughput, Redis hit rate

**Key considerations:**
- Streaming frameworks: Kafka + Flink, Kinesis + Flink, Pub/Sub + Dataflow
- State storage: Redis for millisecond lookups, DynamoDB for persistence
- Consistency: Handle duplicates (dedupe), out-of-order events (windowing)

### Example 3: Data Quality Validation

**User Request:** "Our model performance dropped suddenly. Help me add data quality checks to catch issues early."

**Approach:**
1. **Identify failure modes:** Schema changes, null values spike, distribution shift, data freshness issues
2. **Implement validation framework:** Use Great Expectations to define data quality tests
3. **Create validation suite:**
   - Schema tests: Column types, nullable constraints, value ranges
   - Statistical tests: Mean/std within expected range, null rate <5%, no duplicates
   - Business logic: Transaction amount >0, start_date < end_date
   - Freshness: Data updated within last 2 hours
4. **Integrate into pipeline:** Run validations after each transformation step
5. **Setup alerting:** Slack/email on validation failures, dashboard for trends
6. **Root cause analysis:** When failures occur, use validation results to pinpoint exact issue

**Key code pattern:**
```python
import great_expectations as gx

# Define expectations
context = gx.get_context()
suite = context.create_expectation_suite("data_quality_suite")

# Add expectations
suite.expect_column_values_to_not_be_null("user_id")
suite.expect_column_values_to_be_between("age", min_value=0, max_value=120)
suite.expect_column_mean_to_be_between("transaction_amount", min_value=10, max_value=100)

# Validate data
results = context.run_checkpoint(checkpoint_name="daily_checkpoint")

if not results["success"]:
    alert_team(results)  # Send Slack alert with details
    raise ValueError("Data quality validation failed")
```

## Notes

- **Training vs serving pipelines:** Ensure consistency between how features are computed for training vs inference. Feature stores help solve this (Feast, Tecton)
- **Point-in-time correctness:** For temporal features, ensure you don't leak future information into past predictions during training
- **Data versioning is crucial:** Link model versions to exact data versions for reproducibility
- **Handle PII carefully:** Anonymize, encrypt, or exclude sensitive data. Comply with GDPR/CCPA
- **Backfilling:** When adding new features, need to recompute historical data. Design for efficient backfills
- **Testing:** Unit test transformations with small datasets, integration test full pipeline with realistic data
- **Performance optimization:** Profile pipelines to find bottlenecks (data loading, shuffles, expensive transformations)
- **Cost awareness:** Cloud data processing costs add up. Use partitioning, compression, and incremental processing to minimize costs (see infra-cost skill)
- **Use ml-docs skill:** Fetch documentation for pandas, Spark, Airflow, Great Expectations when implementing specific features
- **Integration with other skills:** Data engineering feeds clean, validated data to classical-ml, deep-learning, and llm-agent skills. Coordinates with mlops-production for serving pipelines