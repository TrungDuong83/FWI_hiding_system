# VIEC_IOT_SWEEP_GRID.md — Feasibility grid sweep IoT (mnc + rtvcq) — mine+đếm

> exp/v5-sectionV · VM hshfwup-run · reuse calibrate (mine_fwi/freeze/select_sfwi) · KHÔNG hiding/RT/5method · 2026-09-07.

**IOT SWEEP GRID: mnc=7/7 rtvcq=7/7 | est_cells=60 (=12 điểm ok≠mult1.0 × 5) | est_hours≈20–30h**

## Gates: G-SW1 (mult=1.0 khớp calib rtvcq 295/26, mnc 297/27) PASS · G-SW2 (n_sfwi=clamp) PASS · G-SW3 (phân loại) PASS · G-SW4 (determinism 2×) PASS.

## GRID 2×7 (nf=#FWI, ns=#SFWI, t=mine_time_s)
| dataset (ξ_op) | 0.4 | 0.6 | 0.8 | **1.0** | 1.2 | 1.4 | 1.6 |
|---|---|---|---|---|---|---|---|
| **rtvcq** (0.057) | OK ξ0.023 nf1114 ns40 t4.67 | OK ξ0.034 nf637 ns40 t3.9 | OK ξ0.046 nf403 ns37 t3.51 | OK ξ0.057 nf295 ns26 t3.21 | OK ξ0.068 nf216 ns19 t2.92 | OK ξ0.08 nf174 ns15 t2.43 | OK ξ0.091 nf138 ns12 t2.04 |
| **mnc** (0.204) | OK ξ0.082 nf5377 ns40 t405.26 | OK ξ0.122 nf1546 ns40 t257.93 | OK ξ0.163 nf636 ns40 t167.6 | OK ξ0.204 nf297 ns27 t110.87 | OK ξ0.245 nf184 ns16 t75.29 | OK ξ0.286 nf89 ns10 t44.99 | OK ξ0.326 nf58 ns10 t35.39 |

**#điểm ok:** rtvcq=7/7, mnc=7/7 (không ceiling/floor). **Sweep (≠mult1.0):** rtvcq=6, mnc=6 → **12 điểm × 5 = 60 cell sweep IoT**.

## Quan sát
- **Không floor/OOM:** mnc mult=0.4 (ξ=0.082, 5377 FWI) mine 405s < 1200s — MNC KHÔNG nổ ở dải mult này (nhờ bỏ Latitude/Downstream + 96 item).
- n_sfwi chạm clamp 40 ở ξ thấp (rtvcq 0.4/0.6/0.8; mnc 0.4/0.6/0.8).
- ξ phân biệt tốt (không collapse như chainstore).

## Ước RT PHA sweep IoT (thô — dựa RT operating IoT; timeout là DATA hợp lệ, KHÔNG lý do bỏ)
- **rtvcq (6 điểm × 5 = 30 cell):** |D|=63k nhẹ. Operating sum ~203s/điểm; ξ thấp (ns=40) nặng hơn ~2–3×. Ước **~1–2h** tổng, nghi KHÔNG timeout.
- **mnc (6 điểm × 5 = 30 cell):** |D|=737k dày/lặp. **NGHI TIMEOUT 2h:**
  - **MSU-MAU mọi điểm mnc** (operating mult=1.0 đã timeout) → ~6×2h.
  - **MCP-safeT mnc ξ thấp** (0.8/0.6/0.4: nf 636/1546/5377, ns=40; operating đã 27min) → nhiều khả năng chạm 2h.
  - HFP/MCP-safeF/MSU-MIU: phút–chục phút. AC re-mine: mnc mine 35–405s/điểm × 5.
  - Ước mnc **~18–25h** (gồm ~8–10 cell timeout).
- **Tổng ước ≈ 20–30h** (bao ~8–10 cell timeout ở mnc, honest). Bounded bởi cap 2h/cell.

## CẦN CONTROL
- Duyệt 12 điểm sweep (rtvcq 6 + mnc 6). Không có floor/ceiling để tỉa. Nếu muốn giảm tải: cân nhắc mnc ξ thấp (nhiều timeout) — nhưng timeout hợp lệ.
- Sau duyệt → handoff chạy sweep IoT (5 method × 12 điểm = 60 cell, cùng VM, 2h/cap, boundary audit, honest timeout) → tích hợp đường cong 9 dataset.

**IOT SWEEP GRID: mnc=7/7 rtvcq=7/7 | est_cells=60 | est_hours≈20–30h**