| Stage | S-box | Configuration | Method | Cells | Area (um^2) | Delay (ns) | ADP (um^2 ns) | Leakage (uW) | Internal (uW) | Switching (uW) | Total (uW) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1. Direct LUT encoding | Proposed S-box | `PROPOSED_LUT` | Direct 32-entry LUT encoding | 39 | 38.304 | 0.310 | 11.874 | 0.986 | 1.718 | 2.538 | 5.241 |
| 1. Direct LUT encoding | FIDES S-box | `FIDES_LUT` | Direct 32-entry LUT encoding | 35 | 35.910 | 0.309 | 11.096 | 0.904 | 1.552 | 2.156 | 4.612 |
| 2. Proposed factorized realization | Proposed S-box | `PROPOSED_FACTORIZED` | Factorized Boolean realization used in the proposed design | 31 | 34.314 | 0.251 | 8.613 | 0.818 | 1.716 | 1.849 | 4.383 |
| 2. Shared-affine area-oriented realization | Proposed S-box | `PROPOSED_SHARED_AFFINE` | Shared-affine realization selected from the ASIC-aware search | 28 | 32.718 | 0.332 | 10.862 | 0.771 | 1.757 | 1.703 | 4.231 |
