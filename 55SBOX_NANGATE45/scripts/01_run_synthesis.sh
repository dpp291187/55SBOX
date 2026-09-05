#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/common.sh"

if ! command -v "$GENUS_BIN" >/dev/null 2>&1; then
    echo "ERROR: genus was not found after loading the Cadence environment."
    exit 3
fi

mkdir -p "$ROOT/reports" "$ROOT/netlist" "$ROOT/logs"

run_one () {
    export CONFIGURATION="$1"
    export TOP="$2"
    export RTL="$ROOT/$3"
    export REPORT_BASE="reports"
    export NETLIST_BASE="netlist"

    echo
    echo "============================================================"
    echo "RUN $CONFIGURATION"
    echo "============================================================"

    "$GENUS_BIN" -batch \
        -files "$ROOT/genus/run_one.tcl" \
        -log "$ROOT/logs/genus_${CONFIGURATION}.log"

    grep -q "GENUS_DONE: $CONFIGURATION" "$ROOT/logs/genus_${CONFIGURATION}.log"
}

run_one PROPOSED_LUT        proposed_sbox_lut        rtl/proposed/proposed_sbox_lut.v
run_one FIDES_LUT           fides_sbox_lut           rtl/fides/fides_sbox_lut.v
run_one PROPOSED_FACTORIZED proposed_sbox_factorized rtl/proposed/proposed_sbox_factorized.v
run_one PROPOSED_SHARED_AFFINE proposed_sbox_shared_affine rtl/proposed/proposed_sbox_shared_affine.v

echo
echo "ALL_GENUS_RUNS_DONE"
