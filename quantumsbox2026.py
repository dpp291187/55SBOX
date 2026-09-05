
from math import log2
from typing import List, Tuple, Dict, Optional, Any
from collections import Counter, defaultdict
from statistics import median
import csv

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XGate
from qiskit.visualization import circuit_drawer
import matplotlib.pyplot as plt

from typing import Iterable, Dict, Any, List
from qiskit import transpile

def _filter_non_gates(ops: Dict[str, int]) -> Dict[str, int]:
    """Loại các pseudo-ops không phải cổng thực (barrier, measure, ...)."""
    drop = {"barrier", "measure", "snapshot", "delay"}
    return {g: int(v) for g, v in ops.items() if g not in drop}

def hw_gate_breakdown_per_seed(
    qc,
    seeds: Iterable[int],
    opt_level: int = 2,
    basis_hw=("cx", "rz", "sx", "x", "h"),
) -> List[Dict[str, Any]]:
    """
    Trả về list các dòng breakdown theo từng seed sau transpile về basis_hw.
    Mỗi dòng có: depth, twoq_depth, count từng gate trong basis, total, other.
    """
    rows = []
    for sd in seeds:
        tqc = transpile(
            qc,
            basis_gates=list(basis_hw),
            optimization_level=int(opt_level),
            seed_transpiler=int(sd),
        )
        ops = _filter_non_gates(tqc.count_ops())

        row = {
            "seed": int(sd),
            "depth": int(tqc.depth()),
            "twoq_depth": int(layer_count_of_gate(tqc, {"cx"})),  # bạn đã có hàm này
        }
        # counts trong basis
        for g in basis_hw:
            row[g] = int(ops.get(g, 0))

        # phần còn lại (nếu transpile ra gate lạ)
        other = {g: int(v) for g, v in ops.items() if g not in set(basis_hw)}
        row["other"] = other
        row["total"] = int(sum(ops.values()))
        rows.append(row)
    return rows

def print_hw_gate_breakdown(
    qc,
    title: str,
    seeds: Iterable[int],
    opt_level: int = 2,
    basis_hw=("cx", "rz", "sx", "x", "h"),
) -> None:
    rows = hw_gate_breakdown_per_seed(qc, seeds, opt_level=opt_level, basis_hw=basis_hw)

    print(f"\n=== HW gate breakdown ({title}) | basis={list(basis_hw)} | opt_level={opt_level} ===")
    for r in rows:
        other_str = f" | other={r['other']}" if r["other"] else ""
        print(
            f" seed={r['seed']}: depth={r['depth']} twoq_depth={r['twoq_depth']} | "
            f"cx={r['cx']} rz={r['rz']} sx={r['sx']} x={r['x']} h={r['h']} | total={r['total']}"
            f"{other_str}"
        )

    # (tuỳ chọn) in min/med/max cho từng gate trong basis
    def _mmm(key: str):
        xs = [r[key] for r in rows]
        return agg_min_med_max(xs)  # bạn đã có hàm này

    print("  min/med/max:")
    for key in ["depth", "twoq_depth", "cx", "rz", "sx", "x", "h", "total"]:
        d = _mmm(key)
        print(f"   - {key:>10}: min={d['min']:.0f}, med={d['med']:.0f}, max={d['max']:.0f}")

# =========================================================
# 0) Helpers
# =========================================================
def popcount(x: int) -> int:
    return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")

def safe_median(xs: List[int]) -> Optional[float]:
    return float(median(xs)) if xs else None

def agg_min_med_max(xs: List[int]) -> Dict[str, Optional[float]]:
    if not xs:
        return {"min": None, "med": None, "max": None}
    return {"min": float(min(xs)), "med": float(median(xs)), "max": float(max(xs))}

def is_bijective(S: List[int]) -> bool:
    return len(set(S)) == len(S)

def infer_nm(S: List[int]) -> Tuple[int, int]:
    L = len(S)
    n = int(round(log2(L)))
    if (1 << n) != L:
        raise ValueError("len(S) must be 2^n.")
    vmax = max(S) if S else 0
    m = max(1, vmax.bit_length())
    if any(v < 0 or v >= (1 << m) for v in S):
        raise ValueError("S-box values out of range for inferred m.")
    return n, m


# =========================================================
# 1) Möbius transform -> ANF masks
# =========================================================
def mobius_anf(f_vals: List[int], n: int) -> List[int]:
    """Truth table (0/1) -> ANF coefficients (0/1) indexed by mask."""
    a = f_vals[:]
    for i in range(n):
        step = 1 << i
        for mask in range(1 << n):
            if mask & step:
                a[mask] ^= a[mask ^ step]
    return a

def truth_bit_from_sbox(S: List[int], n: int, m: int, out_bit_idx: int) -> List[int]:
    """out_bit_idx: 0..m-1, where 0 is MSB of output."""
    return [ (S[x] >> (m - 1 - out_bit_idx)) & 1 for x in range(1 << n) ]

