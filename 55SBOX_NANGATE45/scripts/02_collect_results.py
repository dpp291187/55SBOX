#!/usr/bin/env python3
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGNS = ROOT / "reference" / "designs.csv"
OUT_CSV = ROOT / "results" / "summary.csv"
OUT_MD = ROOT / "results" / "summary.md"

def read_text(path):
    return path.read_text(errors="ignore") if path.exists() else ""

def parse_area(text):
    m = re.search(r"^\S+\s+NA\s+(\d+)\s+([0-9.]+)\s+[0-9.]+\s+([0-9.]+)", text, re.M)
    if not m:
        return None, None
    return int(m.group(1)), float(m.group(2))

def parse_delay(text):
    values = [int(v) for v in re.findall(r"Data Path:-\s+(\d+)", text)]
    return max(values) / 1000.0 if values else None

def parse_power(text):
    m = re.search(
        r"^\s*logic\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)",
        text,
        re.M,
    )
    if not m:
        return (None, None, None, None)
    return tuple(float(m.group(i)) * 1e6 for i in range(1, 5))

rows = []
with DESIGNS.open() as f:
    for d in csv.DictReader(f):
        rpt = ROOT / "reports" / d["Configuration"]
        cells, area = parse_area(read_text(rpt / "05_area_final.rpt"))
        delay = parse_delay(read_text(rpt / "06_timing_final.rpt"))
        leakage, internal, switching, total = parse_power(
            read_text(rpt / "08_power_preliminary.rpt")
        )

        if area is None or delay is None:
            raise SystemExit("Missing or unparsable reports for %s" % d["Configuration"])

        rows.append({
            **d,
            "Cells": cells,
            "Area_um2": area,
            "Delay_ns": delay,
            "ADP_um2_ns": area * delay,
            "Leakage_uW": leakage,
            "Internal_uW": internal,
            "Switching_uW": switching,
            "Total_uW": total,
        })

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "Stage","Stage_Name","Sbox","Configuration","Method","Cells",
    "Area_um2","Delay_ns","ADP_um2_ns",
    "Leakage_uW","Internal_uW","Switching_uW","Total_uW"
]

with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in fields})

lines = [
    "| Stage | S-box | Configuration | Method | Cells | Area (um^2) | Delay (ns) | ADP (um^2 ns) | Leakage (uW) | Internal (uW) | Switching (uW) | Total (uW) |",
    "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]

for r in rows:
    lines.append(
        "| {Stage}. {Stage_Name} | {Sbox} | `{Configuration}` | {Method} | {Cells} | "
        "{Area_um2:.3f} | {Delay_ns:.3f} | {ADP_um2_ns:.3f} | "
        "{Leakage_uW:.3f} | {Internal_uW:.3f} | {Switching_uW:.3f} | {Total_uW:.3f} |".format(**r)
    )

OUT_MD.write_text("\n".join(lines) + "\n")

print("WROTE", OUT_CSV)
print("WROTE", OUT_MD)
print()
for r in rows:
    print("{:<22s} cells={:>2d} area={:7.3f} delay={:.3f} ADP={:7.3f} power={:.3f}".format(
        r["Configuration"], r["Cells"], r["Area_um2"], r["Delay_ns"],
        r["ADP_um2_ns"], r["Total_uW"]
    ))
