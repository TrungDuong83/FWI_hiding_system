# -*- coding: utf-8 -*-
"""
coordinator/resmoke_safe.py — re-smoke ĐÚNG 2 cell khó × MCPriority(safe=True) sau khi cài Safe/ws
incremental (num_cache). KHÔNG phóng 35 cell. Reuse nguyên run_coordinator.run_cell (đủ cột + 2h
deadline + AC re-mine + checkpoint). Chạy: PYTHONHASHSEED=0 python3 coordinator/resmoke_safe.py
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_coordinator as RC                                   # noqa: E402

CELLS = ["chainstore", "accident"]                             # 2 cell khó
METHOD = "MCPriority_safeT"


def main():
    dmap = {d[0]: (d[1], d[2]) for d in RC.DATASETS}
    for ds in CELLS:
        tf, wf = dmap[ds]
        out = os.path.join(RC.RESULTS, f"result_{ds}_{METHOD}.json")
        if os.path.exists(out):
            os.remove(out)                                     # buộc chạy lại với incremental
        calib = json.load(open(os.path.join(RC.CALIB, f"calib_{ds}.json")))
        print(f"[{ds}] load D/W…", flush=True)
        D = RC.load_transactions(os.path.join(RC.DATA, tf))
        Wf = RC.load_weights(os.path.join(RC.DATA, wf), 10, False)
        rec, _ = RC.run_cell(ds, tf, wf, METHOD, D, Wf, calib)
        print(f"[{ds}/{METHOD}] {rec['status']} HF={rec['HF']} MC={rec['MC']} AC={rec['AC']} "
              f"RT={rec['RT_hiding_s']}s AC_remine={rec['AC_remine_s']}s n_del={rec['n_deletions']} "
              f"n_noop={rec['n_noop']} n_safe_blocked={rec['n_safe_blocked']}", flush=True)
        RC.write_progress(ds)
        RC.write_summary()
        RC.git_checkpoint(ds, METHOD)
        del D, Wf
    print("RESMOKE DONE", flush=True)


if __name__ == "__main__":
    main()
