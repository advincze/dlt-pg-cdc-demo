#!/usr/bin/env python3
"""Polls Postgres WAL via dlt pg_replication and loads changes into DuckDB."""
import time
from datetime import datetime, timezone

import dlt
import psycopg2

from pg_replication import replication_resource
from pg_replication.helpers import init_replication

SLOT_NAME = "demo_slot"
PUB_NAME = "my_pub"
SCHEMA_NAME = "public"
TABLE_NAMES = ["orders"]
POLL_INTERVAL = 3


def _print_status(pipeline: dlt.Pipeline, load_info) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

    # Row counts from the normalize step (per-table, this batch only).
    normalize_info = pipeline.last_trace.last_normalize_info
    row_counts = normalize_info.row_counts if normalize_info else {}
    user_rows = {t: n for t, n in row_counts.items() if not t.startswith("_dlt")}

    # Schema changes from the load packages.
    schema_changes: dict[str, list[str]] = {}
    for pkg in load_info.load_packages:
        for table_name, table_schema in pkg.schema_update.items():
            if table_name.startswith("_dlt"):
                continue
            cols = list(table_schema.get("columns", {}).keys())
            if cols:
                schema_changes[table_name] = cols

    lines = [f"[pipeline] {ts}"]
    for table, count in sorted(user_rows.items()):
        lines.append(f"  rows    {table}: +{count}")
    for table, cols in sorted(schema_changes.items()):
        lines.append(f"  schema  {table}: added {', '.join(cols)}")

    print("\n".join(lines))


def main():
    pipeline = dlt.pipeline(
        pipeline_name="pg_cdc",
        destination="duckdb",
        dataset_name="cdc_data",
    )

    dsn = str(dlt.secrets["sources.pg_replication.credentials"])
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_replication_slots WHERE slot_name = %s", (SLOT_NAME,)
        )
        slot_existed = cur.fetchone() is not None

    init_replication(
        slot_name=SLOT_NAME,
        pub_name=PUB_NAME,
        schema_name=SCHEMA_NAME,
        table_names=TABLE_NAMES,
        reset=False,
        persist_snapshots=False,
    )

    if slot_existed:
        print(f"[pipeline] Reusing existing slot '{SLOT_NAME}'. Polling every {POLL_INTERVAL}s...")
    else:
        print(f"[pipeline] Created slot '{SLOT_NAME}'. Polling every {POLL_INTERVAL}s...")

    while True:
        # Instantiate fresh each iteration - the resource is a one-shot generator.
        resource = replication_resource(slot_name=SLOT_NAME, pub_name=PUB_NAME)
        load_info = pipeline.run(resource)
        if load_info.loads_ids:
            _print_status(pipeline, load_info)
        else:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"[pipeline] {ts}  no changes")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
