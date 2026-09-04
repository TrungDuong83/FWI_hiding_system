# -*- coding: utf-8 -*-
"""
calibration/sweep_grid.py — PHA 1a: feasibility grid cho SENSITIVITY SWEEP (chỉ MINE + ĐẾM).

KHÔNG hiding, KHÔNG RT, KHÔNG 5 method. Chỉ mine FWI + đếm + chọn S (đúng cơ chế operating) để
định cỡ tải PHA 1b.

REUSE (KHÔNG sửa logic): import trực tiếp calibrate.py → mine_fwi / freeze / select_sfwi / loaders.
  Đây là ĐÚNG cùng cơ chế đã freeze calib_<ds>.json (mult=1.0 phải khớp — G-SW1).

Lưới: 7 dataset × mult ∈ {0.4,0.6,0.8,1.0,1.2,1.4,1.6}. ξ(mult)=round(mult·ξ_chuẩn, 3) (≤3dp).
  ξ_chuẩn = xi trong calib_<ds>.json (mult=1.0).

Phân loại feasible:
  - ceiling : ξ(mult) ≥ 1.0 (≥max_ws, hết pattern) HOẶC #FWI < 10.
  - floor   : mine vượt 20 phút (SIGALRM 1200s) HOẶC bị kill (OOM/mem). Monotonic: #FWI tăng khi ξ
              giảm ⇒ một điểm floor ⇒ MỌI mult THẤP hơn cũng floor (short-circuit, không mine lại).
  - ok      : còn lại.

Hạ tầng chịu-nổ: mỗi dataset chạy trong 1 WORKER subprocess (load data 1 lần). Worker mine theo mult
GIẢM DẦN (ξ cao→thấp: nhanh→nổ), SIGALRM 1200s/điểm, checkpoint sweep_grid.json sau MỖI điểm. Nếu
worker bị OOM-kill giữa chừng, ORCHESTRATOR (process nhẹ, tách biệt) phát hiện exit≠0 và đánh floor
(monotonic) cho điểm dở + mọi mult thấp hơn chưa làm. Resume: bỏ qua điểm đã có trong sweep_grid.json.

Entry-guarded. Backend Fraction cho freeze/select (exact), ξ ≤3dp.
"""
import os
import sys
import json
import time
import signal
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)                                  # để import calibrate
import calibrate as C                                     # noqa: E402  (reuse, KHÔNG sửa)

MULTS = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
MULTS_DESC = sorted(MULTS, reverse=True)                  # ξ cao→thấp (nhanh→nổ)
MINE_TIMEOUT_S = 1200                                     # 20 phút = ngưỡng floor (spec)
GRID_PATH = os.path.join(HERE, "sweep_grid.json")

# thứ tự dataset: nhanh→chậm (khớp calibrate.DATASETS)
DS_ORDER = [d[0] for d in C.DATASETS]
DS_FILES = {d[0]: (d[1], d[2]) for d in C.DATASETS}


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


# ============================== WORKER (1 dataset, load 1 lần) ==============================
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
        if round(mult, 3) in pts:                        # resume: đã có
            if pts[round(mult, 3)]["feasible"] == "floor":
                floored = True
            continue
        xi = xi_of(mult, xi_std)
        rec = {"mult": mult, "xi": xi, "n_fwi": None, "n_sfwi": None,
               "n_candidate": None, "mine_time_s": None, "feasible": None, "reason": ""}

        if floored:
            rec.update(feasible="floor", reason="floor by monotonicity (higher-ξ point floored)")
            n_fwi = n_sfwi = n_cand = None
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


# ============================== ORCHESTRATOR (nhẹ, tách biệt) ==============================
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
            # worker chết (OOM/kill) → điểm dở + mọi mult thấp hơn = floor (monotonic)
            xi_std = json.load(open(os.path.join(HERE, f"calib_{ds}.json")))["xi"]
            grid = load_grid()
            pts = {round(p["mult"], 3): p for p in grid.get(ds, [])}
            for mult in MULTS_DESC:                        # ξ cao→thấp
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

    # ---- G-SW1 sanity: mult=1.0 khớp calib_<ds>.json đã freeze ----
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
    ok = orchestrate()
    grid = load_grid()
    summ = []
    for ds in DS_ORDER:
        n_ok = sum(1 for p in grid.get(ds, []) if p["feasible"] == "ok")
        summ.append(f"{ds}={n_ok}/{len(MULTS)}pts")
    print("\nSWEEP GRID:", " ".join(summ), flush=True)


if __name__ == "__main__":
    main(sys.argv)
