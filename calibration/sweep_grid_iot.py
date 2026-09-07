# -*- coding: utf-8 -*-
"""
calibration/sweep_grid_iot.py — Feasibility grid SENSITIVITY SWEEP cho IoT (mnc + rtvcq).
Giống hệt sweep_grid.py (7 dataset) nhưng CHỈ mnc+rtvcq → file riêng sweep_grid_iot.json.

KHÔNG hiding, KHÔNG RT, KHÔNG 5 method. Chỉ mine FWI + đếm + chọn S (đúng cơ chế operating).
REUSE calibrate.py (mine_fwi/freeze/select_sfwi/loaders — KHÔNG sửa). ξ_op: mnc=0.204, rtvcq=0.057
(từ calib đã freeze). Lưới mult ∈ {0.4,0.6,0.8,1.0,1.2,1.4,1.6}; ξ(mult)=round(mult·ξ_op,3).

feasible: ceiling (#FWI<10 hoặc ξ≥1.0); floor (mine OOM worker-killed hoặc mine_time>1200s; monotonic);
ok (còn lại). Worker/dataset (load 1 lần) + SIGALRM 1200s/điểm + checkpoint mỗi điểm; OOM → orchestrator
floor điểm dở + thấp hơn. Entry-guarded. Backend Fraction cho freeze/select, ξ≤3dp.
"""
import os
import sys
import json
import time
import signal
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import calibrate as C                                     # noqa: E402  (reuse, KHÔNG sửa)

MULTS = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
MULTS_DESC = sorted(MULTS, reverse=True)
MINE_TIMEOUT_S = 1200
GRID_PATH = os.path.join(HERE, "sweep_grid_iot.json")     # <-- file riêng IoT

DS_ORDER = ["rtvcq", "mnc"]                               # <-- chỉ IoT (rtvcq nhẹ trước, mnc nặng sau)
DS_FILES = {d[0]: (d[1], d[2]) for d in C.DATASETS}       # C.DATASETS đã có rtvcq+mnc


def xi_of(mult, xi_std):
    return round(mult * xi_std, 3)


def load_grid():
    if os.path.exists(GRID_PATH):
        return json.load(open(GRID_PATH))
    return {}


def save_grid(grid):
    tmp = GRID_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(grid, f, indent=1)
    os.replace(tmp, GRID_PATH)


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def worker(ds):
    from preprocess import load_transactions, load_weights
    from fractions import Fraction

    xi_std = json.load(open(os.path.join(HERE, f"calib_{ds}.json")))["xi"]
    tfile, wfile = DS_FILES[ds]
    print(f"[{ds}] worker load… (xi_std={xi_std})", flush=True)
    t0 = time.perf_counter()
    D = load_transactions(os.path.join(C.DATA, tfile))
    Wf = load_weights(os.path.join(C.DATA, wfile), normalize=10, use_fraction=False)
    Wfrac = load_weights(os.path.join(C.DATA, wfile), normalize=10, use_fraction=True)
    print(f"[{ds}] |D|={len(D)} |W|={len(Wf)} ({time.perf_counter()-t0:.1f}s)", flush=True)

    signal.signal(signal.SIGALRM, _alarm)
    grid = load_grid()
    pts = {round(p["mult"], 3): p for p in grid.get(ds, [])}
    floored = False

    for mult in MULTS_DESC:
        if round(mult, 3) in pts:
            if pts[round(mult, 3)]["feasible"] == "floor":
                floored = True
            continue
        xi = xi_of(mult, xi_std)
        rec = {"mult": mult, "xi": xi, "n_fwi": None, "n_sfwi": None,
               "n_candidate": None, "mine_time_s": None, "feasible": None, "reason": ""}

        if floored:
            rec.update(feasible="floor", reason="floor by monotonicity (higher-ξ point floored)")
        elif xi >= 1.0:
            rec.update(n_fwi=0, n_sfwi=0, n_candidate=0, mine_time_s=0.0,
                       feasible="ceiling", reason="xi>=1.0 (>=max_ws, no pattern)")
        else:
            try:
                signal.alarm(MINE_TIMEOUT_S)
                ts = time.perf_counter()
                nodes = C.mine_fwi(D, Wf, xi)
                mt = time.perf_counter() - ts
                signal.alarm(0)
            except _Timeout:
                mt = float(MINE_TIMEOUT_S)
                rec.update(mine_time_s=mt, feasible="floor",
                           reason=f"mine_time>{MINE_TIMEOUT_S}s (>20min)")
                floored = True
                pts[round(mult, 3)] = rec
                grid[ds] = [pts[round(m, 3)] for m in MULTS if round(m, 3) in pts]
                save_grid(grid)
                print(f"[{ds}] mult={mult} xi={xi} → FLOOR (timeout {MINE_TIMEOUT_S}s)", flush=True)
                continue
            n_fwi = len(nodes)
            rec["n_fwi"] = n_fwi
            rec["mine_time_s"] = round(mt, 2)
            if n_fwi < 10:
                rec.update(n_sfwi=0, n_candidate=0, feasible="ceiling", reason="n_fwi<10")
            else:
                itemsets = [n.itemset for n in nodes]
                fwi_ws, _ = C.freeze(D, Wfrac, Fraction(str(xi)), itemsets)
                S, n_cand, n_sfwi = C.select_sfwi(fwi_ws, Fraction(str(xi)))
                rec.update(n_fwi=len(fwi_ws), n_sfwi=n_sfwi, n_candidate=n_cand,
                           feasible="ok", reason="ok")

        pts[round(mult, 3)] = rec
        grid[ds] = [pts[round(m, 3)] for m in MULTS if round(m, 3) in pts]
        save_grid(grid)
        print(f"[{ds}] mult={mult} xi={rec['xi']} → {rec['feasible']} "
              f"n_fwi={rec['n_fwi']} n_sfwi={rec['n_sfwi']} "
              f"t={rec['mine_time_s']}s [{rec['reason']}]", flush=True)


