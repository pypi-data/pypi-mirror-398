# Continuous Load Test

Maintains a target pool of streaming threads to exercise long-running HTTP SSE streams.

## Local Usage

```bash
# Install dependencies
uv sync

# Set environment variables
export LANGSMITH_API_KEY=your-langsmith-key
export DD_API_KEY=your-datadog-key

# Run with defaults (1000 threads)
uv run python runner.py

# Or with custom options
# use --raw-sse flag to send without SDK (which would mask retries etc)
uv run python runner.py \
  --base-url https://your-deployment.langgraph.app \
  --assistant-id long_running \
  --num-threads 1000
  --raw-sse
```

## Metrics

Metrics are shipped to Datadog every 60 seconds. Per-run metrics are sent once when each run completes:

- `langsmith_deployment.continuous.threads.active` - Active streaming threads (gauge)
- `langsmith_deployment.continuous.threads.failed` - Failed threads (gauge)
- `langsmith_deployment.continuous.events` - SSE events received per run (count)
- `langsmith_deployment.continuous.failures` - Connection failures per run (count)
- `langsmith_deployment.continuous.threads.faults.dropped_chunks` - Dropped messages per run (count)
- `langsmith_deployment.continuous.threads.faults.out_of_order_runs` - Runs with out-of-order messages (count)
- `langsmith_deployment.continuous.threads.faults.malformed_chunks` - Malformed chunks per run (count)
- `langsmith_deployment.continuous.threads.latency` - End-to-end latency per message in seconds (distribution)
