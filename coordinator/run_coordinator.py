# -*- coding: utf-8 -*-
"""
coordinator/run_coordinator.py — §V MAIN + SWEEP, 5 method. (PHA 1b)

Cell list (control đã chốt):
  - MAIN : 7 dataset × 5 method tại mult=1.0 (ξ operating, S/~S từ calib_<ds>.json đã freeze).
  - SWEEP: mọi điểm feasible=ok trong sweep_grid.json TRỪ mult=1.0 (đã ở MAIN) và TRỪ toàn bộ
           chainstore (round3 collapse). Mỗi điểm × 5 method. S/~S RE-DERIVE ở ξ(mult) bằng CÙNG
           cơ chế calibrate (mine_fwi→freeze→select_sfwi), cache calibration/sweep_frozen_<ds>_m<mult>.json.

Mỗi cell: HidingDB (float64 production, track=S+~S) → hiding (RT CHỈ pha hiding, deadline 2h) →
boundary audit (float round3 vs Fraction exact ở biên |round3(ws)−ξ|≤0.0015; mismatch>0 ⇒ DỪNG) →
AC re-mine (SAU, KHÔNG deadline) → result_<ds>_m<mult>_<method>.json + progress + summary.csv →
commit+push. Ô TUẦN TỰ, resume idempotent (skip nếu result đã có). MỘT git writer = coordinator.

5 method: HFPriority, MCPriority_safeT, MCPriority_safeF, MSU-MAU, MSU-MIU.
Backend §V = float64 + round(ws,3)≥ξ (SPEC_PART4). REUSE hiding/metrics/miner/calibrate — KHÔNG sửa logic.

Chạy:
  python3 coordinator/run_coordinator.py               # full MAIN+SWEEP
  python3 coordinator/run_coordinator.py --smoke       # chỉ cell nặng (smoke 1b)
  python3 coordinator/run_coordinator.py --ds <ds> ... # lọc dataset
Guard __main__. Nền: setsid nohup ... & disown.
"""
import os
import sys

# Determinism: float sum theo thứ tự hash str ⇒ cố định PYTHONHASHSEED=0 (round(ws,3) biên).
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

