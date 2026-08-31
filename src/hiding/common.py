# -*- coding: utf-8 -*-
"""
src/hiding/common.py — cấu trúc dữ liệu dùng chung cho PART 4 hiding (SPEC §2).

Backend SỐ trung lập: weights truyền vào quyết định kiểu (Fraction cho golden/calibration
exact, float cho production). Lớp KHÔNG tự ép kiểu.

Bẫy #1 (hay sai nhất): xóa một item đổi tw(T_k) ⇒ đổi W_total ⇒ MỌI ws dịch, kể cả itemset
không liên quan. Vì thế `delete()` là CHỖ DUY NHẤT được sửa DB (D, inv, tw_cache, W_total).
Không sửa DB ở bất kỳ nơi nào khác.

    tw(t)   = Σ_{i∈D[t]} W[i] / |D[t]|
    W_total = Σ_t tw(t)
    ws(X)   = Σ_{t ∈ ⋂_{i∈X} inv[i]} tw_cache[t] / W_total
"""
from typing import Dict, Set, Iterable


class HidingDB:
    """
    Giữ trạng thái CSDL có trọng số cho pha hiding. Mọi cập nhật đi qua delete().

    D  : {tid -> set(item)}
    W  : {item -> weight}          (đã chuẩn hóa, do caller cấp)
    inv: {item -> set(tid)}        inverted index (Def 11), cập nhật khi xóa
    tw_cache : {tid -> tw(tid)}    cache, cập nhật khi xóa
    W_total  : Σ tw, biến chạy — cập nhật MỖI lần xóa
    """

    def __init__(self, D: Dict[str, Set[str]], W: Dict[str, float]):
        self.D = {t: set(s) for t, s in D.items()}
        self.W = dict(W)
        self.inv: Dict[str, Set[str]] = {}
        for t, s in self.D.items():
            for i in s:
                self.inv.setdefault(i, set()).add(t)
        self.tw_cache = {t: self._compute_tw(t) for t in self.D}
        self.W_total = sum(self.tw_cache.values())

    def _compute_tw(self, t: str):
        """tw(t) = Σ W[i] / |t| ; giao dịch rỗng → 0 (không chia 0)."""
        s = self.D[t]
        if not s:
            return 0
        return sum(self.W.get(i, 0) for i in s) / len(s)

    def tw(self, t: str):
        """tw đã cache (bất biến trừ khi delete cập nhật)."""
        return self.tw_cache[t]

    def cover(self, X: Iterable[str]) -> Set[str]:
        """⋂_{i∈X} inv[i] = tập tid chứa TẤT CẢ item của X. X rỗng → mọi tid."""
        sets = [self.inv.get(i, set()) for i in X]
        if not sets:
            return set(self.D.keys())
        return set.intersection(*sets)

    def ws(self, X: Iterable[str]):
        """ws(X) = Σ_{t⊇X} tw_cache[t] / W_total (theo W_total HIỆN TẠI — Bẫy #1)."""
        if self.W_total == 0:
            return 0
        return sum(self.tw_cache[t] for t in self.cover(X)) / self.W_total

    def delete(self, v: str, t: str) -> None:
        """
        CHỖ DUY NHẤT sửa DB. Xóa item v khỏi giao dịch t và cập nhật đồng bộ
        inv, tw_cache, W_total. Idempotent-an toàn: nếu v∉D[t] thì không đổi gì
        (discard không lỗi, tw không đổi ⇒ W_total giữ nguyên).
        """
        if v not in self.D.get(t, ()):        # không có gì để xóa → no-op sạch
            return
        self.D[t].discard(v)
        self.inv[v].discard(t)
        tw_old = self.tw_cache[t]
        tw_new = self._compute_tw(t)
        self.W_total += tw_new - tw_old       # cập nhật W_total (Bẫy #1)
        self.tw_cache[t] = tw_new
