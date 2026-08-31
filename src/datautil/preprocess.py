# -*- coding: utf-8 -*-
"""
src/datautil/preprocess.py — load + chuẩn hóa /10 + bỏ qty + kiểm định dạng (SPEC §4).

- Loader đọc format FIMI '<item>:<qty> ...'; qty ĐƯỢC ĐỌC nhưng BỎ QUA ở bước dùng cho FWI
  (tw = Σw/|T|, không quantity). Trả D dạng {tid -> set(item)}.
- Chuẩn hóa weight /10 (Q4) → [0,1]. ws bất biến theo scale ⇒ FWI set y hệt ∀ξ; /10 chỉ đổi
  trình bày. Có tùy chọn Fraction (exact) cho golden/calibration.
- Kiểm định dạng: warn item không có weight; warn w(i) ≤ 0 (phá w>0); error SFWI singleton |X|<2.
"""
from fractions import Fraction
from typing import Dict, Set, Iterable, List, Tuple


def load_transactions(filepath: str) -> Dict[str, Set[str]]:
    """Đọc '<item>:<qty> ...' -> {tid: set(item)}. qty BỎ QUA (FWI dùng tw=Σw/|T|)."""
    D: Dict[str, Set[str]] = {}
    with open(filepath, "r") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            items = {part.split(":")[0] if ":" in part else part for part in line.split()}
            if items:
                D[f"T{i + 1}"] = items
    return D


def load_weights(filepath: str, normalize: int = 10, use_fraction: bool = False) -> Dict[str, float]:
    """
    Đọc '<item>:<w>' hoặc '<item>,<w>' -> {item: w/normalize}.
    use_fraction=True → Fraction exact (weight FIMI là số nguyên nên w/10 exact).
    normalize=1 để giữ raw (không /10).
    """
    W: Dict[str, float] = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.replace(",", ":").split(":")
            if len(parts) >= 2:
                item, raw = parts[0], parts[1]
                if use_fraction:
                    W[item] = Fraction(raw) / normalize
                else:
                    W[item] = float(raw) / normalize
    return W


def validate_weights(W: Dict[str, float], items: Iterable[str] = ()) -> List[str]:
    """warn item không có weight (trong `items`) + warn w(i) ≤ 0. Trả list cảnh báo (không raise)."""
    warns: List[str] = []
    for i in items:
        if i not in W:
            warns.append(f"[warn] item {i!r} không có weight (mặc định 0.0)")
    for i, w in W.items():
        if w <= 0:
            warns.append(f"[warn] w({i!r})={w} ≤ 0 — phá giả định w>0 (Lemma A1)")
    return warns


def validate_sfwi(S: Iterable[Iterable[str]]) -> None:
    """error nếu có SFWI singleton |X|<2 (phá §3.1, van dừng C5.2). Raise ValueError."""
    for s in S:
        if len(set(s)) < 2:
            raise ValueError(f"SFWI singleton bị cấm (|X|<2): {sorted(set(s))!r} — xem C5.2")


def load_dataset(trans_path: str, weight_path: str,
                 normalize: int = 10, use_fraction: bool = False
                 ) -> Tuple[Dict[str, Set[str]], Dict[str, float], List[str]]:
    """Tiện ích: load D + W (đã /normalize) + trả cảnh báo weight. Không raise ở đây."""
    D = load_transactions(trans_path)
    W = load_weights(weight_path, normalize=normalize, use_fraction=use_fraction)
    all_items: Set[str] = set()
    for s in D.values():
        all_items |= s
    warns = validate_weights(W, all_items)
    return D, W, warns