def anf_masks_from_sbox(S: List[int]) -> Tuple[int, int, List[List[int]]]:
    """
    Return: n, m, masks_per_bit[k] = list of ANF masks with coeff 1 for output bit k (MSB-first).
    """
    n, m = infer_nm(S)
    masks_per_bit = []
    for k in range(m):
        f = truth_bit_from_sbox(S, n, m, k)
        coeffs = mobius_anf(f, n)
        masks = [mask for mask, c in enumerate(coeffs) if c]
        masks_per_bit.append(masks)
    return n, m, masks_per_bit


# =========================================================
# 2) ANF stats (very useful for explaining cost differences)
# =========================================================
def anf_stats(anf_masks: List[List[int]]) -> Dict[str, Any]:
    deg_hist = defaultdict(int)
    per_bit_terms = []
    per_bit_maxdeg = []
    total_terms = 0
    max_deg = 0
    hi_deg_terms = 0  # degree >= 3

    for masks in anf_masks:
        total_terms += len(masks)
        per_bit_terms.append(len(masks))
        bd = 0
        for mask in masks:
            d = popcount(mask)
            deg_hist[d] += 1
            bd = max(bd, d)
            max_deg = max(max_deg, d)
            if d >= 3:
                hi_deg_terms += 1
        per_bit_maxdeg.append(bd)

    deg_hist = dict(sorted(deg_hist.items(), key=lambda kv: kv[0]))
    return {
        "total_terms": int(total_terms),
        "max_deg": int(max_deg),
        "hi_deg_terms": int(hi_deg_terms),
        "deg_hist": deg_hist,
        "per_bit_terms": per_bit_terms,
        "per_bit_maxdeg": per_bit_maxdeg,
    }

def required_clean_ancilla_from_degree(d_max: int) -> int:
    # AND-chain method used below: monomial degree d>=3 needs (d-2) clean ancilla
    return max(0, d_max - 2)


# =========================================================
# 3) Circuit builders
# =========================================================
def _apply_mcx(qc: QuantumCircuit, ctrls, tgt):
    d = len(ctrls)
    if d == 0:
        qc.x(tgt)
    elif d == 1:
        qc.cx(ctrls[0], tgt)
    elif d == 2:
        qc.ccx(ctrls[0], ctrls[1], tgt)
    else:
        qc.append(XGate().control(d), list(ctrls) + [tgt])  # generic MCX

def circuit_no_ancilla(n: int, m: int, anf_masks: List[List[int]], name="sbox_no_anc") -> QuantumCircuit:
    """|x>|0^m> -> |x>|S(x)> using direct MCX for each monomial."""
    qc = QuantumCircuit(n + m, name=name)
    x = [qc.qubits[i] for i in range(n)]
    y = [qc.qubits[n + k] for k in range(m)]
    for k in range(m):
        for mask in anf_masks[k]:
            ctrls = [x[i] for i in range(n) if (mask >> (n - 1 - i)) & 1]
            _apply_mcx(qc, ctrls, y[k])
    return qc

def circuit_clean_ancilla(n: int, m: int, anf_masks: List[List[int]],
                          work: int, name="sbox_clean_anc") -> QuantumCircuit:
    """
    Clean ancilla compute–toggle–uncompute:
      d=0 : X(y)
      d=1 : CX
      d=2 : CCX
      d>=3:
        chain into ancilla a[0..d-3], then CCX(a_last, last_control -> y), then uncompute.
    Needs (d-2) clean ancilla for degree d.
    """
    qc = QuantumCircuit(n + m + work, name=name)
    x = [qc.qubits[i] for i in range(n)]
    y = [qc.qubits[n + k] for k in range(m)]
    a = [qc.qubits[n + m + t] for t in range(work)]

    for k in range(m):
        for mask in anf_masks[k]:
            ctrls_idx = [i for i in range(n) if (mask >> (n - 1 - i)) & 1]
            d = len(ctrls_idx)

            if d == 0:
                qc.x(y[k]); continue
            if d == 1:
                qc.cx(x[ctrls_idx[0]], y[k]); continue
            if d == 2:
                qc.ccx(x[ctrls_idx[0]], x[ctrls_idx[1]], y[k]); continue

            need = d - 2
            if work < need:
                raise ValueError(f"Need >= {need} clean ancilla, but work={work}.")

            c = [x[i] for i in ctrls_idx]

            # compute chain into a[0..need-1]
            qc.ccx(c[0], c[1], a[0])
            for j in range(2, d - 1):  # up to c[d-2]
                qc.ccx(a[j - 2], c[j], a[j - 1])

            # toggle target using last control c[d-1]
            qc.ccx(a[need - 1], c[d - 1], y[k])

            # uncompute chain
            for j in reversed(range(2, d - 1)):
                qc.ccx(a[j - 2], c[j], a[j - 1])
            qc.ccx(c[0], c[1], a[0])

    return qc