def orchestrate():
    for ds in DS_ORDER:
        grid = load_grid()
        have = {round(p["mult"], 3) for p in grid.get(ds, [])}
        if have == {round(m, 3) for m in MULTS}:
            print(f"[{ds}] SKIP (đủ {len(MULTS)} điểm)", flush=True)
            continue
        print(f"\n===== WORKER {ds} =====", flush=True)
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--worker", ds])
        if r.returncode != 0:
            xi_std = json.load(open(os.path.join(HERE, f"calib_{ds}.json")))["xi"]
            grid = load_grid()
            pts = {round(p["mult"], 3): p for p in grid.get(ds, [])}
            for mult in MULTS_DESC:
                if round(mult, 3) in pts:
                    continue
                pts[round(mult, 3)] = {
                    "mult": mult, "xi": xi_of(mult, xi_std),
                    "n_fwi": None, "n_sfwi": None, "n_candidate": None, "mine_time_s": None,
                    "feasible": "floor",
                    "reason": f"worker killed (OOM/mem, exit={r.returncode}); monotonic floor",
                }
            grid[ds] = [pts[round(m, 3)] for m in MULTS if round(m, 3) in pts]
            save_grid(grid)
            print(f"[{ds}] worker exit={r.returncode} → floor điểm còn lại (monotonic)", flush=True)

    grid = load_grid()
    print("\n----- G-SW1 sanity (mult=1.0 vs calib freeze) -----", flush=True)
    ok_all = True
    for ds in DS_ORDER:
        calib = json.load(open(os.path.join(HERE, f"calib_{ds}.json")))
        p1 = next((p for p in grid.get(ds, []) if abs(p["mult"] - 1.0) < 1e-9), None)
        if p1 is None:
            print(f"  [{ds}] mult=1.0 MISSING", flush=True); ok_all = False; continue
        m_xi = abs(p1["xi"] - calib["xi"]) < 1e-9
        m_fwi = p1["n_fwi"] == calib["n_fwi"]
        m_sfwi = p1["n_sfwi"] == calib["n_sfwi"]
        m_cand = p1["n_candidate"] == calib["n_candidate"]
        ok = m_xi and m_fwi and m_sfwi and m_cand
        ok_all &= ok
        print(f"  [{ds}] xi={p1['xi']}=={calib['xi']}({m_xi}) n_fwi={p1['n_fwi']}=={calib['n_fwi']}"
              f"({m_fwi}) n_sfwi={p1['n_sfwi']}=={calib['n_sfwi']}({m_sfwi}) "
              f"n_cand={p1['n_candidate']}=={calib['n_candidate']}({m_cand}) → {'OK' if ok else 'FAIL'}",
              flush=True)
    print(f"G-SW1 {'PASS' if ok_all else 'FAIL'}", flush=True)
    return ok_all


def main(argv):
    if len(argv) >= 3 and argv[1] == "--worker":
        worker(argv[2])
        return
    orchestrate()
    grid = load_grid()
    summ = []
    for ds in DS_ORDER:
        n_ok = sum(1 for p in grid.get(ds, []) if p["feasible"] == "ok")
        summ.append(f"{ds}={n_ok}/{len(MULTS)}pts")
    print("\nIOT SWEEP GRID:", " ".join(summ), flush=True)


if __name__ == "__main__":
    main(sys.argv)
