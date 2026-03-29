#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MODE="local"
PI_HOST=""
PI_PATH="~/finance-tracker"
IMAGE=""
COMPOSE_FILE="docker-compose.pi.yml"
COMPOSE_CMD=""

usage() {
  cat <<'EOF'
Usage:
  scripts/deploy_pi_tailscale.sh [options]

Options:
  --mode <local|remote>     local: deploy on current machine (default)
                            remote: rsync code to Raspberry Pi then deploy there
  --pi-host <user@host>     Required for remote mode
  --pi-path <path>          Remote path (default: /opt/finance-tracker)
  --image <registry/image:tag>
                            Optional prebuilt image to pull/run
  --compose-file <path>     Compose file path relative to project root
  -h, --help                Show this help

Examples:
  # Run directly on Pi with prebuilt image
  scripts/deploy_pi_tailscale.sh --mode local --image ghcr.io/OWNER/finance-tracker:latest

  # Deploy from laptop to Pi without copying .env or data/
  scripts/deploy_pi_tailscale.sh --mode remote --pi-host pi@192.168.1.50 --image ghcr.io/OWNER/finance-tracker:latest
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found." >&2
    exit 1
  fi
}

detect_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    return
  fi
  echo "Error: neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --pi-host)
      PI_HOST="${2:-}"
      shift 2
      ;;
    --pi-path)
      PI_PATH="${2:-}"
      shift 2
      ;;
    --image)
      IMAGE="${2:-}"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$MODE" != "local" && "$MODE" != "remote" ]]; then
  echo "Error: --mode must be 'local' or 'remote'." >&2
  exit 1
fi

if [[ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
  echo "Error: compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ "$MODE" == "local" ]]; then
  require_cmd docker
  detect_compose_cmd
  cd "$PROJECT_ROOT"

  if [[ -n "$IMAGE" ]]; then
    export FINANCE_TRACKER_IMAGE="$IMAGE"
    $COMPOSE_CMD -f "$COMPOSE_FILE" pull
  fi

  mkdir -p data
  $COMPOSE_CMD -f "$COMPOSE_FILE" up -d

  echo "Deployment finished on local machine."
  echo "Next: configure Tailscale Serve/Funnel to publish http://127.0.0.1:8000"
  exit 0
fi

# Remote mode
if [[ -z "$PI_HOST" ]]; then
  echo "Error: --pi-host is required for remote mode." >&2
  exit 1
fi

require_cmd rsync
require_cmd ssh

RSYNC_EXCLUDES=(
  --exclude '.git/'
  --exclude '.venv/'
  --exclude '__pycache__/'
  --exclude '*.pyc'
  --exclude 'frontend/node_modules/'
  --exclude 'frontend/dist/'
  --exclude '.env'
  --exclude '.env.*'
  --exclude 'data/'
)

cd "$PROJECT_ROOT"

# Sync source code only. Sensitive local files are intentionally excluded.
ssh "$PI_HOST" "mkdir -p '$PI_PATH'"
rsync -az --delete "${RSYNC_EXCLUDES[@]}" ./ "$PI_HOST:$PI_PATH/"

REMOTE_CMD="cd '$PI_PATH' && mkdir -p data"
if [[ -n "$IMAGE" ]]; then
  REMOTE_CMD+=" && export FINANCE_TRACKER_IMAGE='$IMAGE'"
fi
REMOTE_CMD+=" && if docker compose version >/dev/null 2>&1; then COMPOSE_CMD='docker compose'; elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD='docker-compose'; else echo 'Error: neither docker compose nor docker-compose found on Pi.' >&2; exit 1; fi"
if [[ -n "$IMAGE" ]]; then
  REMOTE_CMD+=" && \$COMPOSE_CMD -f '$COMPOSE_FILE' pull"
fi
REMOTE_CMD+=" && \$COMPOSE_CMD -f '$COMPOSE_FILE' up -d"

ssh "$PI_HOST" "$REMOTE_CMD"

echo "Deployment finished on $PI_HOST:$PI_PATH."
echo "Sensitive files were not copied: .env and data/."
echo "Next: run Tailscale Serve/Funnel on the Pi for public access."