# =========================================================
# 4) Safe export of circuit drawings
# =========================================================
# def _drawer_mpl(qc: QuantumCircuit, fold: int, scale: float):
#     # Some qiskit versions don't support vertical_compression; try safely.
#     try:
#         return circuit_drawer(qc, output="mpl", fold=fold, scale=scale,
#                               idle_wires=True, vertical_compression="high")
#     except TypeError:
#         return circuit_drawer(qc, output="mpl", fold=fold, scale=scale,
#                               idle_wires=True)

def _drawer_mpl(qc: QuantumCircuit, fold: int, scale: float):
    try:
        return circuit_drawer(
            qc, output="mpl", fold=fold, scale=scale,
            idle_wires=True,
            plot_barriers=True,              # <<< thêm
            vertical_compression="high"
        )
    except TypeError:
        return circuit_drawer(
            qc, output="mpl", fold=fold, scale=scale,
            idle_wires=True,
            plot_barriers=False               # <<< thêm
        )


def draw_and_save(qc: QuantumCircuit,
                  base: str,
                  dpi: int = 500,
                  scale: float = 0.85,
                  fold: int = 10**9,          # rất lớn để không wrap
                  fixed_inches=None,          # (W,H) inch
                  tight: bool = True) -> str:
    """
    - tight=True  : crop sát nội dung (như bạn đang dùng)
    - tight=False : giữ nguyên canvas (quan trọng để các part cùng kích thước)
    - fixed_inches: ép size canvas cho đồng nhất giữa các part
    """
    try:
        fig = _drawer_mpl(qc, fold=fold, scale=scale)

        if fixed_inches is not None:
            fig.set_size_inches(float(fixed_inches[0]), float(fixed_inches[1]))
            # canh trái nội dung (nếu matplotlib/qiskit có anchor)
            try:
                ax = fig.axes[0]
                ax.set_anchor("W")
                fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
            except Exception:
                pass

        if tight and fixed_inches is None:
            bbox = "tight"
            pad = 0.1
        else:
            bbox = None
            pad = 0.0

        fig.savefig(base + ".png", dpi=dpi, bbox_inches="tight", pad_inches=0.01)
        fig.savefig(base + ".pdf", dpi=dpi, bbox_inches="tight", pad_inches=0.01)
        plt.close(fig)
        return "png+pdf"
    except Exception:
        plt.close("all")
        return "skipped"


from qiskit.converters import circuit_to_dag
from qiskit.converters import circuit_to_dag

def _num_layers(qc: QuantumCircuit) -> int:
    return len(list(circuit_to_dag(qc).layers()))

def pad_part_to_cols(qc_part: QuantumCircuit, target_cols: int) -> QuantumCircuit:
    """Pad thêm barrier ở CUỐI để canh trái và kéo dài wires tới hết khung."""
    cur = _num_layers(qc_part)
    if cur >= target_cols:
        return qc_part
    out = qc_part.copy()
    all_q = list(range(out.num_qubits))
    for _ in range(target_cols - cur):
        out.barrier(all_q)   # mỗi barrier ~ 1 “cột”
    return out


def num_layers(qc: QuantumCircuit) -> int:
    return len(list(circuit_to_dag(qc).layers()))

def pad_to_layers_end(qc: QuantumCircuit, target_layers: int) -> QuantumCircuit:
    """
    Pad ở CUỐI để canh trái: thêm barrier (ẩn khi vẽ) cho tới khi đủ target_layers.
    """
    cur = num_layers(qc)
    if cur >= target_layers:
        return qc

    out = qc.copy()
    all_q = list(range(out.num_qubits))
    for _ in range(target_layers - cur):
        out.barrier(all_q)   # tạo thêm 1 “cột/layer rỗng”
    return out


def split_circuit_by_layers(qc: QuantumCircuit, cols_per_part: int = 48) -> List[QuantumCircuit]:
    """
    Tách circuit thành nhiều part, mỗi part gồm cols_per_part 'cột' ~ layers (DAG layers).
    Giữ nguyên số qubit/clbit, chỉ lấy các op thuộc các layer tương ứng.
    """
    dag = circuit_to_dag(qc)
    layers = list(dag.layers())
    if len(layers) <= cols_per_part:
        return [qc]

    parts: List[QuantumCircuit] = []
    n_qubits = qc.num_qubits
    n_clbits = qc.num_clbits

    # map theo index để an toàn
    # (qc.qubits[i] -> qc_part.qubits[i])
    for p, start in enumerate(range(0, len(layers), cols_per_part), 1):
        qc_part = QuantumCircuit(n_qubits, n_clbits, name=f"{qc.name}_p{p}")
        qmap = {qc.qubits[i]: qc_part.qubits[i] for i in range(n_qubits)}
        cmap = {qc.clbits[i]: qc_part.clbits[i] for i in range(n_clbits)}

        chunk = layers[start:start + cols_per_part]
        for layer in chunk:
            for node in layer["graph"].op_nodes():
                qc_part.append(
                    node.op,
                    [qmap[q] for q in node.qargs],
                    [cmap[c] for c in node.cargs],
                )

        parts.append(qc_part)

    return parts

