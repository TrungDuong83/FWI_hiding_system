# -*- coding: utf-8 -*-
"""
tests/test_gmemb.py — G-MEMB: membership `ws ≥ ξ` float64 == exact Fraction (KHÔNG round3).

Chứng minh fix control 2026-09 (bỏ round3):
 (1) chess m1.0 (ξ operating, 5 method): HF/MC tính bằng float `ws≥ξ` == HF/MC exact Fraction trên
     TOÀN universe S∪~S; boundary_audit n_mismatch=0. MCP-safe: MC=0 theo CẢ float VÀ exact.
 (2) chess m0.6 (ξ sweep, HFPriority): ca cũ fire n_boundary_mismatch=1184 với round3 → nay = 0.
Entry-guarded; exit≠0 nếu FAIL.
"""
import os
import sys
os.environ["PYTHONHASHSEED"] = "0"
import logging
logging.disable(logging.CRITICAL)
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
import importlib.util
spec = importlib.util.spec_from_file_location("rc", os.path.join(ROOT, "coordinator", "run_coordinator.py"))
RC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RC)
from preprocess import load_transactions, load_weights
from common import HidingDB
from metrics import hiding_failure, missing_cost


def exact_ws_fn(db, Wfrac):
    Wtot = Fraction(0)
    twf = {}
    for t, s in db.D.items():
        if not s:
            continue
        tw = sum(Wfrac.get(i, 0) for i in s) / len(s)
        twf[t] = tw
        Wtot += tw

    def wsf(X):
        return (sum(twf[t] for t in db.cover(X)) / Wtot) if Wtot else Fraction(0)
    return wsf


ok_all = True


def check_full(ds, mult, xi, methods):
    global ok_all
    tf, wf = RC.DS_FILES[ds]
    D = load_transactions(os.path.join(RC.DATA, tf))
    Wf = load_weights(os.path.join(RC.DATA, wf), 10, False)
    Wfrac = load_weights(os.path.join(RC.DATA, wf), 10, True)
    S, fwi = RC.get_frozen(ds, mult, xi, D, Wf, Wfrac)
    NS = [x for x in fwi if x not in set(S)]
    xf = Fraction(str(xi))
    for method in methods:
        db = HidingDB(D, Wf, track=S + NS)
        RC.run_hiding(method, db, S, NS, xi)
        # float metric
        hf_f = float(hiding_failure(db, S, xi))
        mc_f = float(missing_cost(db, NS, xi))
        # exact metric (toàn universe)
        wsf = exact_ws_fn(db, Wfrac)
        hf_e = (sum(1 for s in S if wsf(s) >= xf) / len(S)) if S else 0.0
        mc_e = (sum(1 for ns in NS if not (wsf(ns) >= xf)) / len(NS)) if NS else 0.0
        # full-universe decision mismatch
        full_mm = sum(1 for X in (S + NS) if (float(db.ws(X)) >= xi) != (wsf(X) >= xf))
        nb, nbm = RC.boundary_audit(db, list(dict.fromkeys(S + NS)), xi, Wfrac)
        hf_match = abs(hf_f - hf_e) < 1e-12
        mc_match = abs(mc_f - mc_e) < 1e-12
        mcp_mc0 = True
        if method == "MCPriority_safeT":
            mcp_mc0 = (mc_f == 0.0) and (mc_e == 0.0)
        good = hf_match and mc_match and full_mm == 0 and nbm == 0 and mcp_mc0
        ok_all &= good
        print(f"[{ds} m{mult} {method}] HF float={hf_f:.6f} exact={hf_e:.6f}({hf_match}) "
              f"MC float={mc_f:.6f} exact={mc_e:.6f}({mc_match}) full_mismatch={full_mm} "
              f"n_boundary={nb} n_boundary_mismatch={nbm} "
              f"{'MCP_MC0='+str(mcp_mc0)+' ' if method=='MCPriority_safeT' else ''}→ {'OK' if good else 'FAIL'}")


def check_boundary(ds, mult, xi, method):
    global ok_all
    tf, wf = RC.DS_FILES[ds]
    D = load_transactions(os.path.join(RC.DATA, tf))
    Wf = load_weights(os.path.join(RC.DATA, wf), 10, False)
    Wfrac = load_weights(os.path.join(RC.DATA, wf), 10, True)
    S, fwi = RC.get_frozen(ds, mult, xi, D, Wf, Wfrac)
    NS = [x for x in fwi if x not in set(S)]
    db = HidingDB(D, Wf, track=S + NS)
    RC.run_hiding(method, db, S, NS, xi)
    nb, nbm = RC.boundary_audit(db, list(dict.fromkeys(S + NS)), xi, Wfrac)
    good = nbm == 0
    ok_all &= good
    print(f"[{ds} m{mult} {method}] (ca round3 cũ fire 1184) n_boundary={nb} "
          f"n_boundary_mismatch={nbm} → {'OK' if good else 'FAIL'}")


if __name__ == "__main__":
    check_full("chess_fimi", 1.0, 0.92, RC.METHODS)
    check_boundary("chess_fimi", 0.6, 0.552, "HFPriority")
    print("\nG-MEMB", "PASS" if ok_all else "FAIL")
    sys.exit(0 if ok_all else 1)
