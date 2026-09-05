# SBOX_NANGATE45

Reproducible Cadence Genus/Nangate45 implementation package for the paper
**“Hardware-Efficient 5 x 5 S-Boxes with Strong Cryptographic Criteria for
Lightweight Cryptography.”**

The package contains the exact RTL, constraints, scripts, reference lookup
tables, mapped netlists, synthesis reports, and summarized results for the four
implementations reported in the revised manuscript.

## 1. Evaluated configurations

| Configuration | S-box | Realization |
|---|---|---|
| `PROPOSED_LUT` | Proposed | Direct 32-entry lookup table |
| `FIDES_LUT` | FIDES | Direct 32-entry lookup table |
| `PROPOSED_FACTORIZED` | Proposed | Factorized Boolean realization |
| `PROPOSED_SHARED_AFFINE` | Proposed | Shared-affine area-oriented realization |

The direct-LUT pair provides the common-representation comparison between the
two mappings. The factorized and shared-affine circuits are implementation
points developed specifically for the proposed mapping. They are not presented
as transformations that can automatically be transferred to an arbitrary
S-box.

## 2. S-box definitions

### Proposed S-box

Entry `i` is the decimal output for input `i`:

```text
[16, 18, 28,  8,  1, 13, 17, 11,
 19, 24, 29,  0,  7,  2, 21,  6,
 20,  4, 31, 25,  9, 23, 30, 22,
  3, 26, 10,  5, 27, 12, 14, 15]
```

Machine-readable copy: `reference/proposed_sbox_lut.txt`.

### FIDES S-box

```text
[ 1,  0, 25, 26, 17, 29, 21, 27,
 20,  5,  4, 23, 14, 18,  2, 28,
 15,  8,  6,  3, 13,  7, 24, 16,
 30,  9, 31, 10, 22, 12, 11, 19]
```

Machine-readable copy: `reference/fides_sbox_lut.txt`.

## 3. Project layout

```text
SBOX_NANGATE45/
|-- README.md
|-- SHA256SUMS.txt
|-- config.sh
|-- run_reference_experiment.sh
|-- rtl/
|   |-- proposed/
|   |   |-- proposed_sbox_lut.v
|   |   |-- proposed_sbox_factorized.v
|   |   `-- proposed_sbox_shared_affine.v
|   `-- fides/
|       `-- fides_sbox_lut.v
|-- tb/
|   `-- tb_equivalence.sv
|-- genus/
|   `-- run_one.tcl
|-- scripts/
|   |-- 00_preflight.sh
|   |-- 01_run_synthesis.sh
|   |-- 02_collect_results.py
|   |-- 03_compare_reference.py
|   |-- 04_pack_results.sh
|   |-- clean.sh
|   `-- common.sh
|-- reference/
|   |-- proposed_sbox_lut.txt
|   |-- fides_sbox_lut.txt
|   |-- designs.csv
|   `-- reference_results.csv
|-- reports/
|-- netlist/
|-- logs/
|-- results/
`-- work/
```

The `rtl`, `tb`, `genus`, `scripts`, and `reference` directories contain the
reproducible source flow. The `reports`, `netlist`, `logs`, and `results`
directories contain the retained outputs from the reference run.

## 4. Required software and library

- Linux shell and Python 3;
- Cadence Genus;
- Cadence Xcelium (`xrun`);
- `NangateOpenCellLibrary_typical.lib` from the Nangate Open Cell Library.

Reference-run versions and the Liberty-file checksum are recorded in
`logs/environment.txt`.

## 5. Configure local paths

The archive deliberately contains no user-specific absolute path. Before a new
run, export the local Nangate45 Liberty path. If Cadence is not already on
`PATH`, also export the site setup script:

```bash
export LIB_FILE=/absolute/path/to/NangateOpenCellLibrary_typical.lib
export CADENCE_SETUP=/absolute/path/to/cadence_setup.sh
```

`CADENCE_SETUP` is optional when `genus` and `xrun` are already available.
Alternative executable names may be selected with `GENUS_BIN` and `XRUN_BIN`.

