# -*- coding: utf-8 -*-
"""diag_boundary.py — CHẨN ĐOÁN read-only cổng boundary_mismatch. KHÔNG sửa spec/calib/thuật toán.
So float round3 vs Fraction exact membership TRÊN DB GỐC (chưa hiding) tại ξ operating vs ξ sweep."""
import os, sys, json
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"; os.execv(sys.executable, [sys.executable] + sys.argv)
import logging; logging.disable(logging.CRITICAL)
from fractions import Fraction
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
for d in ("hiding", "metrics", "mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))
sys.path.insert(0, os.path.join(ROOT, "calibration"))
from preprocess import load_transactions, load_weights
from common import HidingDB
import calibrate as CAL

DATA = os.path.join(ROOT, "datasets"); CALIB = os.path.join(ROOT, "calibration")
BAND = 0.0015


def audit(db, universe, xi, Wfrac):
    Wtot = Fraction(0); twf = {}
    for t, s in db.D.items():
        if not s: continue
        tw = sum(Wfrac.get(i, 0) for i in s) / len(s); twf[t] = tw; Wtot += tw
    xf = Fraction(str(xi)); nb = 0; nm = 0; ex = []
    for X in universe:
        r = round(float(db.ws(X)), 3)
        if abs(r - xi) <= BAND:
            nb += 1
            wf = (sum(twf[t] for t in db.cover(X)) / Wtot) if Wtot else Fraction(0)
            if (r >= xi) != (wf >= xf):
                nm += 1
                if len(ex) < 6:
                    ex.append((sorted(X), r, float(wf), (r >= xi), (wf >= xf)))
    return nb, nm, ex


def run(ds, mult, xi):
    tf, wf = {d[0]: (d[1], d[2]) for d in CAL.DATASETS}[ds]
    D = load_transactions(os.path.join(DATA, tf))
    Wf = load_weights(os.path.join(DATA, wf), 10, False)
    Wfrac = load_weights(os.path.join(DATA, wf), 10, True)
    if abs(mult - 1.0) < 1e-9:
        c = json.load(open(os.path.join(CALIB, f"calib_{ds}.json")))
        S = [frozenset(x) for x in c["sfwi"]]; fwi = [frozenset(x) for x in c["fwi"]]
    else:
        c = json.load(open(os.path.join(CALIB, f"sweep_frozen_{ds}_m{mult:.1f}.json")))
        S = [frozenset(x) for x in c["sfwi"]]; fwi = [frozenset(x) for x in c["fwi"]]
    NS = [x for x in fwi if x not in set(S)]
    db = HidingDB(D, Wf, track=S + NS)                       # DB GỐC, CHƯA hiding
    nb, nm, ex = audit(db, list(dict.fromkeys(S + NS)), xi, Wfrac)
    print(f"[{ds} m{mult} ξ={xi}] |FWI|={len(fwi)} DB-GỐC(chưa hiding): n_boundary={nb} n_mismatch={nm}")
    for it, r, wf_, fd, ed in ex:
        print(f"    X={''.join(it)[:40]} round3(ws)={r} exact_ws={wf_:.6f} float_freq={fd} exact_freq={ed}")


if __name__ == "__main__":
    run("chess_fimi", 1.0, 0.92)      # operating (calibrated) — kỳ vọng mismatch=0
    run("chess_fimi", 0.6, 0.552)     # sweep — cell đã chặn
    run("mushroom", 1.0, 0.457)
    run("mushroom", 0.4, 0.183)
