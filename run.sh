#!/bin/bash
# run.sh - Run the job search workflow
#
# Usage:
#   ./run.sh           # Run once
#   ./run.sh --quiet   # Run without console output (for scheduled tasks)
#
# Schedule with Windows Task Scheduler:
#   Action: C:\Program Files\Git\bin\bash.exe
#   Arguments: /c/Users/Nat/Documents/dev/ai-agents/run.sh --quiet

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Logging
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="logs/job_search_${TIMESTAMP}.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check for quiet mode
QUIET=false
if [[ "$1" == "--quiet" ]]; then
    QUIET=true
    exec >> "$LOG_FILE" 2>&1
fi

log "Starting job search workflow..."

# Start Langfuse (optional - for tracing)
LANGFUSE_DIR="../langfuse"
if [[ -f "$LANGFUSE_DIR/docker-compose.yml" ]]; then
    log "Starting Langfuse services..."
    docker compose -f "$LANGFUSE_DIR/docker-compose.yml" up -d 2>/dev/null || true
fi

# Start Ollama (--remove-orphans cleans up old containers like langraph-store)
log "Starting Ollama..."
docker compose up -d --remove-orphans

# Wait for Ollama to be ready
log "Waiting for Ollama to be ready..."
MAX_WAIT=120
WAITED=0
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [[ $WAITED -ge $MAX_WAIT ]]; then
        log "ERROR: Ollama did not start within ${MAX_WAIT}s"
        exit 1
    fi
done
log "Ollama is ready"

# Wait for SearXNG to be ready
log "Waiting for SearXNG to be ready..."
WAITED=0
until curl -s "http://localhost:8080/search?q=test&format=json" > /dev/null 2>&1; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [[ $WAITED -ge $MAX_WAIT ]]; then
        log "ERROR: SearXNG did not start within ${MAX_WAIT}s"
        exit 1
    fi
done
log "SearXNG is ready"

# Activate venv and run workflow
log "Running job search..."
source .venv/Scripts/activate
python scripts/run_job_search.py 2>&1 | tee -a "$LOG_FILE"

log "Job search complete. Log saved to $LOG_FILE"