## 6. Exhaustive functional verification

Run:

```bash
./scripts/00_preflight.sh
```

For every input from 0 through 31, the testbench checks:

- `proposed_sbox_lut` against the proposed reference LUT;
- `proposed_sbox_factorized` against the same LUT;
- `proposed_sbox_shared_affine` against the same LUT; and
- `fides_sbox_lut` against the FIDES reference LUT.

A successful run ends with:

```text
PREFLIGHT_PASS
```

## 7. ASIC synthesis flow

Run all four configurations with:

```bash
./scripts/01_run_synthesis.sh
```

For each configuration, `genus/run_one.tcl` applies the same flow:

1. load `NangateOpenCellLibrary_typical.lib`;
2. read and elaborate the selected RTL top module;
3. create a 10-ns virtual clock;
4. set input and output delays to 0 ns;
5. run `syn_generic`, `syn_map`, and `syn_opt`;
6. report final area, input-to-output delay, QoR, vectorless preliminary power,
   and mapped cell usage; and
7. write the mapped Verilog netlist and SDC file.

The 10-ns virtual clock provides a common timing reference for these purely
combinational S-boxes; the reported critical delay is measured from input to
output. The reported power is a vectorless preliminary estimate and is not a
post-layout signoff value.

## 8. Collect and verify the results

Collect the report values:

```bash
python3 scripts/02_collect_results.py
```

Compare them with the retained reference run:

```bash
python3 scripts/03_compare_reference.py
```

The comparison tolerances are 0.05 square micrometres for area, 0.005 ns for
delay, and 0.05 microwatts for total preliminary power. A different Genus
release or a different Liberty file may legitimately produce different mapped
results; such a run should be reported with its exact tool/library settings.

The complete one-command flow is:

```bash
./run_reference_experiment.sh
```

## 9. Retained reference results

| Configuration | Cells | Area (um^2) | Delay (ns) | ADP (um^2 ns) | Total power (uW) |
|---|---:|---:|---:|---:|---:|
| `PROPOSED_LUT` | 39 | 38.304 | 0.310 | 11.874 | 5.241 |
| `FIDES_LUT` | 35 | 35.910 | 0.309 | 11.096 | 4.612 |
| `PROPOSED_FACTORIZED` | 31 | 34.314 | 0.251 | 8.613 | 4.383 |
| `PROPOSED_SHARED_AFFINE` | 28 | 32.718 | 0.332 | 10.862 | 4.231 |

More precise machine-readable values are stored in `results/summary.csv` and
`reference/reference_results.csv`. Per-cell mapped counts are available in each
`reports/<CONFIGURATION>/09_gates_final.rpt` file.

## 10. Interpretation of the comparison

The `PROPOSED_LUT` and `FIDES_LUT` results are the strict common-RTL-style
comparison: both mappings use a 32-entry combinational case statement and pass
through the same synthesis script, constraints, tool version, and standard-cell
library. Under this common representation, the FIDES lookup-table realization
is slightly smaller and has nearly the same delay.

The factorized and shared-affine circuits show the implementation potential of
the proposed mapping after mapping-specific Boolean restructuring. Because such
restructuring depends on the algebraic structure of the individual mapping, it
would not be scientifically valid to claim that exactly the same factorization
can be imposed on FIDES. Accordingly, the package reports the common-LUT
comparison separately from the proposed mapping's two optimized realizations.

## 11. Package the generated outputs

After a new run, create a timestamped result archive with:

```bash
./scripts/04_pack_results.sh
```

To remove generated outputs while retaining the source flow, use:

```bash
./scripts/clean.sh
```

## 12. Reusing the retained results

No ASIC rerun is required merely because this release removes configurations
that are not reported in the revised manuscript. The RTL, synthesis constraints,
standard-cell library, and retained reports for the four configurations listed
in Section 1 are unchanged. The summary tables are regenerated directly from
those retained reports. A new ASIC run is needed only if the RTL, constraints,
tool version, Liberty file, or synthesis options are changed.
