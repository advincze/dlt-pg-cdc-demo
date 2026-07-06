# dlt CDC demo — top-level task runner

# Auto-detect podman or docker; override with: just compose="docker compose" demo
compose := `command -v podman > /dev/null 2>&1 && echo "podman compose" || echo "docker compose"`

# Start the full demo in a tmux session (3 windows: pipeline / producer / postgres logs)
demo: clean up
    tmux new-session  -d -s cdc -n pipeline 'uv run pipeline.py; echo "[done] press enter"; read'
    tmux new-window   -t cdc: -n producer  'sleep 3 && uv run producer.py; echo "[done] press enter"; read'
    tmux new-window   -t cdc: -n logs      '{{compose}} logs -f'
    tmux select-window -t cdc:pipeline
    tmux attach-session -t cdc

# Start Postgres and wait until healthy
up:
    {{compose}} up -d --wait

# Run only the CDC pipeline
pipeline:
    uv run pipeline.py

# Run only the data producer
producer:
    uv run producer.py

# Tail Postgres logs (shows all SQL via log_statement=all)
logs:
    {{compose}} logs -f

# Stop the tmux session and Postgres
stop:
    -tmux kill-session -t cdc 2>/dev/null
    {{compose}} down

# Remove containers + volumes, DuckDB file, and dlt pipeline state
clean: stop
    rm -f pg_cdc.duckdb pg_cdc.duckdb.wal
    rm -rf .dlt/pipelines
