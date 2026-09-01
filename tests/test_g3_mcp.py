# -*- coding: utf-8 -*-
"""
tests/test_g3_mcp.py — Gate G3: MCPriority (SPEC §3.3, §6), backend Fraction exact.

(1) Golden safe=True, mc_tid : E@T1 → C@T2 → C@T4 ; residual {AC} (HF=1/2) ; MC=0 ; AC=0.
(2) Golden safe=False, mc_tid: E@T1 → E@T2 → A@T3 ; HF=0 ; MC=4/7 (mất {A,AD,ACD,E}) ; AC=0.
(3) Safe fixture: W={A:2/5,B:1/10,C:4/5,D:2/5}, ξ=11/25, D={T1:AB,T2:BD,T3:ABC}, S={ABC}
      → Safe(B,T2) FULL-check = False ; reduced 'chỉ ns⊆T2' = True (full≠reduced; code DÙNG full).
(4) filter-guard fixture: W={A:3/10,B:1/10,C:3/10,D:4/5}, ξ=41/100,
      D={T1:ABCD,T2:ACD,T3:ABCD,T4:BC,T5:ACD}, S={AC,BC}
      → safe=True+filter: HF=1/2, MC=0, AC=0 (nếu AC=1/9 ⇒ filter bị bỏ ⇒ FAIL).
Khớp CHÍNH XÁC tập itemset. Entry-guarded; exit != 0 nếu FAIL.
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
from mcpriority import mcpriority, is_safe                              # noqa: E402
from select_victim import score_mcp                                    # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
from miner import mine_fwi, fwi_itemsets                               # noqa: E402

# ---- Running example ----
W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
XI = F(55, 100)
S = [frozenset("AC"), frozenset("CE")]
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]


def _ac(db_D):
    Wf = {k: float(v) for k, v in W.items()}
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db_D, Wf, 0.55))
    return artificial_cost(fwi_orig, fwi_san)


def test_golden_safe_true():
    db = HidingDB(D, W)
    tr = [f"{v}@{t}" for v, t in mcpriority(db, S, NS, XI, safe_check=True, order="mc_tid")]
    hf, mc, ac = hiding_failure(db, S, XI), missing_cost(db, NS, XI), _ac(db.D)
    residual = sorted("".join(sorted(s)) for s in S if is_frequent(db.ws(s), XI))
    ok = (tr == ["E@T1", "C@T2", "C@T4"] and hf == F(1, 2) and mc == F(0)
          and ac == F(0) and residual == ["AC"])
    print(f"[g3 safe=True]  trace={' -> '.join(tr)} ; HF={hf} MC={mc} AC={ac} residual={residual} ok={ok}")
    return ok


def test_golden_safe_false():
    db = HidingDB(D, W)
    tr = [f"{v}@{t}" for v, t in mcpriority(db, S, NS, XI, safe_check=False, order="mc_tid")]
    hf, mc, ac = hiding_failure(db, S, XI), missing_cost(db, NS, XI), _ac(db.D)
    lost = sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), XI))
    ok = (tr == ["E@T1", "E@T2", "A@T3"] and hf == F(0) and mc == F(4, 7)
          and ac == F(0) and lost == ["A", "ACD", "AD", "E"])
    print(f"[g3 safe=False] trace={' -> '.join(tr)} ; HF={hf} MC={mc} AC={ac} lost={lost} ok={ok}")
    return ok


def test_safe_fixture():
    """Chứng minh full-check ≠ reduced-check; code DÙNG full (is_safe)."""
    Wf = {"A": F(2, 5), "B": F(1, 10), "C": F(4, 5), "D": F(2, 5)}
    Df = {"T1": set("AB"), "T2": set("BD"), "T3": set("ABC")}
    xi = F(11, 25)
    NSf = [frozenset(x) for x in ["A", "AB", "AC", "B", "BC", "C"]]
    db = HidingDB(Df, Wf)

    full = is_safe(db, "B", "T2", NSf, xi)                       # toàn ~S
    ns_in_t2 = [ns for ns in NSf if ns <= db.D["T2"]]            # reduced: chỉ ns⊆T2
    reduced = is_safe(db, "B", "T2", ns_in_t2, xi)
    ok = (full is False) and (reduced is True)
    print(f"[g3 safe-fixture] Safe_full(B,T2)={full} (exp False) ; "
          f"Safe_reduced(B,T2)={reduced} (exp True) ns⊆T2={sorted(''.join(sorted(n)) for n in ns_in_t2)} ok={ok}")
    return ok


def test_filter_guard():
    """filter ws(s)≥ξ trong T_sensitive PHẢI cho AC=0. Bỏ filter ⇒ AC=1/9 ⇒ FAIL."""
    Wf = {"A": F(3, 10), "B": F(1, 10), "C": F(3, 10), "D": F(4, 5)}
    Df = {"T1": set("ABCD"), "T2": set("ACD"), "T3": set("ABCD"), "T4": set("BC"), "T5": set("ACD")}
    xi = F(41, 100)
    Sf = [frozenset("AC"), frozenset("BC")]
    Wfl = {k: float(v) for k, v in Wf.items()}
    fwi_orig = fwi_itemsets(mine_fwi(Df, Wfl, 0.41))
    NSf = sorted((x for x in fwi_orig if x not in {frozenset("AC"), frozenset("BC")}), key=lambda z: (len(z), sorted(z)))

    db = HidingDB(Df, Wf)
    tr = [f"{v}@{t}" for v, t in mcpriority(db, Sf, NSf, xi, safe_check=True, order="mc_tid")]
    hf = hiding_failure(db, Sf, xi)
    mc = missing_cost(db, NSf, xi)
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wfl, 0.41))
    ac = artificial_cost(fwi_orig, fwi_san)
    ok = (hf == F(1, 2) and mc == F(0) and ac == F(0))
    print(f"[g3 filter-guard] trace={' -> '.join(tr)} ; HF={hf} (exp 1/2) MC={mc} (exp 0) "
          f"AC={ac} (exp 0; nếu 1/9 ⇒ filter hỏng) |~S|={len(NSf)} ok={ok}")
    return ok


def main():
    results = [
        ("golden_safe_true", test_golden_safe_true()),
        ("golden_safe_false", test_golden_safe_false()),
        ("safe_fixture", test_safe_fixture()),
        ("filter_guard", test_filter_guard()),
    ]
    allok = all(ok for _, ok in results)
    print("\nG3", "PASS" if allok else "FAIL",
          "-", ", ".join(f"{n}={'OK' if ok else 'FAIL'}" for n, ok in results))
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
