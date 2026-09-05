#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/common.sh"

if ! command -v "$XRUN_BIN" >/dev/null 2>&1; then
    echo "ERROR: xrun was not found after loading the Cadence environment."
    exit 3
fi

rm -rf "$ROOT/work/preflight"
mkdir -p "$ROOT/work/preflight" "$ROOT/logs"
cd "$ROOT/work/preflight"

"$XRUN_BIN" -64bit -sv \
    "$ROOT/rtl/proposed/proposed_sbox_lut.v" \
    "$ROOT/rtl/fides/fides_sbox_lut.v" \
    "$ROOT/rtl/proposed/proposed_sbox_factorized.v" \
    "$ROOT/rtl/proposed/proposed_sbox_shared_affine.v" \
    "$ROOT/tb/tb_equivalence.sv" \
    -top tb_equivalence \
    -l "$ROOT/logs/preflight_xrun.log"

grep -q "PREFLIGHT_PASS" "$ROOT/logs/preflight_xrun.log"
echo "PREFLIGHT_PASS"