import json
import csv
import time
import signal
import socket
import subprocess
import logging
import traceback
from fractions import Fraction

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets")
CALIB = os.path.join(ROOT, "calibration")
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)
for d in ("hiding", "metrics", "mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))
sys.path.insert(0, CALIB)                              # để import calibrate (reuse)

import miner                                                              # noqa: E402
from miner import mine_fwi, fwi_itemsets                                  # noqa: E402
from preprocess import load_transactions, load_weights                    # noqa: E402
from common import HidingDB                                               # noqa: E402
from select_victim import score_hfp, score_mcp                            # noqa: E402
from hfpriority import hfpriority                                         # noqa: E402
import mcpriority as MCP                                                  # noqa: E402
from mcpriority import mcpriority                                         # noqa: E402
from baseline_ppum import run_msu_mau, run_msu_miu                        # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
import calibrate as CAL                                                   # noqa: E402  (freeze/select_sfwi)

miner.config.MAX_PATTERN_LENGTH = 20            # AC re-mine + derive đầy đủ (khớp calibration; >7)
HIDING_DEADLINE_S = 7200                        # 2h/cell CHỈ pha hiding. AC re-mine KHÔNG deadline.
BOUNDARY_BAND = 0.0015                          # |round3(ws_float)−ξ| ≤ band ⇒ audit exact Fraction
HOST = socket.gethostname()

DS_FILES = {
    "chess_fimi": ("chess_fimi_quantities.txt", "chess_fimi_weights.txt"),
    "mushroom":   ("mushroom_quantities.txt",   "mushroom_weights.txt"),
    "retail":     ("retail_quantities.txt",     "retail_weights.txt"),
    "bms-pos":    ("bms-pos_quantities.txt",    "bms-pos_weights.txt"),
    "kosarak":    ("kosarak_quantities.txt",    "kosarak_weights.txt"),
    "accident":   ("accident_quantities.txt",   "accident_weights.txt"),
    "chainstore": ("chainstore_quantities.txt", "chainstore_weights.txt"),
}
DS_ORDER = ["chess_fimi", "mushroom", "retail", "bms-pos", "kosarak", "accident", "chainstore"]
METHODS = ["HFPriority", "MCPriority_safeT", "MCPriority_safeF", "MSU-MAU", "MSU-MIU"]
SWEEP_EXCLUDE_DS = {"chainstore"}                # control: bỏ chainstore khỏi sweep (round3 collapse)
SMOKE_POINTS = [("chess_fimi", 0.6), ("mushroom", 0.4), ("accident", 0.8)]   # cell nặng nhất


# ------------------------------ cell spec (data-driven từ grid) ------------------------------
def mtag(mult):
    return f"{mult:.1f}"


def build_points(smoke=False, ds_filter=None):
    """Trả list điểm (ds, mult, xi, kind). kind∈{main,sweep}. Data-driven từ sweep_grid.json."""
    grid = json.load(open(os.path.join(CALIB, "sweep_grid.json")))
    if smoke:
        pts = []
        for ds, mult in SMOKE_POINTS:
            p = next(p for p in grid[ds] if abs(p["mult"] - mult) < 1e-9)
            pts.append((ds, mult, p["xi"], "sweep"))
        return pts
    pts = []
    for ds in DS_ORDER:
        if ds_filter and ds not in ds_filter:
            continue
        # MAIN: mult=1.0
        p1 = next(p for p in grid[ds] if abs(p["mult"] - 1.0) < 1e-9)
        pts.append((ds, 1.0, p1["xi"], "main"))
        # SWEEP: ok, mult≠1.0, ds không bị loại
        if ds in SWEEP_EXCLUDE_DS:
            continue
        for p in sorted(grid[ds], key=lambda x: x["mult"]):
            if p["feasible"] == "ok" and abs(p["mult"] - 1.0) > 1e-9:
                pts.append((ds, p["mult"], p["xi"], "sweep"))
    return pts


def get_frozen(ds, mult, xi, D, Wf, Wfrac):
    """(S_list, fwi_list) tại ξ(mult). mult=1.0 → calib_<ds>.json; sweep → derive+cache (reuse calibrate)."""
    if abs(mult - 1.0) < 1e-9:
        calib = json.load(open(os.path.join(CALIB, f"calib_{ds}.json")))
        return [frozenset(x) for x in calib["sfwi"]], [frozenset(x) for x in calib["fwi"]]
    path = os.path.join(CALIB, f"sweep_frozen_{ds}_m{mtag(mult)}.json")
    if os.path.exists(path):
        rec = json.load(open(path))
        return [frozenset(x) for x in rec["sfwi"]], [frozenset(x) for x in rec["fwi"]]
    xi_frac = Fraction(str(xi))
    itemsets = [n.itemset for n in CAL.mine_fwi(D, Wf, xi)]
    fwi_ws, _ = CAL.freeze(D, Wfrac, xi_frac, itemsets)
    S, n_cand, n_sfwi = CAL.select_sfwi(fwi_ws, xi_frac)
    rec = {"dataset": ds, "mult": mult, "xi": xi, "n_fwi": len(fwi_ws),
           "n_sfwi": n_sfwi, "n_candidate": n_cand,
           "fwi": CAL._itemset_list([X for X, _ in fwi_ws]), "sfwi": CAL._itemset_list(S)}
    with open(path, "w") as f:
        json.dump(rec, f, indent=1)
    # sanity: khớp grid counts
    grid = json.load(open(os.path.join(CALIB, "sweep_grid.json")))
    g = next(p for p in grid[ds] if abs(p["mult"] - mult) < 1e-9)
    assert rec["n_fwi"] == g["n_fwi"] and rec["n_sfwi"] == g["n_sfwi"] and rec["n_candidate"] == g["n_candidate"], \
        f"derive≠grid {ds} m{mult}: {rec['n_fwi']}/{rec['n_sfwi']}/{rec['n_candidate']} vs {g['n_fwi']}/{g['n_sfwi']}/{g['n_candidate']}"
    return [frozenset(x) for x in rec["sfwi"]], [frozenset(x) for x in rec["fwi"]]


# ------------------------------ hiding + audit ------------------------------
class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _instrument_delete(db):
    cnt = [0]
    orig = db.delete

    def wrapped(v, t):
        orig(v, t)
        cnt[0] += 1
    db.delete = wrapped
    return cnt


def run_hiding(method, db, S, NS, xi):
    """Chạy đúng 1 method, đo RT CHỈ pha hiding (deadline 2h). Trả (rt, status, n_del, n_safe_blocked)."""
    dc = _instrument_delete(db)
    n_safe_blocked = None
    status = "ok"
    safe_cnt = [0]
    orig_is_safe = MCP.is_safe
    if method == "MCPriority_safeT":
        def counting(db_, v, tk, NS_, xi_, round3=False):
            r = orig_is_safe(db_, v, tk, NS_, xi_, round3)
            if not r:
                safe_cnt[0] += 1
            return r
        MCP.is_safe = counting

    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(HIDING_DEADLINE_S)
    t0 = time.perf_counter()
    try:
        if method == "HFPriority":
            hfpriority(db, S, xi, score=score_hfp(S, db.W), round3=True)
        elif method == "MCPriority_safeT":
            mcpriority(db, S, NS, xi, score=score_mcp(NS, db.W), safe_check=True, order="mc_tid", round3=True)
        elif method == "MCPriority_safeF":
            mcpriority(db, S, NS, xi, score=score_mcp(NS, db.W), safe_check=False, order="mc_tid", round3=True)
        elif method == "MSU-MAU":
            run_msu_mau(db, S, xi, round3=True)
        elif method == "MSU-MIU":
            run_msu_miu(db, S, xi, round3=True)
        else:
            raise ValueError(method)
        rt = time.perf_counter() - t0
    except _Timeout:
        rt = float(HIDING_DEADLINE_S)
        status = "timeout"
    finally:
        signal.alarm(0)
        MCP.is_safe = orig_is_safe

    if method in ("MCPriority_safeT", "MCPriority_safeF"):
        n_safe_blocked = safe_cnt[0] if method == "MCPriority_safeT" else 0
    return rt, status, dc[0], n_safe_blocked


def boundary_audit(db, universe, xi, Wfrac):
    """
    Audit float round3 vs Fraction exact tại biên ξ trên DB đã tẩy.
    n_boundary = #itemset có |round3(ws_float)−ξ| ≤ band ; n_boundary_mismatch = #trong đó quyết định
    membership round3 ≠ exact Fraction. mismatch>0 ⇒ backend float sai ở biên ⇒ caller DỪNG.
    """
    Wtot = Fraction(0)
    twf = {}
    for t, s in db.D.items():
        if not s:
            continue
        tw = sum(Wfrac.get(i, 0) for i in s) / len(s)
        twf[t] = tw
        Wtot += tw
    xi_frac = Fraction(str(xi))
    n_boundary = 0
    n_mismatch = 0
    for X in universe:
        r = round(float(db.ws(X)), 3)
        if abs(r - xi) <= BOUNDARY_BAND:
            n_boundary += 1
            cov = db.cover(X)
            wf = (sum(twf[t] for t in cov) / Wtot) if Wtot else Fraction(0)
            if (r >= xi) != (wf >= xi_frac):
                n_mismatch += 1
    return n_boundary, n_mismatch


def run_cell(ds, mult, xi, method, D, Wf, Wfrac, S, fwi, kind):
    out = os.path.join(RESULTS, f"result_{ds}_m{mtag(mult)}_{method}.json")
    if os.path.exists(out):
        return json.load(open(out)), True
    Sset = set(S)
    NS = [x for x in fwi if x not in Sset]
    fwi_orig = set(fwi)

    rec = {"dataset": ds, "method": method, "mult": mult, "xi": xi, "kind": kind,
           "HF": None, "MC": None, "AC": None, "RT_hiding_s": None, "AC_remine_s": None,
           "n_noop": None, "n_safe_blocked": None, "n_deletions": None,
           "n_boundary": None, "n_boundary_mismatch": None, "source": HOST, "status": "error"}
    try:
        db = HidingDB(D, Wf, track=S + NS)
        rt, status, n_del, n_safe_blocked = run_hiding(method, db, S, NS, xi)
        hf = float(hiding_failure(db, S, xi, round3=True))
        mc = float(missing_cost(db, NS, xi, round3=True))
        n_noop = None
        if method in ("MCPriority_safeT", "MCPriority_safeF"):
            n_noop = None if status == "timeout" else (1 if hf > 0 else 0)
        nb, nbm = boundary_audit(db, list(dict.fromkeys(S + NS)), xi, Wfrac)
        # AC re-mine (SAU RT, KHÔNG deadline)
        t_ac = time.perf_counter()
        fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, xi))
        ac = float(artificial_cost(fwi_orig, fwi_san))
        ac_s = time.perf_counter() - t_ac
        rec.update({"HF": round(hf, 6), "MC": round(mc, 6), "AC": round(ac, 6),
                    "RT_hiding_s": round(rt, 3), "AC_remine_s": round(ac_s, 3),
                    "n_noop": n_noop, "n_safe_blocked": n_safe_blocked, "n_deletions": n_del,
                    "n_boundary": nb, "n_boundary_mismatch": nbm, "status": status})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-1500:]
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    return rec, False


