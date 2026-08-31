# -*- coding: utf-8 -*-
"""
src/metrics/metrics.py — 4 metric FWI (SPEC §5). CHỈ HF, MC, AC, RT.
KHÔNG IUS/DUS/TMR/DDI (dựa TU=Σw·qty, sai định nghĩa FWI).

    HF = |{s∈S  : ws_san(s) ≥ ξ}| / |S|        # SFWI CÒN LỘ (0 = ẩn hết)
    MC = |{ns∈~S : ws_san(ns) < ξ}| / |~S|      # NSFWI MẤT (side effect)
    AC = |FWI(san) \ FWI(orig)| / |FWI(san)|    # itemset "ma"; guard |FWI(san)|=0 → 0
    RT = wall-clock CHỈ pha hiding.

- HF/MC recompute `ws` trên DB đã sanitize qua `common.HidingDB.ws` ⇒ dùng **W_total hiện tại**
  (Bẫy #1). `S` đóng băng từ DB gốc; `~S` = FWI(orig) \ S đóng băng từ DB gốc.
- Membership: golden/calibration = exact (`ws ≥ ξ`, Fraction); production = `round(ws,3) ≥ ξ` (float64)
  → tham số `round3`.
- AC re-mine ĐẦY ĐỦ bằng `miner.mine_fwi` (do CALLER thực hiện, truyền vào 2 tập itemset). Module này
  thuần: chỉ tiêu thụ `db` (duck-typed `.ws`) + các tập frozenset ⇒ không phụ thuộc miner/common.

Backend số trung lập: trả `Fraction(a,b)` (exact); trình bày ×100% ở lớp report.
"""
import time
from contextlib import contextmanager
from fractions import Fraction
from typing import Iterable, FrozenSet, Set, Dict


def _ratio(num: int, den: int) -> Fraction:
    """num/den exact; den=0 → 0 (guard chia 0)."""
    return Fraction(num, den) if den else Fraction(0)


def is_frequent(ws_val, xi, round3: bool = False) -> bool:
    """FWI membership. round3=True: round(ws,3) ≥ ξ (production float64). Ngược lại exact."""
    if round3:
        return round(float(ws_val), 3) >= xi
    return ws_val >= xi


def hiding_failure(db, S: Iterable[Iterable[str]], xi, round3: bool = False) -> Fraction:
    """HF = #SFWI còn lộ / |S|. |S|=0 → 0."""
    S = list(S)
    exposed = sum(1 for s in S if is_frequent(db.ws(s), xi, round3))
    return _ratio(exposed, len(S))


def missing_cost(db, NS: Iterable[Iterable[str]], xi, round3: bool = False) -> Fraction:
    """MC = #NSFWI mất (ws<ξ) / |~S|. |~S|=0 → 0."""
    NS = list(NS)
    lost = sum(1 for ns in NS if not is_frequent(db.ws(ns), xi, round3))
    return _ratio(lost, len(NS))


def artificial_cost(fwi_orig: Set[FrozenSet[str]], fwi_san: Set[FrozenSet[str]]) -> Fraction:
    """AC = |FWI(san)\\FWI(orig)| / |FWI(san)|. |FWI(san)|=0 → 0 (guard)."""
    if not fwi_san:
        return Fraction(0)
    phantom = fwi_san - fwi_orig
    return _ratio(len(phantom), len(fwi_san))


@contextmanager
def measure_runtime():
    """RT: wall-clock CHỈ pha hiding. Dùng: `with measure_runtime() as rt: ...`; rt() = giây."""
    t0 = time.perf_counter()
    elapsed = {"v": None}
    try:
        yield lambda: (time.perf_counter() - t0) if elapsed["v"] is None else elapsed["v"]
    finally:
        elapsed["v"] = time.perf_counter() - t0


def evaluate(db, S, NS, xi,
             fwi_orig: Set[FrozenSet[str]], fwi_san: Set[FrozenSet[str]],
             runtime: float, round3: bool = False) -> Dict[str, object]:
    """Gộp 4 metric thành dict. AC nhận sẵn 2 tập FWI (caller mine bằng miner.mine_fwi)."""
    return {
        "HF": hiding_failure(db, S, xi, round3),
        "MC": missing_cost(db, NS, xi, round3),
        "AC": artificial_cost(fwi_orig, fwi_san),
        "RT": runtime,
    }


if __name__ == "__main__":
    # Unit verify (hand-computed): áp KẾT QUẢ golden HFPriority `C@T3 → C@T1` lên running example,
    # metrics phải cho HF=0, MC=3/7 (mất {C,CD,ACD}), AC=0. Tính tay đã khớp (W_total→379/120,
    # ws(AC)=135/379, ws(CE)=187/379 đều <0.55; lost đúng {C,CD,ACD}).
    import os
    import sys
    from fractions import Fraction as F
    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(os.path.dirname(HERE))
    sys.path.insert(0, os.path.join(ROOT, "src", "hiding"))
    sys.path.insert(0, os.path.join(ROOT, "src", "mining"))
    import logging
    logging.disable(logging.CRITICAL)
    from common import HidingDB
    from miner import mine_fwi, fwi_itemsets

    W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    XI = F(55, 100)
    S = [frozenset("AC"), frozenset("CE")]
    NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]

    db = HidingDB(D, W)
    db.delete("C", "T3")
    db.delete("C", "T1")

    hf = hiding_failure(db, S, XI)
    mc = missing_cost(db, NS, XI)
    # AC: mine FWI(orig) và FWI(san) (engine float, ws bất biến scale)
    Wf = {k: float(v) for k, v in W.items()}
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, 0.55))
    ac = artificial_cost(fwi_orig, fwi_san)

    lost = [("".join(sorted(ns))) for ns in NS if not is_frequent(db.ws(ns), XI)]
    ok = (hf == F(0)) and (mc == F(3, 7)) and (ac == F(0)) and (sorted(lost) == ["ACD", "C", "CD"])
    print(f"[metrics unit] HF={hf} (exp 0) MC={mc} (exp 3/7) AC={ac} (exp 0) lost={sorted(lost)}")
    print("METRICS UNIT", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
