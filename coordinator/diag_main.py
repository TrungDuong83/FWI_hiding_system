# -*- coding: utf-8 -*-
"""diag_main.py — CHẨN ĐOÁN read-only: MAIN cell (ξ calibrated, mult=1.0) SAU hiding có boundary
mismatch không? Xác định blast-radius của cổng round3. Tái dùng run_coordinator (KHÔNG sửa)."""
import os, sys
os.environ["PYTHONHASHSEED"] = "0"
import importlib.util, logging
logging.disable(logging.CRITICAL)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("rc", os.path.join(HERE, "run_coordinator.py"))
RC = importlib.util.module_from_spec(spec); spec.loader.exec_module(RC)
from preprocess import load_transactions, load_weights
from common import HidingDB

CASES = [("chess_fimi", 1.0, 0.92), ("mushroom", 1.0, 0.457), ("retail", 1.0, 0.008)]
for ds, mult, xi in CASES:
    tf, wf = RC.DS_FILES[ds]
    D = load_transactions(os.path.join(RC.DATA, tf))
    Wf = load_weights(os.path.join(RC.DATA, wf), 10, False)
    Wfrac = load_weights(os.path.join(RC.DATA, wf), 10, True)
    S, fwi = RC.get_frozen(ds, mult, xi, D, Wf, Wfrac)
    NS = [x for x in fwi if x not in set(S)]
    for method in RC.METHODS:
        db = HidingDB(D, Wf, track=S + NS)
        rt, status, n_del, n_sblk = RC.run_hiding(method, db, S, NS, xi)
        nb, nbm = RC.boundary_audit(db, list(dict.fromkeys(S + NS)), xi, Wfrac)
        print(f"[{ds} m{mult} {method}] status={status} n_del={n_del} n_boundary={nb} "
              f"n_boundary_mismatch={nbm}", flush=True)
