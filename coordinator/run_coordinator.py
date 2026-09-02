# -*- coding: utf-8 -*-
"""
coordinator/run_coordinator.py — §V grid 7 dataset × 5 method = 35 cell.

Mỗi cell: đọc calib_<ds>.json (ξ/S/~S ĐÓNG BĂNG) → HidingDB (float64 production) → chạy hiding
(đo RT_hiding CHỈ pha hiding, deadline 2h) → AC re-mine (SAU, KHÔNG deadline) → ghi
result_<ds>_<method>.json + progress + summary.csv → commit+push. Ô TUẦN TỰ, resume idempotent
(skip nếu result đã có). MỘT git writer = coordinator.

Backend §V = float64 + round(ws,3)≥ξ (SPEC_PART4 §2/§5). S=sfwi[], ~S=fwi[]\sfwi[] (frozen).

REUSE (KHÔNG sửa): hfpriority/mcpriority/baseline_ppum (hiding), metrics, miner, calib json.
- n_safe_blocked (MCPriority): đếm qua monkeypatch mcpriority.is_safe (KHÔNG sửa source).
- n_deletions: đếm qua wrap db.delete (sống sót cả khi timeout).
- n_noop (MCPriority): 1 nếu còn SFWI lộ (HF>0, dừng bằng no-op) else 0. method khác = null.

Chạy:  python3 coordinator/run_coordinator.py [<ds> ...]   # không arg = cả 35 cell
Guard __main__. Chạy nền: setsid nohup ... & disown (PLAYBOOK §3.1).
"""
import os
import sys
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

import miner                                                              # noqa: E402
from miner import mine_fwi, fwi_itemsets                                  # noqa: E402
from preprocess import load_transactions, load_weights                    # noqa: E402
from common import HidingDB                                               # noqa: E402
from select_victim import score_hfp, score_mcp                            # noqa: E402
from hfpriority import hfpriority                                         # noqa: E402
import mcpriority as MCP                                                  # noqa: E402
from mcpriority import mcpriority                                         # noqa: E402
from baseline_ppum import run_msu_mau, run_msu_miu                        # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost         # noqa: E402

miner.config.MAX_PATTERN_LENGTH = 20            # AC re-mine đầy đủ (khớp calibration; >7)
HIDING_DEADLINE_S = 7200                        # 2h/cell CHỈ pha hiding (Q10). AC re-mine KHÔNG deadline.
HOST = socket.gethostname()

DATASETS = [                                    # fast → slow
    ("chess_fimi", "chess_fimi_quantities.txt", "chess_fimi_weights.txt"),
    ("mushroom",   "mushroom_quantities.txt",   "mushroom_weights.txt"),
    ("retail",     "retail_quantities.txt",     "retail_weights.txt"),
    ("bms-pos",    "bms-pos_quantities.txt",    "bms-pos_weights.txt"),
    ("kosarak",    "kosarak_quantities.txt",    "kosarak_weights.txt"),
    ("accident",   "accident_quantities.txt",   "accident_weights.txt"),
    ("chainstore", "chainstore_quantities.txt", "chainstore_weights.txt"),
]
METHODS = ["HFPriority", "MCPriority_safeT", "MCPriority_safeF", "MSU-MAU", "MSU-MIU"]


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _instrument_delete(db):
    """Wrap db.delete để đếm n_deletions (sống sót cả khi timeout)."""
    cnt = [0]
    orig = db.delete

    def wrapped(v, t):
        orig(v, t)
        cnt[0] += 1
    db.delete = wrapped
    return cnt


def run_hiding(method, db, S, NS, xi):
    """Chạy đúng 1 method, đo RT CHỈ pha hiding (deadline 2h). Trả (rt_s, status, counters)."""
    dc = _instrument_delete(db)
    n_noop = n_safe_blocked = None
    status = "ok"

    # counters cho MCPriority qua monkeypatch is_safe (không sửa source)
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
    return rt, status, dc[0], n_noop, n_safe_blocked


