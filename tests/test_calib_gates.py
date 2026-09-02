# -*- coding: utf-8 -*-
"""
tests/test_calib_gates.py — Gates G-C1..G-C4 cho calibration (SPEC_CALIBRATION §VERIFY).

G-C1: 50 ≤ #FWI ≤ 300 ; #SFWI = clamp(round(0.1·#candidate), 10, 40).
G-C2: mọi SFWI có |X|≥2 ∧ ws>ξ (recompute exact Fraction).
G-C3: oracle maxlen>7 — mine cap cao hơn CAP, #FWI không đổi (0 FWI dài bị rớt); báo max len.
G-C4: determinism — chạy lại freeze+select 2 lần → cùng #FWI + cùng S.

Chạy trên các calib_<ds>.json ĐÃ có. Dataset lớn: G-C3/G-C4 (re-mine) chỉ chạy khi truyền tên
dataset làm arg (mặc định: chess_fimi, mushroom, retail để nhanh). G-C1/G-C2 chạy cho MỌI json.
Entry-guarded; exit != 0 nếu FAIL.
"""
import os
import sys
import json
import glob
import logging
from fractions import Fraction

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets")
CALIB = os.path.join(ROOT, "calibration")
for d in ("mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))
sys.path.insert(0, CALIB)

import miner                                                          # noqa: E402
from miner import mine_fwi, fwi_itemsets                             # noqa: E402
from preprocess import load_transactions, load_weights              # noqa: E402
from calibrate import freeze, select_sfwi, CAP                      # noqa: E402

REMINE_DEFAULT = {"chess_fimi", "mushroom", "retail"}
FILES = {"chess_fimi": ("chess_fimi_quantities.txt", "chess_fimi_weights.txt"),
         "mushroom": ("mushroom_quantities.txt", "mushroom_weights.txt"),
         "retail": ("retail_quantities.txt", "retail_weights.txt"),
         "accident": ("accident_quantities.txt", "accident_weights.txt"),
         "bms-pos": ("bms-pos_quantities.txt", "bms-pos_weights.txt"),
         "kosarak": ("kosarak_quantities.txt", "kosarak_weights.txt"),
         "chainstore": ("chainstore_quantities.txt", "chainstore_weights.txt")}


def _clamp(n_cand):
    return max(10, min(40, round(0.1 * n_cand)))


def _load(ds):
    tf, wf = FILES[ds]
    D = load_transactions(os.path.join(DATA, tf))
    Wf = load_weights(os.path.join(DATA, wf), 10, False)
    Wfrac = load_weights(os.path.join(DATA, wf), 10, True)
    return D, Wf, Wfrac


def check(ds, rec, remine):
    xi = rec["xi"]
    xi_frac = Fraction(str(xi))
    ok = True

    # G-C1
    gc1 = (50 <= rec["n_fwi"] <= 300) and (rec["n_sfwi"] == _clamp(rec["n_candidate"]))
    ok &= gc1

    # G-C2 (recompute exact ws cho SFWI) + G-C3/G-C4 nếu remine
    D, Wf, Wfrac = _load(ds)
    sfwi = [frozenset(x) for x in rec["sfwi"]]
    # exact ws cho từng SFWI (targeted inv)
    freq = set().union(*sfwi) if sfwi else set()
    Wtot = Fraction(0); tw = {}; inv = {i: set() for i in freq}
    for t, s in D.items():
        if not s:
            continue
        twt = sum(Wfrac.get(i, 0) for i in s) / len(s)
        Wtot += twt
        it = s & freq
        if it:
            tw[t] = twt
            for i in it:
                inv[i].add(t)

    def ws(X):
        cov = set.intersection(*(inv[i] for i in X))
        return sum(tw[t] for t in cov) / Wtot

    gc2 = all(len(X) >= 2 and ws(X) > xi_frac for X in sfwi)
    ok &= gc2

    # G-C3 (cheap, rigorous cho MỌI dataset): max|X| trong FWI đã freeze < CAP ⇒ cap KHÔNG cắt
    # (nếu itemset dài nhất < cap thì miner dừng tự nhiên, không bị maxlen chặn ⇒ 0 FWI dài bị rớt).
    maxlen_frozen = max((len(x) for x in rec["fwi"]), default=0)
    gc3 = maxlen_frozen < CAP
    ok &= gc3
    print(f"[{ds}] G-C1 #FWI={rec['n_fwi']}∈[50,300] & #SFWI={rec['n_sfwi']}==clamp({rec['n_candidate']})"
          f"={_clamp(rec['n_candidate'])} → {gc1} ; G-C2 |X|≥2∧ws>ξ → {gc2} ; "
          f"G-C3 max|X|(fwi)={maxlen_frozen}<CAP={CAP} → {gc3}")

    if remine:
        # G-C3: mine cap cao hơn → #FWI không đổi (0 FWI dài rớt)
        hi = CAP + 10
        miner.config.MAX_PATTERN_LENGTH = hi
        sets_hi = fwi_itemsets(mine_fwi(D, Wf, xi))
        miner.config.MAX_PATTERN_LENGTH = CAP
        maxlen = max((len(x) for x in sets_hi), default=0)
        gc3b = (len(sets_hi) == rec["n_fwi"])
        ok &= gc3b
        print(f"[{ds}] G-C3+ re-mine cap={hi}: #FWI={len(sets_hi)} == frozen {rec['n_fwi']} → {gc3b} "
              f"(max|X|={maxlen})")

        # G-C4: freeze+select lại 2 lần → cùng kết quả
        nodes = mine_fwi(D, Wf, xi)
        its = [n.itemset for n in nodes]
        f1, _ = freeze(D, Wfrac, xi_frac, its)
        s1, c1, k1 = select_sfwi(f1, xi_frac)
        f2, _ = freeze(D, Wfrac, xi_frac, its)
        s2, c2, k2 = select_sfwi(f2, xi_frac)
        norm = lambda S: sorted(tuple(sorted(X)) for X in S)
        gc4 = (norm(s1) == norm(s2) and c1 == c2 and k1 == k2
               and norm(s1) == norm(sfwi) and len(f1) == rec["n_fwi"])
        ok &= gc4
        print(f"[{ds}] G-C4 determinism (2×) & khớp json: {gc4}")
    return ok


def main(argv):
    remine_set = set(argv[1:]) if len(argv) > 1 else REMINE_DEFAULT
    files = sorted(glob.glob(os.path.join(CALIB, "calib_*.json")))
    if not files:
        print("Không có calib_*.json"); return False
    allok = True
    for fp in files:
        rec = json.load(open(fp))
        ds = rec["dataset"]
        allok &= check(ds, rec, remine=(ds in remine_set))
    print("\nCALIB gates", "PASS" if allok else "FAIL")
    return allok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv) else 1)
