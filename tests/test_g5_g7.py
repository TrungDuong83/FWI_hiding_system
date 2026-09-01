# -*- coding: utf-8 -*-
"""
tests/test_g5_g7.py — Gate G5 (parity float64+round3 ↔ Fraction) + G7 (determinism).

G5: chạy lại 3 golden trace bằng backend float64 + round(ws,3)≥ξ → trace + HF/MC/AC KHỚP
    backend Fraction (exact), ZERO mismatch. Đồng thời khớp giá trị golden đã chốt.
G7: chạy 2 lần cùng input → trace + metrics Y HỆT; mining MP (use_mp=True) == đơn luồng (cùng SET).

3 config golden (running example ξ=0.55, S={AC,CE}):
    HFP            : C@T3→C@T1     ; HF=0   MC=3/7 (lost {C,CD,ACD})      AC=0
    MCP safe=True  : E@T1→C@T2→C@T4; HF=1/2 MC=0   (residual {AC})        AC=0
    MCP safe=False : E@T1→E@T2→A@T3; HF=0   MC=4/7 (lost {A,AD,ACD,E})    AC=0
Entry-guarded; exit != 0 nếu FAIL.
"""
import os
import sys
import logging
from fractions import Fraction as F

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for d in ("hiding", "metrics", "mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))

from common import HidingDB                                              # noqa: E402
from hfpriority import hfpriority                                        # noqa: E402
from mcpriority import mcpriority                                        # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
from miner import mine_fwi, fwi_itemsets                                # noqa: E402

W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
S = [frozenset("AC"), frozenset("CE")]
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]
Wf = {k: float(v) for k, v in W.items()}          # cho AC re-mine (engine luôn float)

CONFIGS = [
    ("HFP",        "hfp", {}),
    ("MCP_safeT",  "mcp", {"safe_check": True,  "order": "mc_tid"}),
    ("MCP_safeF",  "mcp", {"safe_check": False, "order": "mc_tid"}),
]

# Golden đã chốt (để G5 vừa parity vừa khớp giá trị thật)
EXPECT = {
    "HFP":       {"trace": ["C@T3", "C@T1"],        "HF": F(0),    "MC": F(3, 7), "AC": F(0),
                  "lost": ["ACD", "C", "CD"],       "residual": []},
    "MCP_safeT": {"trace": ["E@T1", "C@T2", "C@T4"], "HF": F(1, 2), "MC": F(0),    "AC": F(0),
                  "lost": [],                        "residual": ["AC"]},
    "MCP_safeF": {"trace": ["E@T1", "E@T2", "A@T3"], "HF": F(0),    "MC": F(4, 7), "AC": F(0),
                  "lost": ["A", "ACD", "AD", "E"],   "residual": []},
}


def run_config(kind, params, backend):
    """backend: 'frac' (Fraction, exact) | 'float' (float64, round3). Trả dict kết quả."""
    if backend == "frac":
        Wb, xi, r3 = W, F(55, 100), False
    else:
        Wb, xi, r3 = Wf, 0.55, True
    db = HidingDB(D, Wb)
    if kind == "hfp":
        trace = hfpriority(db, S, xi, round3=r3)
    else:
        trace = mcpriority(db, S, NS, xi, round3=r3, **params)
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, 0.55))
    return {
        "trace": [f"{v}@{t}" for v, t in trace],
        "HF": hiding_failure(db, S, xi, r3),
        "MC": missing_cost(db, NS, xi, r3),
        "AC": artificial_cost(fwi_orig, fwi_san),
        "lost": sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), xi, r3)),
        "residual": sorted("".join(sorted(s)) for s in S if is_frequent(db.ws(s), xi, r3)),
    }


def test_g5_parity():
    allok = True
    for name, kind, params in CONFIGS:
        rf = run_config(kind, params, "frac")
        rx = run_config(kind, params, "float")
        parity = rf == rx                                   # float64+round3 == Fraction
        match_golden = rf == EXPECT[name]
        ok = parity and match_golden
        allok &= ok
        print(f"[G5 {name}] parity(float↔frac)={parity} match_golden={match_golden} "
              f"trace={' -> '.join(rf['trace'])} HF={rf['HF']} MC={rf['MC']} AC={rf['AC']}")
    print("G5", "PASS" if allok else "FAIL")
    return allok


def test_g7_determinism():
    allok = True
    # (a) full pipeline 2 lần cùng input → y hệt
    for name, kind, params in CONFIGS:
        r1 = run_config(kind, params, "float")
        r2 = run_config(kind, params, "float")
        ok = r1 == r2
        allok &= ok
        print(f"[G7 {name}] run1==run2 = {ok}")
    # (b) mining MP (use_mp=True) == đơn luồng (cùng SET, bất biến thứ tự worker)
    set_sp = fwi_itemsets(mine_fwi(D, Wf, 0.55, use_mp=False))
    set_mp = fwi_itemsets(mine_fwi(D, Wf, 0.55, use_mp=True))
    ok_mine = set_sp == set_mp
    allok &= ok_mine
    print(f"[G7 mining] single==MP set = {ok_mine} (#={len(set_sp)})")
    print("G7", "PASS" if allok else "FAIL")
    return allok


def main():
    g5 = test_g5_parity()
    print()
    g7 = test_g7_determinism()
    allok = g5 and g7
    print("\nGB(G5+G7)", "PASS" if allok else "FAIL")
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
