# VIEC_CALIBRATE — calibrate ξ + freeze SFWI (7 dataset)

> Deliverable: `calibration/calib_<ds>.json` (7 dataset) + `calibration/calibrate.py` +
> `tests/test_calib_gates.py`. Faithful SPEC_CALIBRATION.md. Backend freeze = `Fraction` (exact).
> Mọi số dưới đây là output THẬT (không ghi-theo-verify). 1 pha: calibrate + freeze → DỪNG (không §V).

## Bảng kết quả (frozen)
| dataset | ξ | #FWI | #candidate | #SFWI | max\|X\|(FWI) |
|---|---|---|---|---|---|
| chess_fimi | 0.920 | 293 | 280 | 28 | 6 |
| mushroom | 0.457 | 299 | 282 | 28 | 6 |
| retail | 0.008 | 241 | 141 | 14 | 4 |
| accident | 0.751 | 299 | 285 | 28 | 6 |
| bms-pos | 0.021 | 276 | 211 | 21 | 4 |
| kosarak | 0.011 | 263 | 220 | 22 | 5 |
| chainstore | 0.003 | 264 | 13 | 10 | 2 |

- #FWI ∈ [50,300] ✔ mọi dataset (ξ nhỏ nhất cho biên thấp của dải).
- #SFWI = clamp(round(0.1·#candidate), 10, 40): vd accident round(28.5)=28, chainstore round(1.3)=1→clamp 10.
- chainstore rất thưa: #FWI=264 nhưng chỉ 13 candidate (|X|≥2 ∧ ws>ξ) — phần lớn FWI là singleton;
  #SFWI chạm sàn clamp = 10.

## Cơ chế (SPEC_CALIBRATION)
- **Sweep ξ:** binary search đa-mức (0.05→0.01→0.001) trên #FWI đơn điệu giảm theo ξ; chọn ξ **nhỏ
  nhất** (≤3dp) còn #FWI≤300 (và ≥50). Engine (miner Đợt A, đã vá) dùng để đếm #FWI (float, nhanh).
- **Freeze exact (Fraction):** ws tính lại chính xác trên itemset đã mine bằng targeted inverted index
  (chỉ item xuất hiện trong FWI ⇒ không dựng full-DB cho dataset 1M-tx); re-filter ws≥ξ exact.
- **Chọn SFWI:** candidate = FWI {|X|≥2 ∧ ws>ξ}; overlap_score(X)=Σ_{i∈X} pop(i), pop(i)=#candidate
  chứa i ("độ phổ biến item trong không gian NSFWI, NSCov-based" — đọc không-vòng-lặp: trên tập
  candidate, vì S chưa chọn); xếp giảm (tie ws desc → lexicographic id-numeric) → top
  clamp(round(0.1·#cand),10,40) = S. seed=42, deterministic.
- weight /10; backend production sẽ dùng round(ws,3)≥ξ, còn freeze/calibrate dùng Fraction exact.

## Gates (output THẬT — `python3 tests/test_calib_gates.py`, chạy nền)
```
[accident]   G-C1 #FWI=299∈[50,300] & #SFWI=28==clamp(285)=28 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=6<CAP=20 → True
[bms-pos]    G-C1 #FWI=276∈[50,300] & #SFWI=21==clamp(211)=21 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=4<CAP=20 → True
[chainstore] G-C1 #FWI=264∈[50,300] & #SFWI=10==clamp(13)=10 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=2<CAP=20 → True
[chess_fimi] G-C1 #FWI=293∈[50,300] & #SFWI=28==clamp(280)=28 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=6<CAP=20 → True
[kosarak]    G-C1 #FWI=263∈[50,300] & #SFWI=22==clamp(220)=22 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=5<CAP=20 → True
[mushroom]   G-C1 #FWI=299∈[50,300] & #SFWI=28==clamp(282)=28 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=6<CAP=20 → True
[retail]     G-C1 #FWI=241∈[50,300] & #SFWI=14==clamp(141)=14 → True ; G-C2 |X|≥2∧ws>ξ → True ; G-C3 max|X|(fwi)=4<CAP=20 → True
[chess_fimi] G-C3+ re-mine cap=30: #FWI=293 == frozen 293 → True (max|X|=6)
[chess_fimi] G-C4 determinism (2×) & khớp json: True
[mushroom]   G-C3+ re-mine cap=30: #FWI=299 == frozen 299 → True (max|X|=6)
[mushroom]   G-C4 determinism (2×) & khớp json: True
[retail]     G-C3+ re-mine cap=30: #FWI=241 == frozen 241 → True (max|X|=4)
[retail]     G-C4 determinism (2×) & khớp json: True
CALIB gates PASS
```

| Gate | Nội dung | Kết quả |
|---|---|---|
| G-C1 | #FWI∈[50,300]; #SFWI=clamp(round(0.1·#cand),10,40) | PASS ×7 |
| G-C2 | mọi SFWI \|X\|≥2 ∧ ws>ξ (exact Fraction) | PASS ×7 |
| G-C3 | maxlen>7: max\|X\| FWI đã freeze < CAP(20) ⇒ cap KHÔNG cắt (0 FWI dài bị rớt) | PASS ×7 (max\|X\|≤6) |
| G-C3+ | (cross-check nhỏ) re-mine cap=30 → #FWI không đổi | PASS (chess/mushroom/retail) |
| G-C4 | determinism: freeze+select 2× → cùng #FWI + cùng S, khớp json | PASS (chess/mushroom/retail) |

**Cảnh báo maxlen:** KHÔNG có — mọi dataset max\|X\| FWI ≤ 6 < cap 20 (và cross-check cap=30 không thêm
FWI). Không có FWI dài bị rớt.

## Ghi chú
- Mining dataset lớn (accident 340k tx ~21′; bms-pos 515k ~8′; kosarak 990k ~6′; chainstore 1.1M ~32′)
  chạy TUẦN TỰ ở nền, checkpoint mỗi dataset (resume skip nếu json đã có). RT một nguồn (chưa đo §V).
- ξ cũ (utility+qty) KHÔNG tái dùng — đây là ξ mới theo định nghĩa FWI (tw=Σw/|T|, /10).
- Output đóng băng: mọi cell §V (5 cột: HFP/MCP-safe/MCP-nosafe/MSU-MAU/MSU-MIU) dùng CÙNG S/~S/ξ này.

## RESUME_CMD
```
python3 calibration/calibrate.py [<ds> ...]   # calibrate/freeze (skip nếu calib_<ds>.json đã có)
python3 tests/test_calib_gates.py             # exit 0 = CALIB gates PASS (G-C1..C4)
```
