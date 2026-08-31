# -*- coding: utf-8 -*-
"""
src/hiding/hfpriority.py — HFPriority (Max-Conflict, SPEC §3.2).

Ưu tiên ẩn nhanh: KHÔNG safe-check ⇒ HF→0, MC có thể cao (đặc tính chấp nhận được).

    While (∃ s∈S : ws(s) ≥ ξ):
        T_sensitive = { T_k | ∃ s∈S : s ⊆ T_k ∧ ws(s) ≥ ξ }      # CÓ filter ws(s)≥ξ
        sort T_sensitive theo tw GIẢM DẦN (tie: TID tăng dần, numeric)
        for T_k in T_sensitive:
            v = select_victim(D[T_k], sensitive_items, ScoreHFP, safe=None)
            if v: delete(v, T_k)                                   # 1 deletion / lần thăm giao dịch
                  if (∀ s∈S: ws(s) < ξ): break
Termination (A3.1): Φ = tổng vị trí item-của-S giảm ngặt mỗi delete ⇒ hữu hạn (không cần no-op).

REUSE nguyên common.HidingDB / select_victim / metrics (frozen). Mutate `db` tại chỗ, trả trace.
"""
import os
import sys

# bootstrap path (repo dùng module phẳng, không package) — tự định vị sibling src dirs
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ("hiding", "metrics"):
    _p = os.path.join(_SRC, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from select_victim import select_victim, sensitive_items_of, score_hfp, id_key   # noqa: E402
from metrics import is_frequent                                                  # noqa: E402


def _tid_order_key(db, t):
    """Sort T_sensitive: tw GIẢM DẦN, tie TID TĂNG DẦN numeric (CLAUDE §B.3).
    TID dạng 'T<số>' (loader) → tách số; fallback id_key nếu khác format."""
    tail = t[1:] if (len(t) > 1 and t[0] == "T") else t
    tk = int(tail) if tail.isdigit() else id_key(t)
    return (-db.tw(t), tk)


def hfpriority(db, S, xi, score=None, round3=False):
    """
    db: common.HidingDB (mutate tại chỗ). S: iterable SFWI (|X|≥2). xi: ngưỡng.
    score: ScoreHFP precomputed (None → tự tính từ S, db.W). round3: membership production.
    Trả: trace = list[(item, tid)] theo thứ tự xóa.
    """
    S = [frozenset(s) for s in S]
    sensitive_items = sensitive_items_of(S)
    if score is None:
        score = score_hfp(S, db.W)

    # Φ0 = tổng vị trí item-thuộc-S trong DB (chặn trên #deletion, A3.1) — bảo vệ vòng lặp
    phi0 = sum(len(db.D[t] & sensitive_items) for t in db.D)
    deletions = 0
    trace = []

    def exposed_any():
        return any(is_frequent(db.ws(s), xi, round3) for s in S)

    while exposed_any():
        exposed = [s for s in S if is_frequent(db.ws(s), xi, round3)]   # filter ws(s)≥ξ
        t_sensitive = set()
        for s in exposed:
            t_sensitive |= db.cover(s)
        order = sorted(t_sensitive, key=lambda t: _tid_order_key(db, t))

        moved = False
        for tk in order:
            v = select_victim(db.D[tk], sensitive_items, score, safe=None)
            if v is not None:
                db.delete(v, tk)
                trace.append((v, tk))
                moved = True
                deletions += 1
                if deletions > phi0:                      # A3.1: không thể vượt Φ0
                    raise RuntimeError("HFPriority vượt Φ0 — logic sai (không dừng)")
                if not exposed_any():
                    break
        if not moved:                                     # input hợp lệ: không xảy ra
            break
    return trace


if __name__ == "__main__":
    import logging
    from fractions import Fraction as F
    logging.disable(logging.CRITICAL)
    sys.path.insert(0, os.path.join(_SRC, "mining"))
    from common import HidingDB

    W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    S = [frozenset("AC"), frozenset("CE")]
    db = HidingDB(D, W)
    tr = hfpriority(db, S, F(55, 100))
    print("[hfpriority smoke] trace =", " -> ".join(f"{v}@{t}" for v, t in tr))
