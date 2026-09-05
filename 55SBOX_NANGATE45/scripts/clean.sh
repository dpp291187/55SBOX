#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

rm -rf "$ROOT/reports/"*
rm -rf "$ROOT/netlist/"*
rm -rf "$ROOT/logs/"*
rm -rf "$ROOT/results/"*
rm -rf "$ROOT/work/"*

echo "Generated outputs removed."
