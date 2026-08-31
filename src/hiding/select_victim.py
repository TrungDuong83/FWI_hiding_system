# -*- coding: utf-8 -*-
"""
src/hiding/select_victim.py — helper two-stage + precompute Score (SPEC §3.4, §3.5).

Score = PER-ITEM, precompute MỘT LẦN, bất biến qua giao dịch/iteration:
    ScoreHFP(v) = |SCov(v)| · w(v)          (Max-Conflict; item nặng & phủ nhiều SFWI)
    ScoreMCP(v) = 1 / (|NSCov(v)| + 1)       (Min-Side-Effect; item phủ nhiều NSFWI bị né)
Quyết định xóa = PER-(item, giao dịch): vòng ngoài (thuật toán) duyệt giao dịch, select_victim
chọn item score cao nhất CÓ MẶT trong chính giao dịch đó.

Tie-break (D2): id TĂNG DẦN, numeric — id nhỏ hơn thắng. id_key numeric CẢ item lẫn TID
(FIMI id số; sort chuỗi "10"<"2" sẽ sai, phá tái lập).
"""
from fractions import Fraction
from collections import defaultdict
from typing import Dict, Iterable, Set, Callable, Optional


def id_key(v):
    """'id tăng dần' = numeric ascending. Item/TID số → int; ngược lại giữ chuỗi."""
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return v


def sensitive_items_of(S: Iterable[Iterable[str]]) -> Set[str]:
    """Tập item xuất hiện trong ít nhất một SFWI (miền victim hợp lệ — Lemma A1)."""
    items: Set[str] = set()
    for s in S:
        items.update(s)
    return items


def scov(S: Iterable[Iterable[str]]) -> Dict[str, int]:
    """SCov(v) = #SFWI chứa v."""
    c: Dict[str, int] = defaultdict(int)
    for s in S:
        for v in s:
            c[v] += 1
    return dict(c)


def nscov(NS: Iterable[Iterable[str]]) -> Dict[str, int]:
    """NSCov(v) = #NSFWI chứa v."""
    c: Dict[str, int] = defaultdict(int)
    for ns in NS:
        for v in ns:
            c[v] += 1
    return dict(c)


def score_hfp(S: Iterable[Iterable[str]], W: Dict[str, float]) -> Dict[str, float]:
    """ScoreHFP(v)=|SCov(v)|·w(v) cho MỌI item trong W (item ngoài S → 0)."""
    sc = scov(S)
    return {v: sc.get(v, 0) * W.get(v, 0) for v in W}


def score_mcp(NS: Iterable[Iterable[str]], W: Dict[str, float]) -> Dict[str, Fraction]:
    """ScoreMCP(v)=1/(|NSCov(v)|+1) cho MỌI item trong W. Fraction → exact (ranking tất định)."""
    ns = nscov(NS)
    return {v: Fraction(1, ns.get(v, 0) + 1) for v in W}


def select_victim(T_k: Iterable[str],
                  sensitive_items: Set[str],
                  score: Dict[str, float],
                  safe: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """
    Chọn victim trong giao dịch T_k (SPEC §3.5).
      Cand = { i ∈ T_k | i ∈ sensitive_items }           # victim BẮT BUỘC ∈ SFWI (Lemma A1)
      sort key = (-score[v], id_key(v))                   # score ↓, tie: id ↑ (D2)
      trả v đầu tiên thỏa safe (nếu có), None nếu không có.
    safe=None: HFPriority / MCPriority(safe_check=False). safe=callable: MCPriority(safe_check=True).
    """
    cand = [i for i in T_k if i in sensitive_items]
    cand.sort(key=lambda v: (-score[v], id_key(v)))
    for v in cand:
        if safe is None or safe(v):
            return v
    return None
