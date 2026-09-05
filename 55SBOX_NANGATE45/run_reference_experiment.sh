#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

./scripts/00_preflight.sh
./scripts/01_run_synthesis.sh
python3 scripts/02_collect_results.py

echo
echo "Reference comparison:"
python3 scripts/03_compare_reference.py || true

echo
echo "Done."
echo "See:"
echo "  results/summary.md"
