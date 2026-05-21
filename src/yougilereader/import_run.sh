#!/usr/bin/env bash
cd "$(dirname "$0")/.."
exec python3 -m yougilereader.import_to_db "$@"