# ------------------------------ progress / summary / git ------------------------------
SUMMARY_COLS = ["dataset", "method", "mult", "xi", "kind", "HF", "MC", "AC", "RT_hiding_s",
                "AC_remine_s", "n_noop", "n_safe_blocked", "n_deletions",
                "n_boundary", "n_boundary_mismatch", "source", "status"]


def write_progress(points):
    done = sum(1 for (ds, mult, xi, kind) in points for m in METHODS
               if os.path.exists(os.path.join(RESULTS, f"result_{ds}_m{mtag(mult)}_{m}.json")))
    with open(os.path.join(RESULTS, "progress_sectionV.json"), "w") as f:
        json.dump({"total_cells": len(points) * len(METHODS), "done_cells": done}, f, indent=1)


def write_summary(points):
    rows = []
    for (ds, mult, xi, kind) in points:
        for m in METHODS:
            p = os.path.join(RESULTS, f"result_{ds}_m{mtag(mult)}_{m}.json")
            if os.path.exists(p):
                r = json.load(open(p))
                rows.append({c: r.get(c) for c in SUMMARY_COLS})
    with open(os.path.join(RESULTS, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_COLS)
        w.writeheader()
        w.writerows(rows)


def git_checkpoint(msg):
    try:
        subprocess.run(["git", "add", "results/", "calibration/"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-q", "-m", msg + "\n\n"
                        "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"],
                       cwd=ROOT, check=True)
        for _ in range(4):
            r = subprocess.run(["git", "push", "origin", "exp/v5-sectionV"], cwd=ROOT)
            if r.returncode == 0:
                break
            time.sleep(3)
    except subprocess.CalledProcessError:
        pass


# ------------------------------ main ------------------------------
def main(argv):
    smoke = "--smoke" in argv
    ds_filter = None
    if "--ds" in argv:
        i = argv.index("--ds")
        ds_filter = argv[i + 1:]
    points = build_points(smoke=smoke, ds_filter=ds_filter)
    print(f"[coord] {'SMOKE' if smoke else 'FULL'} {len(points)} điểm × {len(METHODS)} method "
          f"= {len(points)*len(METHODS)} cell", flush=True)
    for (ds, mult, xi, kind) in points:
        print(f"[{ds}/m{mtag(mult)}] ({kind}) load D/W ξ={xi}…", flush=True)
        tf, wf = DS_FILES[ds]
        D = load_transactions(os.path.join(DATA, tf))
        Wf = load_weights(os.path.join(DATA, wf), 10, False)
        Wfrac = load_weights(os.path.join(DATA, wf), 10, True)
        S, fwi = get_frozen(ds, mult, xi, D, Wf, Wfrac)
        for m in METHODS:
            rec, skipped = run_cell(ds, mult, xi, m, D, Wf, Wfrac, S, fwi, kind)
            tag = "SKIP" if skipped else rec["status"]
            print(f"[{ds}/m{mtag(mult)}/{m}] {tag} HF={rec['HF']} MC={rec['MC']} AC={rec['AC']} "
                  f"RT={rec['RT_hiding_s']}s AC_rem={rec['AC_remine_s']}s n_del={rec['n_deletions']} "
                  f"n_noop={rec['n_noop']} n_sblk={rec['n_safe_blocked']} "
                  f"nb={rec['n_boundary']} nbm={rec['n_boundary_mismatch']}", flush=True)
            if not skipped:
                write_progress(points)
                write_summary(points)
                git_checkpoint(f"coord: {ds}/m{mtag(mult)}/{m} ({kind})")
                if rec.get("n_boundary_mismatch"):
                    print(f"[STOP] n_boundary_mismatch={rec['n_boundary_mismatch']} tại "
                          f"{ds}/m{mtag(mult)}/{m} ⇒ DỪNG báo control", flush=True)
                    sys.exit(3)
                if rec["status"] == "error":
                    print(f"[STOP] error tại {ds}/m{mtag(mult)}/{m}: {rec.get('error')} ⇒ DỪNG", flush=True)
                    sys.exit(4)
        del D, Wf, Wfrac
    print("COORD DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv)
