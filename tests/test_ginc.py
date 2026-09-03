# -*- coding: utf-8 -*-
"""
tests/test_ginc.py — Gates cho Safe/ws INCREMENTAL (num_cache, SPEC §3.3).

G-INC1 parity incremental↔oracle: trên golden + Safe fixture, chạy CÓ track (num_cache O(1)) vs
        KHÔNG track (oracle O(cover)) → trace + HF/MC + tập lost/residual KHỚP CHÍNH XÁC (Fraction).
        + kiểm bất biến num_cache[X] == Σ_{T⊇X} tw(T) sau khi hiding.
G-INC2 float-drift ở quy mô: MCP-safe trên chess_fimi với num_cache FRACTION (exact) vs FLOAT64+round3
        → HF/MC/AC + lost/residual khớp. Lệch ⇒ phải dùng Fraction num_cache (báo).
G-INC3 determinism: MCP-safe chess_fimi float 2× → HF/MC/AC + n_deletions y hệt (PYTHONHASHSEED=0).
Entry-guarded; exit != 0 nếu FAIL.
"""
import os
import sys
import json
import logging
from fractions import Fraction as F

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets")
CALIB = os.path.join(ROOT, "calibration")
for d in ("hiding", "metrics", "mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))

from common import HidingDB                                              # noqa: E402
from hfpriority import hfpriority                                        # noqa: E402
from mcpriority import mcpriority, is_safe                              # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
from miner import mine_fwi, fwi_itemsets                                # noqa: E402
from preprocess import load_transactions, load_weights                  # noqa: E402

# ---- Running example ----
W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
XI = F(55, 100)
S = [frozenset("AC"), frozenset("CE")]
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]
Wf = {k: float(v) for k, v in W.items()}


def _run(kind, track_on, Wb, xi, r3):
    track = (list(S) + list(NS)) if track_on else None
    db = HidingDB(D, Wb, track=track)
    if kind == "hfp":
        tr = hfpriority(db, S, xi, round3=r3)
    elif kind == "safeT":
        tr = mcpriority(db, S, NS, xi, safe_check=True, order="mc_tid", round3=r3)
    else:
        tr = mcpriority(db, S, NS, xi, safe_check=False, order="mc_tid", round3=r3)
    hf = hiding_failure(db, S, xi, round3=r3)
    mc = missing_cost(db, NS, xi, round3=r3)
    lost = sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), xi, r3))
    resid = sorted("".join(sorted(s)) for s in S if is_frequent(db.ws(s), xi, r3))
    return [f"{v}@{t}" for v, t in tr], hf, mc, lost, resid, db


def test_ginc1():
    ok = True
    for kind in ("hfp", "safeT", "safeF"):
        a = _run(kind, False, W, XI, False)      # oracle (no track), Fraction exact
        b = _run(kind, True, W, XI, False)       # incremental (track), Fraction exact
        same = a[:5] == b[:5]
        ok &= same
        print(f"[G-INC1 {kind}] trace/HF/MC/lost/resid oracle==incremental: {same} "
              f"(trace={' -> '.join(b[0])} HF={b[1]} MC={b[2]})")
    # num_cache invariant sau hiding (safeT incremental db)
    db = _run("safeT", True, W, XI, False)[5]
    inv_ok = all(db.num_cache[X] == sum(db.tw_cache[t] for t in db.cover(X)) for X in db._tracked)
    ok &= inv_ok
    print(f"[G-INC1] num_cache[X]==Σtw(T⊇X) ∀ tracked X: {inv_ok}")
    # Safe fixture: is_safe track vs no-track (full=False)
    Wfx = {"A": F(2, 5), "B": F(1, 10), "C": F(4, 5), "D": F(2, 5)}
    Dfx = {"T1": set("AB"), "T2": set("BD"), "T3": set("ABC")}
    xf = F(11, 25)
    NSf = [frozenset(x) for x in ["A", "AB", "AC", "B", "BC", "C"]]
    db0 = HidingDB(Dfx, Wfx)
    db1 = HidingDB(Dfx, Wfx, track=NSf)
    s0 = is_safe(db0, "B", "T2", NSf, xf)
    s1 = is_safe(db1, "B", "T2", NSf, xf)
    fx_ok = (s0 == s1 is False)
    ok &= fx_ok
    print(f"[G-INC1 safe-fixture] is_safe oracle={s0} incremental={s1} (exp both False): {fx_ok}")
    print("G-INC1", "PASS" if ok else "FAIL")
    return ok


def _chess_run(fraction, r3):
    calib = json.load(open(os.path.join(CALIB, "calib_chess_fimi.json")))
    xi = F(str(calib["xi"])) if fraction else calib["xi"]
    Sc = [frozenset(x) for x in calib["sfwi"]]
    fwi = [frozenset(x) for x in calib["fwi"]]
    Sset = set(Sc)
    NSc = [x for x in fwi if x not in Sset]
    Dc = load_transactions(os.path.join(DATA, "chess_fimi_quantities.txt"))
    Wc = load_weights(os.path.join(DATA, "chess_fimi_weights.txt"), 10, use_fraction=fraction)
    db = HidingDB(Dc, Wc, track=Sc + NSc)
    tr = mcpriority(db, Sc, NSc, xi, safe_check=True, order="mc_tid", round3=r3)
    hf = hiding_failure(db, Sc, xi, round3=r3)
    mc = missing_cost(db, NSc, xi, round3=r3)
    Wcf = load_weights(os.path.join(DATA, "chess_fimi_weights.txt"), 10, use_fraction=False)
    fwi_orig = set(fwi)
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wcf, calib["xi"]))
    ac = artificial_cost(fwi_orig, fwi_san)
    lost = sorted("".join(sorted(ns)) for ns in NSc if not is_frequent(db.ws(ns), xi, r3))
    resid = sorted("".join(sorted(s)) for s in Sc if is_frequent(db.ws(s), xi, r3))
    return (float(hf), float(mc), float(ac), lost, resid, len(tr))


def test_ginc2():
    frac = _chess_run(fraction=True, r3=False)      # num_cache Fraction, exact
    flo = _chess_run(fraction=False, r3=True)        # num_cache float64 + round3
    same = frac[:5] == flo[:5]                        # HF/MC/AC + lost/resid
    print(f"[G-INC2 chess] Fraction HF/MC/AC={frac[:3]} lost={len(frac[3])} resid={frac[4]}")
    print(f"[G-INC2 chess] float+r3 HF/MC/AC={flo[:3]} lost={len(flo[3])} resid={flo[4]}")
    print(f"[G-INC2] Fraction==float64+round3 (HF/MC/AC/lost/resid): {same} -> numcache={'float' if same else 'FRACTION-required'}")
    print("G-INC2", "PASS" if same else "FAIL")
    return same, ("float" if same else "fraction")


def test_ginc3():
    r1 = _chess_run(fraction=False, r3=True)
    r2 = _chess_run(fraction=False, r3=True)
    same = r1 == r2                                   # HF/MC/AC/lost/resid + n_deletions
    print(f"[G-INC3 chess] run1==run2 (HF/MC/AC/lost/resid/n_del): {same} "
          f"(HF={r1[0]} MC={r1[1]} AC={r1[2]} n_del={r1[5]})")
    print("G-INC3", "PASS" if same else "FAIL")
    return same


def main():
    g1 = test_ginc1()
    g2, numcache = test_ginc2()
    g3 = test_ginc3()
    allok = g1 and g2 and g3
    print(f"\nG-INC {'PASS' if allok else 'FAIL'} (num_cache dtype cho hiding = {numcache})")
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