def draw_and_save_segmented(qc: QuantumCircuit,
                            base: str,
                            cols_per_part: int = 48,
                            dpi: int = 500,
                            scale: float = 0.85) -> str:
    parts = split_circuit_by_layers(qc, cols_per_part=cols_per_part)

    # >>> bắt buộc pad để part nào cũng đủ cột -> wires kéo dài đều
    parts = [pad_part_to_cols(p, cols_per_part) for p in parts]

    if len(parts) == 1:
        return draw_and_save(qc, base, dpi=dpi, scale=scale, tight=True)

    # >>> PAD để part nào cũng dài đúng cols_per_part layer (canh trái)
    parts = [pad_to_layers_end(p, cols_per_part) for p in parts]

    # ---- Pass 1: lấy canvas size lớn nhất ----
    sizes = []
    for p in parts:
        fig = _drawer_mpl(p, fold=48, scale=scale)
        sizes.append(fig.get_size_inches())
        plt.close(fig)

    fixed = (max(s[0] for s in sizes), max(s[1] for s in sizes))

    # ---- Pass 2: save theo cùng fixed canvas ----
    k = len(parts)
    for i, p in enumerate(parts, 1):
        draw_and_save(
            p,
            f"{base}_p{i:02d}of{k:02d}",
            dpi=dpi,
            scale=scale,
            fixed_inches=fixed,
            tight=False
        )

    return f"segmented({k} parts, {cols_per_part} cols/part, fixed_canvas={fixed})"


def export_all_views(qc: QuantumCircuit,
                     base: str,
                     seeds: List[int],
                     opt_level_hw: int,
                     opt_level_nct: int,
                     export_raw: bool = True,
                     export_hw: bool = True,
                     export_nct: bool = True,
                     cols_per_part: int = 28) -> Dict[str, str]:
    out = {}
    seed_draw = seeds[0] if seeds else 0
    fixed = (20, 3.2)
    cols_per_part=42
    # 1) RAW
    if export_raw:
        out["RAW"] = draw_and_save_segmented(
            qc, base + "_RAW",
            cols_per_part=cols_per_part,
            dpi=dpi, scale=0.85
        )

    # 2) HW basis
    if export_hw:
        basis_hw = ["cx", "rz", "sx", "x", "h"]
        try:
            tqc_hw = compile_once(qc, basis_hw, opt_level_hw, seed_draw)
            out["HW"] = draw_and_save_segmented(
                tqc_hw, base + f"_HW_seed{seed_draw}",
                cols_per_part=cols_per_part,
                dpi=dpi, scale=0.85
            )
        except Exception:
            out["HW"] = "skipped"

    # 3) NCT basis
    if export_nct:
        basis_nct = ["x", "cx", "ccx"]
        try:
            tqc_nct = compile_once(qc, basis_nct, opt_level_nct, seed_draw)
            out["NCT"] = draw_and_save_segmented(
                tqc_nct, base + f"_NCT_seed{seed_draw}",
                cols_per_part=cols_per_part,
                dpi=dpi, scale=0.85
            )
        except Exception:
            out["NCT"] = "unavailable"

    return out



# =========================================================
# 5) Metrics (logical + compiled)
# =========================================================
def logical_counts(qc: QuantumCircuit) -> Dict[str, int]:
    cnt = Counter(inst.operation.name for inst in qc.data)

    # Attempt to detect multi-controlled X variants (names vary by version)
    mcx_like = 0
    for name, v in cnt.items():
        nm = name.lower()
        if "mcx" in nm or nm.startswith("c") and nm.endswith("x") and nm not in ("cx", "ccx"):
            mcx_like += v

    return {
        "width_raw": qc.num_qubits,
        "depth_raw": qc.depth(),
        "x": int(cnt.get("x", 0)),
        "cx": int(cnt.get("cx", 0)),
        "ccx": int(cnt.get("ccx", 0)),
        "mcx_like": int(mcx_like),
        "total_ops": int(sum(cnt.values())),
    }

def layer_count_of_gate(circ: QuantumCircuit, gate_names: set) -> int:
    """Count how many DAG layers contain at least one op whose name is in gate_names."""
    from qiskit.converters import circuit_to_dag
    dag = circuit_to_dag(circ)
    layers = 0
    for layer in dag.layers():
        ops = layer["graph"].op_nodes()
        if any(op.name in gate_names for op in ops):
            layers += 1
    return int(layers)

def compile_once(qc: QuantumCircuit,
                 basis: List[str],
                 opt_level: int,
                 seed: int) -> QuantumCircuit:
    return transpile(qc, basis_gates=basis, optimization_level=opt_level, seed_transpiler=seed)

