# -*- coding: utf-8 -*-
"""
calibration/calibrate.py — calibrate ξ + freeze SFWI cho 7 dataset (SPEC_CALIBRATION.md).

RULE (đã chốt):
- #FWI ∈ [50,300]: sweep ξ giảm dần từ điểm tham khảo cao, chọn ξ NHỎ NHẤT cho #FWI vào dải; ξ ≤3dp.
- candidate = FWI {|X|≥2 ∧ ws>ξ}. overlap_score(X)=Σ_{i∈X} pop(i), pop(i)=#candidate chứa i
  ("độ phổ biến item trong không gian NSFWI, NSCov-based" — đọc không-vòng-lặp: trên tập candidate,
   vì S chưa chọn). Xếp giảm (tie: ws desc → lexicographic) → top clamp(round(0.1·#cand),10,40) = S.
- Backend freeze = Fraction (exact): ws tính lại chính xác trên itemset đã mine (targeted inverted
  index, không dựng full-DB), ngưỡng ws≥ξ / ws>ξ exact.
- Oracle maxlen>7: mine với cap cao để chắc không rớt FWI dài.
- weight /10, seed=42, deterministic.

REUSE: miner.mine_fwi (Đợt A, đã vá; KHÔNG sửa) cho sweep #FWI (float, nhanh). preprocess loader.
Checkpoint: mỗi dataset ghi calibration/calib_<ds>.json; resume skip nếu đã có.
Entry-guarded.
"""
import os
import sys
import json
import time
import logging
from fractions import Fraction
from decimal import Decimal

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets")
OUTDIR = HERE
for d in ("mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))

import miner                                                        # noqa: E402
from miner import mine_fwi, fwi_itemsets                            # noqa: E402
from preprocess import load_transactions, load_weights             # noqa: E402

SEED = 42
FWI_LO, FWI_HI = 50, 300
CAP = 20                        # maxlen cho sweep+freeze (>7); G-C3 kiểm cap cao hơn
miner.config.MAX_PATTERN_LENGTH = CAP

DATASETS = [                    # fast → slow (SPEC §6: tuần tự, checkpoint)
    ("chess_fimi", "chess_fimi_quantities.txt", "chess_fimi_weights.txt", "0.950"),
    ("mushroom",   "mushroom_quantities.txt",   "mushroom_weights.txt",   "0.800"),
    ("retail",     "retail_quantities.txt",     "retail_weights.txt",     "0.100"),
    ("accident",   "accident_quantities.txt",   "accident_weights.txt",   "0.950"),
    ("bms-pos",    "bms-pos_quantities.txt",    "bms-pos_weights.txt",    "0.100"),
    ("kosarak",    "kosarak_quantities.txt",    "kosarak_weights.txt",    "0.100"),
    ("chainstore", "chainstore_quantities.txt", "chainstore_weights.txt", "0.100"),
]


# --------------------------------- sweep #FWI (engine float) ---------------------------------
def count_fwi(D_sets, Wf, xi_float, cache):
    if xi_float in cache:
        return cache[xi_float]
    t0 = time.perf_counter()
    n = len(mine_fwi(D_sets, Wf, xi_float))
    cache[xi_float] = n
    print(f"      mine ξ={xi_float:.3f} → #FWI={n}  ({time.perf_counter()-t0:.1f}s)", flush=True)
    return n


def find_xi(D_sets, Wf, start):
    """
    Tìm ξ NHỎ NHẤT (grid 0.001) với #FWI ≤ 300 (= biên thấp của dải [50,300]; #FWI đơn điệu
    giảm theo ξ). Binary search trên grid trong bracket coarse → ít mine hơn linear (an toàn cho
    dataset lớn). Trả (ξ, #FWI).
    """
    cache = {}
    Q = Decimal("0.001")

    def g(x):
        return count_fwi(D_sets, Wf, float(x), cache)

    # U: ξ có g(U) ≤ HI (tăng coarse từ start nếu start quá dày)
    U = Decimal(start)
    while g(U) > FWI_HI and U + Decimal("0.05") <= Decimal("0.999"):
        U += Decimal("0.05")
    # Bracket đa-mức (0.05→0.01→0.001): descend từ hi, dừng khi g>HI (không mine tuyến tính ở ξ thấp).
    hi, lo = U, None
    for step in (Decimal("0.05"), Decimal("0.01"), Decimal("0.001")):
        x = hi
        while x - step > 0:
            x -= step
            if g(x) > FWI_HI:
                lo = x
                break
            hi = x
        if lo is not None:
            break
    if lo is None:
        return hi, g(hi)                     # ngay ξ thấp nhất (~0.001) vẫn ≤HI
    # binary search grid (lo, hi]: g(lo)>HI, g(hi)≤HI → ξ* = ξ NHỎ NHẤT với g≤HI
    while hi - lo > Q:
        mid = ((lo + hi) / 2).quantize(Q)
        if mid <= lo:
            mid = lo + Q
        if mid >= hi:
            mid = hi - Q
        if g(mid) <= FWI_HI:
            hi = mid
        else:
            lo = mid
    return hi, g(hi)


# --------------------------------- freeze exact (Fraction) ---------------------------------
def freeze(D_sets, Wfrac, xi_frac, itemsets):
    """Tính ws exact (Fraction) cho mọi itemset đã mine; re-filter ws≥ξ. targeted inverted index."""
    freq_items = set().union(*itemsets) if itemsets else set()
    Wtot = Fraction(0)
    tw_need = {}
    inv = {i: set() for i in freq_items}
    for t, s in D_sets.items():
        if not s:
            continue
        twt = sum(Wfrac.get(i, 0) for i in s) / len(s)
        Wtot += twt
        inter = s & freq_items
        if inter:
            tw_need[t] = twt
            for i in inter:
                inv[i].add(t)

    def ws(X):
        cov = set.intersection(*(inv[i] for i in X))
        return sum(tw_need[t] for t in cov) / Wtot

    out = []
    for X in itemsets:
        w = ws(X)
        if w >= xi_frac:                       # exact membership
            out.append((frozenset(X), w))
    return out, Wtot


def _idkey(v):
    return int(v) if (isinstance(v, str) and v.isdigit()) else v


def select_sfwi(fwi_ws, xi_frac):
    """candidate=|X|≥2 ∧ ws>ξ; overlap=Σ pop(i) (pop=#candidate chứa i); top clamp(round(0.1·#cand),10,40)."""
    candidates = [(X, w) for (X, w) in fwi_ws if len(X) >= 2 and w > xi_frac]
    pop = {}
    for X, _ in candidates:
        for i in X:
            pop[i] = pop.get(i, 0) + 1

    def owt(X):
        return sum(pop[i] for i in X)

    def lexkey(X):
        return tuple(sorted(X, key=_idkey))

    ranked = sorted(candidates, key=lambda xw: (-owt(xw[0]), -xw[1], lexkey(xw[0])))
    n_sfwi = max(10, min(40, round(0.1 * len(candidates))))
    n_sfwi = min(n_sfwi, len(candidates))     # không vượt số candidate
    S = [X for (X, _) in ranked[:n_sfwi]]
    return S, len(candidates), n_sfwi


def _itemset_list(itemsets):
    return sorted((sorted(X, key=_idkey) for X in itemsets), key=lambda z: (len(z), [_idkey(i) for i in z]))


def calibrate_one(ds, tfile, wfile, start):
    out_path = os.path.join(OUTDIR, f"calib_{ds}.json")
    if os.path.exists(out_path):
        print(f"[{ds}] SKIP (đã có {os.path.basename(out_path)})", flush=True)
        return json.load(open(out_path))
    print(f"[{ds}] load…", flush=True)
    t0 = time.perf_counter()
    D = load_transactions(os.path.join(DATA, tfile))
    Wf = load_weights(os.path.join(DATA, wfile), normalize=10, use_fraction=False)
    Wfrac = load_weights(os.path.join(DATA, wfile), normalize=10, use_fraction=True)
    print(f"[{ds}] |D|={len(D)} |W|={len(Wf)} ({time.perf_counter()-t0:.1f}s). Sweep ξ…", flush=True)

    xi, n_engine = find_xi(D, Wf, start)
    xi_float = float(xi)
    xi_frac = Fraction(xi)                                 # 3dp Decimal → Fraction exact
    print(f"[{ds}] chọn ξ={xi} (#FWI engine={n_engine}). Freeze exact…", flush=True)

    nodes = mine_fwi(D, Wf, xi_float)
    itemsets = [n.itemset for n in nodes]
    fwi_ws, Wtot = freeze(D, Wfrac, xi_frac, itemsets)
    S, n_cand, n_sfwi = select_sfwi(fwi_ws, xi_frac)

    rec = {
        "dataset": ds,
        "xi": float(xi),
        "n_fwi": len(fwi_ws),
        "n_sfwi": n_sfwi,
        "n_candidate": n_cand,
        "fwi": _itemset_list([X for X, _ in fwi_ws]),
        "sfwi": _itemset_list(S),
    }
    with open(out_path, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"[{ds}] FROZEN ξ={float(xi):.3f} #FWI={rec['n_fwi']} #cand={n_cand} #SFWI={n_sfwi} "
          f"({time.perf_counter()-t0:.1f}s) → {os.path.basename(out_path)}", flush=True)
    return rec


def main(argv):
    want = argv[1:] if len(argv) > 1 else [d[0] for d in DATASETS]
    done = []
    for ds, tf, wf, start in DATASETS:
        if ds not in want:
            continue
        rec = calibrate_one(ds, tf, wf, start)
        done.append(rec)
    print("\nCALIBRATE:", " ".join(f"{r['dataset']}=ξ{r['xi']:.3f}(#FWI{r['n_fwi']}/#SFWI{r['n_sfwi']})" for r in done), flush=True)


if __name__ == "__main__":
    main(sys.argv)
