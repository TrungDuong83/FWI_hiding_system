# -*- coding: utf-8 -*-
"""
tests/test_g2_hfp.py — Gate G2: HFPriority khớp golden (SPEC §3.2, §6), backend Fraction exact.

Golden (ξ=0.55, S={AC,CE}):
    trace = C@T3 → C@T1 ; HF=0 ; MC=3/7 (mất {C,CD,ACD}) ; AC=0.
Khớp CHÍNH XÁC tập itemset, không chỉ con số tổng.
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
from select_victim import score_hfp                                     # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
from miner import mine_fwi, fwi_itemsets                                # noqa: E402

W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
XI = F(55, 100)
S = [frozenset("AC"), frozenset("CE")]
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]   # FWI(orig)\S


def main():
    db = HidingDB(D, W)
    score = score_hfp(S, db.W)
    trace = hfpriority(db, S, XI, score=score)

    tr_str = [f"{v}@{t}" for v, t in trace]
    ok_trace = tr_str == ["C@T3", "C@T1"]

    hf = hiding_failure(db, S, XI)
    mc = missing_cost(db, NS, XI)
    lost = sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), XI))

    Wf = {k: float(v) for k, v in W.items()}
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, 0.55))
    ac = artificial_cost(fwi_orig, fwi_san)

    ok_hf = hf == F(0)
    ok_mc = mc == F(3, 7)
    ok_lost = lost == ["ACD", "C", "CD"]
    ok_ac = ac == F(0)

    print(f"[g2_hfp] trace={' -> '.join(tr_str)} ok={ok_trace}")
    print(f"[g2_hfp] HF={hf} (exp 0) ok={ok_hf} ; MC={mc} (exp 3/7) lost={lost} ok={ok_mc and ok_lost}")
    print(f"[g2_hfp] AC={ac} (exp 0) ok={ok_ac}")

    allok = ok_trace and ok_hf and ok_mc and ok_lost and ok_ac
    print("\nG2", "PASS" if allok else "FAIL")
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
