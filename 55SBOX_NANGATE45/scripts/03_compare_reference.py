#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = {r["Configuration"]: r for r in csv.DictReader((ROOT/"reference/reference_results.csv").open())}
NEW = {r["Configuration"]: r for r in csv.DictReader((ROOT/"results/summary.csv").open())}

AREA_TOL = 0.05
DELAY_TOL = 0.005
POWER_TOL = 0.05

failed = False

missing = sorted(set(REF) - set(NEW))
unexpected = sorted(set(NEW) - set(REF))
if missing or unexpected:
    if missing:
        print("Missing configurations:", ", ".join(missing))
    if unexpected:
        print("Unexpected configurations:", ", ".join(unexpected))
    raise SystemExit(1)

for name, ref in REF.items():
    new = NEW[name]

    da = float(new["Area_um2"]) - float(ref["Area_um2"])
    dd = float(new["Delay_ns"]) - float(ref["Delay_ns"])
    dp = float(new["Total_uW"]) - float(ref["Total_uW"])

    ok = abs(da) <= AREA_TOL and abs(dd) <= DELAY_TOL and abs(dp) <= POWER_TOL

    print("{:<22s} area {:+.3f}  delay {:+.3f}  power {:+.3f}  {}".format(
        name, da, dd, dp, "PASS" if ok else "CHECK"
    ))

    if not ok:
        failed = True

raise SystemExit(1 if failed else 0)
