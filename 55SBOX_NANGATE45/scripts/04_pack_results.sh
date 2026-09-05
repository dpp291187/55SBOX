#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/02_collect_results.py

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="SBOX_NANGATE45_RESULTS_${STAMP}.tar.gz"

tar -czf "$OUT" reports netlist logs results

echo
echo "Created:"
echo "  $ROOT/$OUT"
