# -*- coding: utf-8 -*-
"""
src/hiding/baseline_ppum.py — Baseline PPUM (MSU-MAU + MSU-MIU) cho §V, FWI-deletion.

Faithful SPEC_BASELINE.md §3 (port Algorithm 1/2 của Lin et al., EAAI 55, 2016 sang tw/ws;
GIỮ nguyên nguyên lý, chỉ đổi thao tác thành *item deletion*). Cặp bracket hai failure-mode
qua Weight Transformation: MAU xóa item NẶNG (W_total↓ → regime AC), MIU xóa item NHẸ
(W_total↑ → regime MC).

Preprocessing chung (§3):
    f(i)   = |SCov(i)| = #{X∈S : i∈X}                     # occurrence frequency
    owt(X) = Σ_{i∈X} f(i)                                 # overlapping weight
    duyệt S theo owt GIẢM DẦN (tie: ws(X) desc; tie: lexicographic)

MSU-MAU (Alg 1, DYNAMIC max-tw):
    v* = argmax_{i∈X} w(i)   (tie: item-id nhỏ)           # bất biến qua giao dịch (adaptation §2.1)
    while ws(X) ≥ ξ:  T* = argmax_{T∈cover(X)} tw(T)  (RE-SELECT ĐỘNG; tie TID nhỏ); delete v*@T*

MSU-MIU (Alg 2, STATIC pre-sort):
    if ws(X) < ξ: bỏ qua
    v* = argmin_{i∈X} w(i)   (tie: item-id nhỏ)
    cover_sorted = sort cover(X) theo tw GIẢM DẦN (TĨNH 1 LẦN; tie TID nhỏ)
    for T* in cover_sorted:  if ws(X)<ξ: break; if X⊆D[T*]: delete v*@T*

RANH GIỚI (SPEC_BASELINE §2/§3, prompt §2): KHÔNG Safe()/no-op/né-non-sensitive; KHÔNG nhánh
giảm-quantity (FWI không quantity ⇒ luôn xóa); KHÔNG `select_victim` (baseline có victim-rule
riêng); reuse `HidingDB.delete` (Bẫy #1) + `metrics.is_frequent` cho test ws≥ξ. Baseline luôn
ẩn hết ⇒ HF=0 (không no-op).

Chữ ký theo kiểu hfpriority/mcpriority (prompt §6): nhận `db: HidingDB` (giữ cả D lẫn W), mutate
tại chỗ (DB' = db.D sau khi chạy), trả `trace = list[(item, tid)]`.
"""
import os
import sys

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ("hiding", "metrics"):
    _p = os.path.join(_SRC, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from metrics import is_frequent          # noqa: E402  (membership dùng CHUNG với HFP/MCP/metrics)


# --------------------------- helpers (local; KHÔNG dùng select_victim) ---------------------------
def _idkey(v):
    """item-id/TID tăng dần numeric (id số → int; ngược lại giữ chuỗi)."""
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return v


def _tid_num(t):
    """TID 'T<số>' → số (tie TID nhỏ). Fallback _idkey."""
    tail = t[1:] if (len(t) > 1 and t[0] == "T") else t
    return int(tail) if tail.isdigit() else _idkey(t)


def scov_count(S):
    """f(i) = |SCov(i)| = số SFWI chứa i."""
    f = {}
    for X in S:
        for i in X:
            f[i] = f.get(i, 0) + 1
    return f


def victim_item(X, W, mode):
    """v*(X): mode='max' → argmax w(i); 'min' → argmin w(i). Tie: item-id nhỏ. Bất biến qua giao dịch."""
    best = None
    best_w = None
    for i in sorted(X, key=_idkey):          # duyệt id tăng ⇒ strict so sánh giữ id nhỏ khi tie
        w = W.get(i, 0)
        if best is None or (w > best_w if mode == "max" else w < best_w):
            best, best_w = i, w
    return best


def preprocess_order(db, S, f=None):
    """
    Sắp S theo owt(X)=Σ_{i∈X} f(i) GIẢM DẦN; tie ws(X) desc; tie lexicographic (id-numeric tuple).
    f: dict item->trọng số thứ tự (mặc định |SCov|). CHỈ đổi THỨ TỰ, không đụng victim-rule (§5 gate).
    """
    S = [frozenset(X) for X in S]
    if f is None:
        f = scov_count(S)

    def owt(X):
        return sum(f.get(i, 0) for i in X)

    return sorted(S, key=lambda X: (-owt(X), -db.ws(X), tuple(sorted(X, key=_idkey))))


# --------------------------------- MSU-MAU (Alg 1) ---------------------------------
def run_msu_mau(db, S, xi, round3=False):
    """MSU-MAU: victim item = max w; victim txn = argmax tw RE-SELECT ĐỘNG mỗi vòng. Trả trace."""
    order = preprocess_order(db, S)
    sensitive_items = set().union(*[set(X) for X in order]) if order else set()
    phi0 = sum(len(db.D[t] & sensitive_items) for t in db.D)          # chặn trên #deletion
    deletions = 0
    trace = []
    for X in order:
        v = victim_item(X, db.W, "max")                              # precompute 1 lần / X (bất biến)
        while is_frequent(db.ws(X), xi, round3):                     # thay du>0; test exact ws≥ξ
            cover = db.cover(X)
            Tstar = min(cover, key=lambda t: (-db.tw(t), _tid_num(t)))  # argmax tw, tie TID nhỏ (ĐỘNG)
            db.delete(v, Tstar)                                      # xóa item (reuse delete — Bẫy #1)
            trace.append((v, Tstar))
            deletions += 1
            if deletions > phi0:
                raise RuntimeError("MSU-MAU vượt Φ0 — logic sai (không dừng)")
    return trace


# --------------------------------- MSU-MIU (Alg 2) ---------------------------------
def run_msu_miu(db, S, xi, round3=False):
    """MSU-MIU: victim item = min w; cover sort tw-desc TĨNH 1 LẦN rồi duyệt tuần tự. Trả trace."""
    order = preprocess_order(db, S)
    trace = []
    for X in order:
        if not is_frequent(db.ws(X), xi, round3):                   # Alg2 l.6-8
            continue
        v = victim_item(X, db.W, "min")
        cover_sorted = sorted(db.cover(X), key=lambda t: (-db.tw(t), _tid_num(t)))  # TĨNH 1 LẦN
        for Tstar in cover_sorted:
            if not is_frequent(db.ws(X), xi, round3):
                break
            if X <= db.D[Tstar]:                                    # giao dịch còn chứa X?
                db.delete(v, Tstar)
                trace.append((v, Tstar))
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
    XI = F(55, 100)

    for name, fn in (("MSU-MAU", run_msu_mau), ("MSU-MIU", run_msu_miu)):
        db = HidingDB(D, W)
        tr = fn(db, S, XI)
        print(f"[{name} smoke] trace =", " -> ".join(f"{v}@{t}" for v, t in tr))
