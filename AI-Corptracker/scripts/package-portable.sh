#!/usr/bin/env bash
# Собирает архив AI-Corptracker для переноса (без .env, без тяжёлых офисных файлов).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
BASENAME="$(basename "$ROOT")"
# По умолчанию архив в dist/ внутри проекта (удобно копировать)
mkdir -p "$ROOT/dist"
OUT="${1:-$ROOT/dist/${BASENAME}-portable.tar.gz}"

cd "$PARENT"
tar -czf "$OUT" \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='env' \
  --exclude='*.docx' \
  --exclude='*.xlsx' \
  --exclude='.~lock*' \
  --exclude='*~' \
  --exclude='.idea' \
  --exclude='.vscode' \
  --exclude='.cursor' \
  --exclude='dist' \
  --exclude='*.tar.gz' \
  --exclude='*.zip' \
  "$BASENAME"

echo "Готово: $OUT"
ls -lh "$OUT"
