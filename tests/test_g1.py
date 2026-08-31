# -*- coding: utf-8 -*-
"""
tests/test_g1.py — Gate G1: nền hiding (common/select_victim/preprocess) khớp running example.

Chuẩn (SPEC §6, CLAUDE §B.6), backend Fraction (exact):
  W = {A:.9,B:.4,C:.7,D:.5,E:.2}; D: T1=ACDE T2=BCE T3=ACD T4=ABCE T5=ACDE T6=BDE ; ξ=0.55
  W_total=16/5 ; ws(AC)=3/4 ; FWI(0.55)=9 tập {A,C,D,E,AC,AD,CD,CE,ACD}
  ScoreHFP: A=.9,B=0,C=1.4,D=0,E=.2   ; ScoreMCP: A=1/4,B=1,C=1/4,D=1/5,E=1/2
  delete cập nhật W_total đúng (Bẫy #1); xóa C∈AC khỏi T1 ⇒ ws(AC) giảm ngặt (A1).
Entry-guarded; exit != 0 nếu FAIL.
"""
import os
import sys
import logging
from fractions import Fraction as F
from itertools import combinations

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "hiding"))
sys.path.insert(0, os.path.join(ROOT, "src", "mining"))
sys.path.insert(0, os.path.join(ROOT, "src", "datautil"))

from common import HidingDB                                               # noqa: E402
from select_victim import (                                              # noqa: E402
    score_hfp, score_mcp, select_victim, sensitive_items_of,
)
import preprocess                                                        # noqa: E402
from miner import mine_fwi, fwi_itemsets                                 # noqa: E402

# ---- Running example (Fraction exact) ----
W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
XI = F(55, 100)
S = [frozenset("AC"), frozenset("CE")]            # SFWI
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]   # NSFWI
GOLDEN_FWI = {"A", "C", "D", "E", "AC", "AD", "CD", "CE", "ACD"}


def test_wtotal_wsAC():
    db = HidingDB(D, W)
    ok1 = db.W_total == F(16, 5)
    ok2 = db.ws("AC") == F(3, 4)
    print(f"[wtotal/ws] W_total={db.W_total} (exp 16/5) ok={ok1} ; ws(AC)={db.ws('AC')} (exp 3/4) ok={ok2}")
    return ok1 and ok2


def test_fwi_count():
    """Đếm FWI qua HidingDB.ws (độc lập engine) — phải == 9 tập golden."""
    db = HidingDB(D, W)
    items = sorted(W)
    got = set()
    for r in range(1, len(items) + 1):
        for c in combinations(items, r):
            if db.ws(c) >= XI:
                got.add("".join(sorted(c)))
    ok = got == GOLDEN_FWI
    print(f"[fwi_count] #{len(got)} match={ok} diff={got ^ GOLDEN_FWI}")
    return ok


def test_scores():
    hfp = score_hfp(S, W)
    mcp = score_mcp(NS, W)
    exp_hfp = {"A": F(9, 10), "B": F(0), "C": F(14, 10), "D": F(0), "E": F(2, 10)}
    exp_mcp = {"A": F(1, 4), "B": F(1), "C": F(1, 4), "D": F(1, 5), "E": F(1, 2)}
    ok1 = hfp == exp_hfp
    ok2 = mcp == exp_mcp
    print(f"[score_hfp] {{ {', '.join(f'{k}:{hfp[k]}' for k in sorted(hfp))} }} ok={ok1}")
    print(f"[score_mcp] {{ {', '.join(f'{k}:{mcp[k]}' for k in sorted(mcp))} }} ok={ok2}")
    # HFPriority victim trên T3=ACD phải là C (max ScoreHFP giữa {A,C})
    v = select_victim(D["T3"], sensitive_items_of(S), hfp, safe=None)
    ok3 = v == "C"
    print(f"[select_victim] victim(T3=ACD, HFP) = {v} (exp C) ok={ok3}")
    return ok1 and ok2 and ok3


def test_delete_updates_wtotal():
    db = HidingDB(D, W)
    ws_ac_before = db.ws("AC")
    db.delete("C", "T1")                       # xóa C∈AC khỏi T1
    # 1) inv & D cập nhật
    ok_inv = ("T1" not in db.inv["C"]) and ("C" not in db.D["T1"])
    # 2) W_total khớp recompute-from-scratch trên D đã sửa (Bẫy #1)
    fresh = HidingDB(db.D, W)
    ok_wt = db.W_total == fresh.W_total
    # 3) ws(AC) giảm NGẶT (Lemma A1) và bằng giá trị tính tay
    ws_ac_after = db.ws("AC")
    # cover(AC) sau xóa = {T3,T4,T5}; num=0.7+0.55+0.575=1.825=73/40
    twT1_new = (W["A"] + W["D"] + W["E"]) / 3          # T1=ADE
    Wtot_new = F(16, 5) - F(23, 40) + twT1_new         # 23/40 = tw(ACDE)
    exp_ws_after = F(73, 40) / Wtot_new
    ok_val = ws_ac_after == exp_ws_after
    ok_dec = ws_ac_after < ws_ac_before
    print(f"[delete] inv/D ok={ok_inv} ; W_total match fresh ok={ok_wt} ; "
          f"ws(AC) {ws_ac_before} -> {ws_ac_after} (exp {exp_ws_after}) val_ok={ok_val} strict_dec={ok_dec}")
    return ok_inv and ok_wt and ok_val and ok_dec


def test_preprocess():
    # /10 invariance: FWI(W) == FWI(W/10) trên running example.
    # Engine = backend float64 production (SPEC §2) ⇒ dùng float ξ/weights; phần exact do HidingDB.
    Wf = {k: float(v) for k, v in W.items()}
    Wf10 = {k: v / 10 for k, v in Wf.items()}
    fwi_raw = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_scaled = fwi_itemsets(mine_fwi(D, Wf10, 0.55))
    ok_inv = fwi_raw == fwi_scaled and len(fwi_raw) == 9
    # validate_sfwi: singleton bị cấm
    ok_sing = False
    try:
        preprocess.validate_sfwi([frozenset("A")])
    except ValueError:
        ok_sing = True
    # validate_weights: cảnh báo w<=0
    warns = preprocess.validate_weights({"X": 0, "Y": F(3, 10)}, items=["X", "Y", "Z"])
    ok_warn = any("≤ 0" in w for w in warns) and any("không có weight" in w for w in warns)
    print(f"[preprocess] /10-invariant FWI ok={ok_inv} ; validate_sfwi(singleton) raises={ok_sing} ; "
          f"validate_weights warns ok={ok_warn}")
    return ok_inv and ok_sing and ok_warn


def main():
    results = [
        ("wtotal/ws", test_wtotal_wsAC()),
        ("fwi_count", test_fwi_count()),
        ("scores", test_scores()),
        ("delete", test_delete_updates_wtotal()),
        ("preprocess", test_preprocess()),
    ]
    allok = all(ok for _, ok in results)
    print("\nG1", "PASS" if allok else "FAIL",
          "-", ", ".join(f"{n}={'OK' if ok else 'FAIL'}" for n, ok in results))
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
