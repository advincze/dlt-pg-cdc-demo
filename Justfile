# dlt CDC demo — top-level task runner

# Start the full demo in a tmux session (3 windows: pipeline / producer / postgres logs)
demo: clean up
    tmux new-session  -d -s cdc -n pipeline 'uv run pipeline.py; echo "[done] press enter"; read'
    tmux new-window   -t cdc: -n producer  'sleep 3 && uv run producer.py; echo "[done] press enter"; read'
    tmux new-window   -t cdc: -n logs      'docker compose logs -f'
    tmux select-window -t cdc:pipeline
    tmux attach-session -t cdc

# Start Postgres and wait until healthy
up:
    docker compose up -d --wait

# Run only the CDC pipeline
pipeline:
    uv run pipeline.py

# Run only the data producer
producer:
    uv run producer.py

# Tail Postgres logs (shows all SQL via log_statement=all)
logs:
    docker compose logs -f

# Stop the tmux session and Postgres
stop:
    -tmux kill-session -t cdc 2>/dev/null
    docker compose down

# Remove containers + volumes, DuckDB file, and dlt pipeline state
clean: stop
    rm -f pg_cdc.duckdb pg_cdc.duckdb.wal
    rm -rf .dlt/pipelines