def compiled_metrics_hw(qc: QuantumCircuit,
                        opt_level: int,
                        seeds: List[int],
                        basis_hw=("cx", "rz", "sx", "x", "h")) -> Dict[str, Any]:
    depths, twoq_depths, cxs, oneqs, totals = [], [], [], [], []
    for sd in seeds:
        tqc = compile_once(qc, list(basis_hw), opt_level, sd)
        ops = tqc.count_ops()
        depth = int(tqc.depth())
        cx = int(ops.get("cx", 0))
        oneq = int(sum(v for g, v in ops.items() if g != "cx"))
        total = int(sum(ops.values()))
        twoq_depth = layer_count_of_gate(tqc, {"cx"})
        depths.append(depth)
        cxs.append(cx)
        oneqs.append(oneq)
        totals.append(total)
        twoq_depths.append(twoq_depth)

    return {
        "basis": "HW",
        "width": qc.num_qubits,
        "depth": agg_min_med_max(depths),
        "twoq_depth": agg_min_med_max(twoq_depths),
        "cx": agg_min_med_max(cxs),
        "oneq_total": agg_min_med_max(oneqs),
        "gates_total": agg_min_med_max(totals),
        "seeds": seeds,
    }

def compiled_metrics_nct(qc: QuantumCircuit,
                         opt_level: int,
                         seeds: List[int],
                         basis_nct=("x", "cx", "ccx")) -> Dict[str, Any]:
    """
    Try compile to NCT basis (x,cx,ccx) to report Toffoli-count + Toffoli-depth.
    This often works best for circuits already expressed using x/cx/ccx (e.g., clean-ancilla).
    If transpile cannot express some ops in this basis, we mark as unavailable.
    """
    depths, cxs, ccxs, totals, toff_depths = [], [], [], [], []
    ok = True
    for sd in seeds:
        try:
            tqc = compile_once(qc, list(basis_nct), opt_level, sd)
        except Exception:
            ok = False
            break

        ops = tqc.count_ops()
        depth = int(tqc.depth())
        cx = int(ops.get("cx", 0))
        ccx = int(ops.get("ccx", 0))
        total = int(sum(ops.values()))
        td = layer_count_of_gate(tqc, {"ccx"})
        depths.append(depth)
        cxs.append(cx)
        ccxs.append(ccx)
        totals.append(total)
        toff_depths.append(td)

    if not ok:
        return {"basis": "NCT", "available": False}

    return {
        "basis": "NCT",
        "available": True,
        "width": qc.num_qubits,
        "depth": agg_min_med_max(depths),
        "cx": agg_min_med_max(cxs),
        "ccx": agg_min_med_max(ccxs),
        "toffoli_depth": agg_min_med_max(toff_depths),
        "gates_total": agg_min_med_max(totals),
        "seeds": seeds,
    }


# =========================================================
# 6) Pareto + objective ranking
# =========================================================
def dominates(a: Dict[str, float], b: Dict[str, float], keys: List[str]) -> bool:
    """a dominates b if a <= b for all keys and < for at least one key."""
    le_all = all(a[k] <= b[k] for k in keys)
    lt_any = any(a[k] < b[k] for k in keys)
    return le_all and lt_any

