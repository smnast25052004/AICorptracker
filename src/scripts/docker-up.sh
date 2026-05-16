#!/usr/bin/env bash
# Поднять все сервисы AI-Corptracker. Ищет Compose в PATH, /usr/local/bin, плагин docker compose.
set -euo pipefail
cd "$(dirname "$0")/.."

run_compose() {
  if docker compose version &>/dev/null; then
    exec docker compose "$@"
  fi
  if command -v docker-compose &>/dev/null; then
    exec docker-compose "$@"
  fi
  if [[ -x /usr/local/bin/docker-compose ]]; then
    exec /usr/local/bin/docker-compose "$@"
  fi
  echo "Docker Compose не найден. Установите один из вариантов:" >&2
  echo "  sudo apt install -y docker-compose-plugin   # затем: docker compose up -d" >&2
  echo "  sudo apt install -y docker-compose" >&2
  exit 1
}

run_compose up -d "$@"
