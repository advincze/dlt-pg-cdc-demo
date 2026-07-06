#!/usr/bin/env python3
"""Continuously inserts orders into Postgres, then evolves the schema after 30s."""
import random
import time

import psycopg2

DSN = "postgresql://demo:demo@localhost:5432/demo"

NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi"]
TIERS = ["bronze", "silver", "gold", "platinum"]


def _exec(cur, sql, params=None) -> None:
    print(f"[sql] {cur.mogrify(sql, params).decode()}")
    cur.execute(sql, params)


def main():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()

    print("[producer] Phase 1: inserting rows for 30 seconds...")
    start = time.time()
    count = 0
    while time.time() - start < 30:
        _exec(
            cur,
            "INSERT INTO orders (customer_name, amount) VALUES (%s, %s)",
            (random.choice(NAMES), round(random.uniform(10, 500), 2)),
        )
        count += 1
        if count % 10 == 0:
            print(f"[producer]   {count} rows inserted")
        time.sleep(0.5)

    print(f"[producer] Phase 1 complete: {count} rows inserted")
    _exec(cur, "ALTER TABLE orders ADD COLUMN loyalty_tier VARCHAR(20)")
    print("[producer] Schema altered. Continuing inserts with loyalty_tier populated...")

    count2 = 0
    while True:
        _exec(
            cur,
            "INSERT INTO orders (customer_name, amount, loyalty_tier) VALUES (%s, %s, %s)",
            (random.choice(NAMES), round(random.uniform(10, 500), 2), random.choice(TIERS)),
        )
        count2 += 1
        if count2 % 10 == 0:
            print(f"[producer]   {count + count2} rows total ({count2} post-schema-change)")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