def run_cell(ds, tf, wf, method, D, Wf, calib):
    out = os.path.join(RESULTS, f"result_{ds}_{method}.json")
    if os.path.exists(out):
        return json.load(open(out)), True                    # resume skip
    xi = calib["xi"]
    S = [frozenset(x) for x in calib["sfwi"]]
    fwi = [frozenset(x) for x in calib["fwi"]]
    Sset = set(S)
    NS = [x for x in fwi if x not in Sset]
    fwi_orig = set(fwi)

    rec = {"dataset": ds, "method": method, "xi": xi,
           "HF": None, "MC": None, "AC": None, "RT_hiding_s": None,
           "n_noop": None, "n_safe_blocked": None, "n_deletions": None,
           "AC_remine_s": None, "source": HOST, "status": "error"}
    try:
        db = HidingDB(D, Wf)                                   # float64 production, fresh mỗi cell
        rt, status, n_del, n_noop, n_safe_blocked = run_hiding(method, db, S, NS, xi)
        hf = float(hiding_failure(db, S, xi, round3=True))
        mc = float(missing_cost(db, NS, xi, round3=True))
        if method in ("MCPriority_safeT", "MCPriority_safeF"):
            n_noop = 1 if hf > 0 else 0                        # dừng bằng no-op ⟺ còn SFWI lộ
        # AC re-mine (SAU RT, KHÔNG deadline)
        t_ac = time.perf_counter()
        fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, xi))
        ac = float(artificial_cost(fwi_orig, fwi_san))
        ac_s = time.perf_counter() - t_ac
        rec.update({"HF": round(hf, 6), "MC": round(mc, 6), "AC": round(ac, 6),
                    "RT_hiding_s": round(rt, 3), "n_noop": n_noop,
                    "n_safe_blocked": n_safe_blocked, "n_deletions": n_del,
                    "AC_remine_s": round(ac_s, 3), "status": status})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-1500:]
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)
    return rec, False


def write_progress(ds):
    done = [m for m in METHODS if os.path.exists(os.path.join(RESULTS, f"result_{ds}_{m}.json"))]
    with open(os.path.join(RESULTS, f"progress_{ds}.json"), "w") as f:
        json.dump({"dataset": ds, "done": done, "attempts": len(done)}, f, indent=1)


def write_summary():
    cols = ["dataset", "method", "xi", "HF", "MC", "AC", "RT_hiding_s",
            "n_noop", "n_safe_blocked", "n_deletions", "AC_remine_s", "source", "status"]
    rows = []
    for ds, _, _ in DATASETS:
        for m in METHODS:
            p = os.path.join(RESULTS, f"result_{ds}_{m}.json")
            if os.path.exists(p):
                r = json.load(open(p))
                rows.append({c: r.get(c) for c in cols})
    with open(os.path.join(RESULTS, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def git_checkpoint(ds, method):
    try:
        subprocess.run(["git", "add", "results/"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-q", "-m",
                        f"coord: {ds}/{method} result\n\n"
                        "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>\n"
                        "Claude-Session: https://claude.ai/code/session_01Qjq8gsQeVBACNw6VxMaV58"],
                       cwd=ROOT, check=True)
        for _ in range(4):
            r = subprocess.run(["git", "push", "origin", "exp/v5-sectionV"], cwd=ROOT)
            if r.returncode == 0:
                break
            time.sleep(3)
    except subprocess.CalledProcessError:
        pass                                                  # nothing to commit / offline: bỏ qua


def main(argv):
    want_ds = argv[1:] if len(argv) > 1 else [d[0] for d in DATASETS]
    for ds, tf, wf in DATASETS:
        if ds not in want_ds:
            continue
        if all(os.path.exists(os.path.join(RESULTS, f"result_{ds}_{m}.json")) for m in METHODS):
            print(f"[{ds}] all 5 done — skip", flush=True)
            continue
        calib = json.load(open(os.path.join(CALIB, f"calib_{ds}.json")))
        print(f"[{ds}] load D/W…", flush=True)
        D = load_transactions(os.path.join(DATA, tf))
        Wf = load_weights(os.path.join(DATA, wf), 10, False)
        for m in METHODS:
            rec, skipped = run_cell(ds, tf, wf, m, D, Wf, calib)
            tag = "SKIP" if skipped else rec["status"]
            print(f"[{ds}/{m}] {tag} HF={rec['HF']} MC={rec['MC']} AC={rec['AC']} "
                  f"RT={rec['RT_hiding_s']}s AC_remine={rec['AC_remine_s']}s "
                  f"n_del={rec['n_deletions']} n_noop={rec['n_noop']} n_safe_blocked={rec['n_safe_blocked']}",
                  flush=True)
            if not skipped:
                write_progress(ds)
                write_summary()
                git_checkpoint(ds, m)
        del D, Wf
    print("COORD DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv)
