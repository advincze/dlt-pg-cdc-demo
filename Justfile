# dlt CDC demo — top-level task runner

# Auto-detect podman or docker; override with: just compose="docker compose" demo
compose := `command -v podman > /dev/null 2>&1 && echo "podman compose" || echo "docker compose"`

# Start the full demo in a tmux session (3 panes on one screen: pipeline | producer | postgres logs)
demo: clean up
    tmux new-session  -d -s cdc 'uv run pipeline.py; echo "[done] press enter"; read'
    tmux split-window -t cdc -h 'sleep 3 && uv run producer.py; echo "[done] press enter"; read'
    tmux split-window -t cdc -v '{{compose}} logs -f'
    tmux select-pane  -t cdc:0.0
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
