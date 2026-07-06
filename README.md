# dlt pg_replication CDC Demo

A self-contained demo of Change Data Capture (CDC) using:

- **PostgreSQL** (Docker) as the source with logical replication enabled
- **dlt** `pg_replication` verified source to stream WAL changes
- **DuckDB** as the local destination
- A **producer** that inserts data, then evolves the schema live

The key insight: when the producer runs `ALTER TABLE orders ADD COLUMN loyalty_tier`, the dlt pipeline automatically detects the schema change and evolves the DuckDB table - no pipeline code changes needed.

## Prerequisites

- Docker + Docker Compose
- [uv](https://docs.astral.sh/uv/) (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Setup

```bash
# Install Python dependencies
uv sync

# Start Postgres (creates table + publication via init.sql)
docker compose up -d
```

## Run the demo

Open two terminals:

**Terminal 1 - Start the CDC pipeline:**
```bash
uv run pipeline.py
```

Expected output:
```
[pipeline] Initializing replication slot (idempotent)...
[pipeline] Slot 'demo_slot' ready. Polling every 3s...
[pipeline] Loaded batch: ...
```

**Terminal 2 - Start the producer:**
```bash
uv run producer.py
```

Expected output:
```
[producer] Phase 1: inserting rows for 30 seconds...
[producer]   10 rows inserted
...
[producer] Phase 2: ALTER TABLE orders ADD COLUMN loyalty_tier VARCHAR(20)
[producer] Schema altered. Continuing inserts with loyalty_tier populated...
```

After the schema change, you will see the pipeline pick up the new `loyalty_tier` column automatically.

## Inspect the data

```bash
uv run python -c "
import duckdb
conn = duckdb.connect('pg_cdc.duckdb')
print('Row count:', conn.execute('SELECT COUNT(*) FROM cdc_data.orders').fetchone()[0])
print('Schema:', conn.execute('DESCRIBE cdc_data.orders').fetchall())
print()
print('Sample rows after schema change:')
print(conn.execute('SELECT * FROM cdc_data.orders WHERE loyalty_tier IS NOT NULL LIMIT 5').df())
"
```

## How it works

```
Postgres (WAL)
     |
     | logical replication (pgoutput protocol)
     v
dlt pg_replication source
     |
     | polls every 3 seconds, tracks LSN watermark in dlt state
     v
DuckDB (pg_cdc.duckdb / cdc_data.orders)
```

### Schema evolution flow

When `ALTER TABLE orders ADD COLUMN loyalty_tier` fires:

1. Postgres writes a `Relation` WAL message with the new 5-column schema
2. The dlt source detects the schema change mid-batch and cleanly ends the batch
3. On the next poll cycle, the new `Relation` message is processed first
4. dlt's schema evolution logic adds the `loyalty_tier` column to DuckDB automatically
5. Subsequent inserts land in the new column - no pipeline changes required

## Reset

```bash
# Tear down Postgres (removes all data including replication slot)
docker compose down -v

# Remove DuckDB and dlt pipeline state
rm -f pg_cdc.duckdb pg_cdc.duckdb.wal
rm -rf .dlt/pipelines
```