def pareto_front(items: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
    """Return non-dominated set (Pareto front)."""
    front = []
    for i, it in enumerate(items):
        dominated_flag = False
        for j, jt in enumerate(items):
            if i != j and dominates(jt["vec"], it["vec"], keys):
                dominated_flag = True
                break
        if not dominated_flag:
            front.append(it)
    return front

def objective_score(vec: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(weights.get(k, 0.0) * vec[k] for k in weights.keys())


# =========================================================
# 7) Evaluate one S-box
# =========================================================
def evaluate_sbox(S: List[int],
                  label: str,
                  seeds: List[int],
                  opt_level_hw: int = 2,
                  opt_level_nct: int = 1,
                  export: bool = True,
                  out_prefix: str = "") -> Dict[str, Any]:

    n, m, anf_masks = anf_masks_from_sbox(S)
    astats = anf_stats(anf_masks)
    work = required_clean_ancilla_from_degree(astats["max_deg"])

    qc_no = circuit_no_ancilla(n, m, anf_masks, name=f"{label}_noanc")
    qc_ca = circuit_clean_ancilla(n, m, anf_masks, work=work, name=f"{label}_cleananc")
    print_hw_gate_breakdown(qc_no, title=f"{label} no_ancilla", seeds=seeds, opt_level=opt_level_hw)
    print_hw_gate_breakdown(qc_ca, title=f"{label} clean_ancilla", seeds=seeds, opt_level=opt_level_hw)

    res = {
        "label": label,
        "n": n,
        "m": m,
        "bijective": is_bijective(S),
        "anf": astats,
        "clean_work": work,
        "no_ancilla": {},
        "clean_ancilla": {},
    }

    # logical
    res["no_ancilla"]["logical"] = logical_counts(qc_no)
    res["clean_ancilla"]["logical"] = logical_counts(qc_ca)

    # compiled HW metrics (robust across seeds)
    res["no_ancilla"]["hw"] = compiled_metrics_hw(qc_no, opt_level_hw, seeds)
    res["clean_ancilla"]["hw"] = compiled_metrics_hw(qc_ca, opt_level_hw, seeds)

    # compiled NCT metrics (best-effort)
    res["no_ancilla"]["nct"] = compiled_metrics_nct(qc_no, opt_level_nct, seeds)
    res["clean_ancilla"]["nct"] = compiled_metrics_nct(qc_ca, opt_level_nct, seeds)

    # export drawings
    # if export:
    #     base_no = f"{out_prefix}{label}_{n}x{m}_noanc"
    #     base_ca = f"{out_prefix}{label}_{n}x{m}_cleananc"
    #     res["no_ancilla"]["export"] = draw_and_save(qc_no, base_no, dpi=220, scale=0.85)
    #     res["clean_ancilla"]["export"] = draw_and_save(qc_ca, base_ca, dpi=220, scale=0.85)
    #
    # return res
# export drawings (RAW + HW + NCT)
    if export:
        base_no = f"{out_prefix}{label}_{n}x{m}_noanc"
        base_ca = f"{out_prefix}{label}_{n}x{m}_cleananc"

        res["no_ancilla"]["exports"] = export_all_views(
            qc_no, base_no,
            seeds=seeds,
            opt_level_hw=opt_level_hw,
            opt_level_nct=opt_level_nct,
            export_raw=True, export_hw=True, export_nct=True
        )

        res["clean_ancilla"]["exports"] = export_all_views(
            qc_ca, base_ca,
            seeds=seeds,
            opt_level_hw=opt_level_hw,
            opt_level_nct=opt_level_nct,
            export_raw=True, export_hw=True, export_nct=True
        )
        return res

# =========================================================
# 8) Print summary for comparison
# =========================================================
def _fmt_mmm(d: Dict[str, Optional[float]]) -> str:
    return f"min={d['min']:.0f}, med={d['med']:.0f}, max={d['max']:.0f}" if d["min"] is not None else "N/A"

def print_summary(res: Dict[str, Any]) -> None:
    print(f"\n=== {res['label']} | n={res['n']} m={res['m']} | bijective={res['bijective']} ===")
    a = res["anf"]
    print(f"ANF: total_terms={a['total_terms']} | max_deg={a['max_deg']} | hi_deg_terms(>=3)={a['hi_deg_terms']} | clean_work={res['clean_work']}")
    print(f"ANF per-bit terms: {a['per_bit_terms']}")
    print(f"ANF degree hist: {a['deg_hist']}")

    for mode in ["no_ancilla", "clean_ancilla"]:
        lg = res[mode]["logical"]
        hw = res[mode]["hw"]
        nct = res[mode]["nct"]
        exp = res[mode].get("export", None)

        print(f"\n[{mode}] RAW: width={lg['width_raw']} depth={lg['depth_raw']} | X={lg['x']} CX={lg['cx']} CCX={lg['ccx']} MCX~={lg['mcx_like']} total_ops={lg['total_ops']}")
        print(f"  HW  : width={hw['width']} | depth({_fmt_mmm(hw['depth'])}) | twoq_depth({_fmt_mmm(hw['twoq_depth'])}) | CX({_fmt_mmm(hw['cx'])}) | gates({_fmt_mmm(hw['gates_total'])})")

        if nct.get("available", False):
            print(f"  NCT : width={nct['width']} | CCX(Toffoli)({_fmt_mmm(nct['ccx'])}) | Toffoli-depth({_fmt_mmm(nct['toffoli_depth'])}) | CX({_fmt_mmm(nct['cx'])})")
        else:
            print("  NCT : unavailable (cannot transpile fully to {x,cx,ccx} for this circuit/version)")

        # if exp:
        #     print(f"  EXPORT: {exp}")
        #
        exps = res[mode].get("exports", {})
        if exps:
            print(f"  EXPORTS: RAW={exps.get('RAW')} | HW={exps.get('HW')} | NCT={exps.get('NCT')}")

def flatten_for_ranking(res: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Create a comparable vector using MEDIAN HW metrics (recommended for ranking)."""
    hw = res[mode]["hw"]
    vec = {
        "width": hw["width"],
        "depth_med": hw["depth"]["med"],
        "twoq_depth_med": hw["twoq_depth"]["med"],
        "cx_med": hw["cx"]["med"],
        "gates_med": hw["gates_total"]["med"],
        "anf_terms": res["anf"]["total_terms"],
        "max_deg": res["anf"]["max_deg"],
        "hi_deg_terms": res["anf"]["hi_deg_terms"],
    }
    return vec

def rank_all(results: List[Dict[str, Any]],
             mode: str,
             weights: Dict[str, float],
             topk: int = 10) -> None:
    rows = []
    for res in results:
        vec = flatten_for_ranking(res, mode)
        # Only include keys that exist and are numeric
        if any(vec[k] is None for k in vec.keys() if k.endswith("_med")):
            continue
        # Build score vector for objective
        obj_vec = {
            "width": float(vec["width"]),
            "depth_med": float(vec["depth_med"]),
            "twoq_depth_med": float(vec["twoq_depth_med"]),
            "cx_med": float(vec["cx_med"]),
            "gates_med": float(vec["gates_med"]),
        }
        score = objective_score(obj_vec, weights)
        rows.append((score, res["label"], obj_vec, vec))

    rows.sort(key=lambda x: x[0])
    print(f"\n=== RANKING ({mode}) by weighted objective ===")
    print("Weights:", weights)
    for i, (score, label, obj_vec, vec) in enumerate(rows[:topk], 1):
        print(f"{i:>2}. {label:>10} | score={score:.2f} | width={obj_vec['width']:.0f} depth={obj_vec['depth_med']:.0f} "
              f"twoq_depth={obj_vec['twoq_depth_med']:.0f} cx={obj_vec['cx_med']:.0f} gates={obj_vec['gates_med']:.0f} "
              f"| ANFterms={vec['anf_terms']} maxdeg={vec['max_deg']}")

def pareto_report(results: List[Dict[str, Any]],
                  mode: str,
                  pareto_keys: List[str]) -> None:
    items = []
    for res in results:
        vec = flatten_for_ranking(res, mode)
        # Build Pareto vector
        pvec = {}
        ok = True
        for k in pareto_keys:
            if k not in vec or vec[k] is None:
                ok = False
                break
            pvec[k] = float(vec[k])
        if ok:
            items.append({"label": res["label"], "vec": pvec})

    front = pareto_front(items, pareto_keys)
    print(f"\n=== PARETO FRONT ({mode}) on {pareto_keys} ===")
    for it in sorted(front, key=lambda t: tuple(t["vec"][k] for k in pareto_keys)):
        v = it["vec"]
        print(f"- {it['label']}: " + ", ".join([f"{k}={v[k]:.0f}" for k in pareto_keys]))

def export_csv(results: List[Dict[str, Any]], filename: str) -> None:
    """Export key MEDIAN HW metrics for both modes to CSV."""
    fields = [
        "label","n","m","bijective",
        "anf_total_terms","anf_max_deg","anf_hi_deg_terms","clean_work",
        "no_width","no_depth_med","no_twoq_depth_med","no_cx_med","no_gates_med",
        "ca_width","ca_depth_med","ca_twoq_depth_med","ca_cx_med","ca_gates_med",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for res in results:
            no = flatten_for_ranking(res, "no_ancilla")
            ca = flatten_for_ranking(res, "clean_ancilla")
            row = {
                "label": res["label"], "n": res["n"], "m": res["m"], "bijective": res["bijective"],
                "anf_total_terms": res["anf"]["total_terms"],
                "anf_max_deg": res["anf"]["max_deg"],
                "anf_hi_deg_terms": res["anf"]["hi_deg_terms"],
                "clean_work": res["clean_work"],
                "no_width": no["width"], "no_depth_med": no["depth_med"], "no_twoq_depth_med": no["twoq_depth_med"],
                "no_cx_med": no["cx_med"], "no_gates_med": no["gates_med"],
                "ca_width": ca["width"], "ca_depth_med": ca["depth_med"], "ca_twoq_depth_med": ca["twoq_depth_med"],
                "ca_cx_med": ca["cx_med"], "ca_gates_med": ca["gates_med"],
            }
            w.writerow(row)
    print(f"\n[CSV] exported: {filename}")





from typing import Iterable, Dict, Any, List
from qiskit import transpile

def _filter_non_gates(ops: Dict[str, int]) -> Dict[str, int]:
    """Loại các pseudo-ops không phải cổng thực (barrier, measure, ...)."""
    drop = {"barrier", "measure", "snapshot", "delay"}
    return {g: int(v) for g, v in ops.items() if g not in drop}

def hw_gate_breakdown_per_seed(
    qc,
    seeds: Iterable[int],
    opt_level: int = 2,
    basis_hw=("cx", "rz", "sx", "x", "h"),
) -> List[Dict[str, Any]]:
    """
    Trả về list các dòng breakdown theo từng seed sau transpile về basis_hw.
    Mỗi dòng có: depth, twoq_depth, count từng gate trong basis, total, other.
    """
    rows = []
    for sd in seeds:
        tqc = transpile(
            qc,
            basis_gates=list(basis_hw),
            optimization_level=int(opt_level),
            seed_transpiler=int(sd),
        )
        ops = _filter_non_gates(tqc.count_ops())

        row = {
            "seed": int(sd),
            "depth": int(tqc.depth()),
            "twoq_depth": int(layer_count_of_gate(tqc, {"cx"})),  # bạn đã có hàm này
        }
        # counts trong basis
        for g in basis_hw:
            row[g] = int(ops.get(g, 0))

        # phần còn lại (nếu transpile ra gate lạ)
        other = {g: int(v) for g, v in ops.items() if g not in set(basis_hw)}
        row["other"] = other
        row["total"] = int(sum(ops.values()))
        rows.append(row)
    return rows

def print_hw_gate_breakdown(
    qc,
    title: str,
    seeds: Iterable[int],
    opt_level: int = 2,
    basis_hw=("cx", "rz", "sx", "x", "h"),
) -> None:
    rows = hw_gate_breakdown_per_seed(qc, seeds, opt_level=opt_level, basis_hw=basis_hw)

    print(f"\n=== HW gate breakdown ({title}) | basis={list(basis_hw)} | opt_level={opt_level} ===")
    for r in rows:
        other_str = f" | other={r['other']}" if r["other"] else ""
        print(
            f" seed={r['seed']}: depth={r['depth']} twoq_depth={r['twoq_depth']} | "
            f"cx={r['cx']} rz={r['rz']} sx={r['sx']} x={r['x']} h={r['h']} | total={r['total']}"
            f"{other_str}"
        )

    # (tuỳ chọn) in min/med/max cho từng gate trong basis
    def _mmm(key: str):
        xs = [r[key] for r in rows]
        return agg_min_med_max(xs)  # bạn đã có hàm này

    print("  min/med/max:")
    for key in ["depth", "twoq_depth", "cx", "rz", "sx", "x", "h", "total"]:
        d = _mmm(key)
        print(f"   - {key:>10}: min={d['min']:.0f}, med={d['med']:.0f}, max={d['max']:.0f}")





# =========================================================
# 9) MAIN: put your S-box list here
# =========================================================
if __name__ == "__main__":
    # Compile robustness: choose multiple seeds for min/median/max.
    # For papers, 5–15 seeds is common. Start with 5 for speed.
    # ===== EXPORT CONFIG =====
    EXPORT = True

    # số "cột" gate tối đa mỗi dòng khi vẽ (Qiskit gọi là fold)
    fold = 45  # bạn muốn 16 cột thì dùng 16; 20 cột thì dùng 20

    # ép tất cả part cùng khung để LaTeX không phóng to part cuối
    # fixed_size = (40, 3.2)  # (width_inch, height_inch) - chỉnh theo số qubit/độ dày bạn thích

    dpi = 500
    SCALE = 1

    # seeds để lấy min/med/max (robustness)11
    seeds = [1, 2, 0, 4, 3]

    # Put S-boxes to compare (label, LUT list)
    sboxes = [
        # ("Sbox55", [16, 28, 1, 5, 26, 22, 10, 14, 21, 25, 4, 0, 29, 17, 13, 9, 2, 30, 19, 7, 8, 20, 24, 12, 3, 31, 18, 6, 11, 23, 27, 15]),
        # ("Sbox55", [10, 3, 11, 22, 17, 4,1, 8, 12, 28, 23, 18, 26, 6, 31, 20, 15, 24, 29, 13, 14, 19, 30, 5, 25, 27, 7, 0, 16, 21, 2,  9] )
         ("Sbox55", [8,19,30,7,6,25,16,13,22,15,3,24,17,12, 4,27,11,0,29,20,1,14,23,26,28,21,9,2,31,18,10,5]
         # [16, 18, 28, 8, 1, 13, 17, 11, 19, 24, 29, 0, 7, 2, 21, 6, 20, 4, 31, 25, 9, 23, 30, 22, 3, 26, 10, 5, 27, 12, 14, 15]
),
        # add more...
    ]

    results = []
    for label, S in sboxes:
        res = evaluate_sbox(S, label=label, seeds=seeds, export=True)
        print_summary(res)
        results.append(res)

    # Ranking settings (you can tune weights depending on what you care most)
    # Example: prioritize CX and depth, then width
    weights_no = {"cx_med": 1.0, "depth_med": 0.5, "twoq_depth_med": 0.5, "width": 0.2, "gates_med": 0.05}
    weights_ca = {"cx_med": 1.0, "depth_med": 0.5, "twoq_depth_med": 0.5, "width": 0.2, "gates_med": 0.05}

    rank_all(results, mode="no_ancilla", weights=weights_no, topk=10)
    rank_all(results, mode="clean_ancilla", weights=weights_ca, topk=10)

    # Pareto report (recommended for paper figures)
    pareto_report(results, mode="no_ancilla", pareto_keys=["width","depth_med","cx_med"])
    pareto_report(results, mode="clean_ancilla", pareto_keys=["width","depth_med","cx_med"])

    # Export a CSV you can paste into Excel / LaTeX table later
    # export_csv(results, "sbox_quantum_compare.csv")
