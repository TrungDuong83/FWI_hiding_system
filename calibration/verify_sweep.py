# -*- coding: utf-8 -*-
"""verify_sweep.py — G-SW2/G-SW3/G-SW4 cho sweep_grid.json. Entry-guarded, exit≠0 nếu FAIL."""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import calibrate as C
from fractions import Fraction

MULTS = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
grid = json.load(open(os.path.join(HERE, "sweep_grid.json")))
DS = [d[0] for d in C.DATASETS]


def clamp_formula(n_cand):
    return min(max(10, min(40, round(0.1 * n_cand))), n_cand)


ok_all = True

# -------- G-SW2: ok points → n_sfwi = clamp(round(0.1·n_cand),10,40) capped n_cand --------
print("----- G-SW2: n_sfwi formula (ok points) -----")
g2 = True
for ds in DS:
    for p in grid[ds]:
        if p["feasible"] != "ok":
            continue
        exp = clamp_formula(p["n_candidate"])
        good = p["n_sfwi"] == exp
        g2 &= good
        if not good:
            print(f"  FAIL {ds} mult={p['mult']}: n_sfwi={p['n_sfwi']} != clamp({p['n_candidate']})={exp}")
print(f"G-SW2 {'PASS' if g2 else 'FAIL'} (n_sfwi khớp clamp; |X|≥2∧ws>ξ đảm bảo bởi tái dùng select_sfwi/freeze)")
ok_all &= g2

# -------- G-SW3: classification đúng định nghĩa --------
print("----- G-SW3: phân loại ceiling/floor/ok -----")
g3 = True
for ds in DS:
    for p in grid[ds]:
        f, xi, nf = p["feasible"], p["xi"], p["n_fwi"]
        if f == "ceiling":
            good = (xi >= 1.0) or (nf is not None and nf < 10)
        elif f == "floor":
            good = ("time" in p["reason"] or "min" in p["reason"]
                    or "OOM" in p["reason"] or "monoton" in p["reason"] or "killed" in p["reason"])
        elif f == "ok":
            good = (xi < 1.0) and (nf is not None and nf >= 10)
        else:
            good = False
        g3 &= good
        if not good:
            print(f"  FAIL {ds} mult={p['mult']} feasible={f} xi={xi} n_fwi={nf} reason={p['reason']}")
print(f"G-SW3 {'PASS' if g3 else 'FAIL'}")
ok_all &= g3

# -------- G-SW4: determinism (re-mine 2 điểm rẻ, đếm 2× khớp) --------
print("----- G-SW4: determinism (re-mine 2×) -----")
from preprocess import load_transactions, load_weights
g4 = True
checks = [("mushroom", 1.2), ("chess_fimi", 0.8)]     # rẻ, có #FWI đáng kể
for ds, mult in checks:
    tf, wf = {d[0]: (d[1], d[2]) for d in C.DATASETS}[ds]
    xi_std = json.load(open(os.path.join(HERE, f"calib_{ds}.json")))["xi"]
    xi = round(mult * xi_std, 3)
    D = load_transactions(os.path.join(C.DATA, tf))
    Wf = load_weights(os.path.join(C.DATA, wf), normalize=10, use_fraction=False)
    n1 = len(C.mine_fwi(D, Wf, xi))
    n2 = len(C.mine_fwi(D, Wf, xi))
    stored = next(p["n_fwi"] for p in grid[ds] if abs(p["mult"] - mult) < 1e-9)
    good = (n1 == n2 == stored)
    g4 &= good
    print(f"  {ds} mult={mult} xi={xi}: n1={n1} n2={n2} stored={stored} → {'OK' if good else 'FAIL'}")
print(f"G-SW4 {'PASS' if g4 else 'FAIL'}")
ok_all &= g4

print(f"\nSWEEP VERIFY {'PASS' if ok_all else 'FAIL'} (G-SW2/3/4)")
sys.exit(0 if ok_all else 1)
