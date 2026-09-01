# -*- coding: utf-8 -*-
"""
src/hiding/mcpriority.py — MCPriority (Min-Side-Effect, SPEC §3.3).

Ưu tiên bảo toàn NSFWI: CHỈ safe deletion + dừng no-op ⇒ MC=0, AC=0 BY CONSTRUCTION,
chấp nhận HF>0. Tham số: safe_check∈{True,False}, order∈{'mc_tid','tw_desc'}.

    While (∃ s∈S : ws(s) ≥ ξ):
        T_sensitive = { T_k | ∃ s∈S : s⊆T_k ∧ ws(s)≥ξ }         # CÓ filter ws(s)≥ξ
        order='mc_tid'  → duyệt theo TID tăng (numeric)          # cấu hình chính thức (D1)
        order='tw_desc' → sort tw giảm (tie TID↑)                # ablation E5
        movedThisPass = False
        for T_k:
            safe = (λ v: Safe(v,T_k)) if safe_check else None
            v = select_victim(D[T_k], sensitive_items, ScoreMCP, safe)
            if v: delete(v,T_k); movedThisPass=True; if ẩn hết: break
        if not movedThisPass: break        # NO-OP minh bạch (full-pass-no-move)

Safe(v,T_k) — FULL-CHECK TOÀN BỘ ~S theo W'_total MỚI (SPEC §3.3; KHÔNG reduced, KHÔNG fast-path):
    n=|T_k| ; Ssum=Σ_{i∈T_k} w(i) ; tw_old=Ssum/n ; tw_new=(Ssum-w(v))/(n-1)
    Δ=tw_new-tw_old ; W'_total=W_total+Δ
    ∀ns∈~S:  ns⊄T_k → num'=num(ns) ; v∉ns → num'=num(ns)-tw_old+tw_new ; v∈ns → num'=num(ns)-tw_old
             nếu ws'(ns)=num'/W'_total < ξ  ⇒  return False
    return True

REUSE nguyên common.HidingDB / select_victim / metrics (frozen). Mutate `db` tại chỗ, trả trace.
"""
import os
import sys

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ("hiding", "metrics"):
    _p = os.path.join(_SRC, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from select_victim import select_victim, sensitive_items_of, score_mcp, id_key   # noqa: E402
from metrics import is_frequent                                                  # noqa: E402


def _tid_num(t):
    """TID tăng dần numeric (CLAUDE §B.3). 'T<số>' → số; fallback id_key."""
    tail = t[1:] if (len(t) > 1 and t[0] == "T") else t
    return int(tail) if tail.isdigit() else id_key(t)


def is_safe(db, v, tk, NS, xi, round3=False) -> bool:
    """
    Safe(v,T_k): FULL-CHECK toàn ~S theo W'_total mới (SPEC §3.3). True ⟺ xóa v khỏi T_k
    KHÔNG làm bất kỳ ns∈~S nào tụt dưới ξ. KHÔNG reduced 'chỉ ns⊆T_k', KHÔNG fast-path.
    """
    D_tk = db.D[tk]
    n = len(D_tk)
    if n < 2:                                  # tiền điều kiện |T_k|≥2 (không rỗng hóa)
        return False
    tw_old = db.tw(tk)
    wv = db.W.get(v, 0)
    Ssum = tw_old * n
    tw_new = (Ssum - wv) / (n - 1)
    Wp = db.W_total + (tw_new - tw_old)        # W'_total
    if Wp <= 0:
        return False
    for ns in NS:
        cov = db.cover(ns)
        num = sum(db.tw_cache[t] for t in cov)
        if tk not in cov:                      # ns ⊄ T_k : T_k không đóng góp
            nump = num
        elif v not in ns:                      # T_k vẫn ⊇ ns : đổi tw
            nump = num - tw_old + tw_new
        else:                                  # v∈ns : T_k rời cover(ns)
            nump = num - tw_old
        if not is_frequent(nump / Wp, xi, round3):
            return False
    return True


def mcpriority(db, S, NS, xi, score=None, safe_check=True, order="mc_tid", round3=False):
    """
    db: common.HidingDB (mutate). S: SFWI (|X|≥2). NS: ~S=FWI(orig)\\S (đóng băng từ DB gốc).
    score: ScoreMCP precomputed (None → tự tính từ NS, db.W). Trả: trace = list[(item, tid)].
    """
    S = [frozenset(s) for s in S]
    NS = [frozenset(x) for x in NS]
    sensitive_items = sensitive_items_of(S)
    if score is None:
        score = score_mcp(NS, db.W)

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

        if order == "mc_tid":
            ordered = sorted(t_sensitive, key=_tid_num)
        elif order == "tw_desc":
            ordered = sorted(t_sensitive, key=lambda t: (-db.tw(t), _tid_num(t)))
        else:
            raise ValueError(f"order không hợp lệ: {order!r}")

        moved = False
        for tk in ordered:
            safe = (lambda v, _tk=tk: is_safe(db, v, _tk, NS, xi, round3)) if safe_check else None
            victim = select_victim(db.D[tk], sensitive_items, score, safe)
            if victim is not None:
                db.delete(victim, tk)
                trace.append((victim, tk))
                moved = True
                deletions += 1
                if deletions > phi0:
                    raise RuntimeError("MCPriority vượt Φ0 — logic sai (không dừng)")
                if not exposed_any():
                    break
        if not moved:                          # NO-OP: full-pass-no-move → DỪNG (HF>0 hợp lệ)
            break
    return trace


if __name__ == "__main__":
    import logging
    from fractions import Fraction as F
    logging.disable(logging.CRITICAL)
    from common import HidingDB

    W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    S = [frozenset("AC"), frozenset("CE")]
    NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]
    XI = F(55, 100)

    for sc in (True, False):
        db = HidingDB(D, W)
        tr = mcpriority(db, S, NS, XI, safe_check=sc, order="mc_tid")
        print(f"[mcpriority smoke safe={sc}] trace =", " -> ".join(f"{v}@{t}" for v, t in tr))
