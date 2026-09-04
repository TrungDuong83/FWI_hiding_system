# -*- coding: utf-8 -*-
"""diag_drift.py — CHẨN ĐOÁN read-only: mismatch sau hiding do num_cache incremental (float drift)?
So 3 ws cho itemset ở biên SAU khi chạy HFPriority chess m0.6:
  (a) incremental = db.ws(X) [num_cache float, incremental qua deletions]
  (b) fresh_float = Σ tw_cache[t]/W_total tính lại trực tiếp (KHÔNG qua num_cache)
  (c) exact       = Fraction ws tính lại từ db.D
Nếu round3(a) lệch (c) NHƯNG round3(b) khớp (c) ⇒ root cause = trôi số num_cache incremental.
KHÔNG sửa spec/calib/thuật toán."""
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
from hfpriority import hfpriority
from select_victim import score_hfp
DATA = os.path.join(ROOT, "datasets"); CALIB = os.path.join(ROOT, "calibration")
BAND = 0.0015; XI = 0.552

c = json.load(open(os.path.join(CALIB, "sweep_frozen_chess_fimi_m0.6.json")))
S = [frozenset(x) for x in c["sfwi"]]; fwi = [frozenset(x) for x in c["fwi"]]
NS = [x for x in fwi if x not in set(S)]
D = load_transactions(os.path.join(DATA, "chess_fimi_quantities.txt"))
Wf = load_weights(os.path.join(DATA, "chess_fimi_weights.txt"), 10, False)
Wfrac = load_weights(os.path.join(DATA, "chess_fimi_weights.txt"), 10, True)
db = HidingDB(D, Wf, track=S + NS)
print(f"build ok |track|={len(S)+len(NS)}; run HFPriority…", flush=True)
hfpriority(db, S, XI, score=score_hfp(S, db.W), round3=True)
print("hiding done; auditing 3-way…", flush=True)

# fresh W_total + tw exact
Wtot = Fraction(0); twf = {}
for t, s in db.D.items():
    if not s: continue
    tw = sum(Wfrac.get(i, 0) for i in s) / len(s); twf[t] = tw; Wtot += tw
Wtot_f = sum(db.tw_cache.values())          # fresh float W_total
xf = Fraction(str(XI))
nb = mm_incr = mm_fresh = 0
ex = []
for X in list(dict.fromkeys(S + NS)):
    a = db.ws(X)                                          # incremental num_cache float
    r_a = round(float(a), 3)
    if abs(r_a - XI) <= BAND:
        nb += 1
        cov = db.cover(X)
        b = sum(db.tw_cache[t] for t in cov) / Wtot_f     # fresh float
        r_b = round(float(b), 3)
        cexact = (sum(twf[t] for t in cov) / Wtot) if Wtot else Fraction(0)
        exact_freq = (cexact >= xf)
        if (r_a >= XI) != exact_freq:
            mm_incr += 1
            if len(ex) < 8:
                ex.append((r_a, r_b, float(cexact)))
        if (r_b >= XI) != exact_freq:
            mm_fresh += 1
print(f"n_boundary={nb}  mismatch_INCREMENTAL(num_cache)={mm_incr}  mismatch_FRESH_float={mm_fresh}", flush=True)
print("examples [round3(incremental), round3(fresh_float), exact_ws]:", flush=True)
for a, b, e in ex:
    print(f"    incr={a} fresh={b} exact={e:.7f}", flush=True)
