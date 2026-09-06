# VIEC_SECTIONV.md — §V FULL RUN (MAIN + SWEEP, 5 method) — kết quả cuối

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · GCP c2-standard-16 (16 vCPU / 64GB, Ubuntu 22.04.5) · PYTHONHASHSEED=0 · RT một nguồn (một code, một máy).

**SECTIONV OK: main=35 sweep=140 (tổng 175 cell) | timeouts=8 | boundary_mismatch=0 | total_RT=86788s (24.11h) | total_AC_remine=12055s (3.35h)**

## Cấu hình & phương pháp
- **Membership = `ws ≥ ξ` float64 trực tiếp** (control 2026-09 bỏ `round(·,3)` — vùng bóng làm-tròn gây mismatch sau hiding). Nhất quán hiding↔metric↔exact. Verify: G-MEMB PASS, mọi cell `n_boundary_mismatch=0`.
- **5 method:** HFPriority, MCPriority_safeT (safe), MCPriority_safeF (nosafe), MSU-MAU, MSU-MIU (baseline).
- **Cell:** MAIN = 7 ds × 5 method tại mult=1.0 (ξ operating, S/~S từ calib). SWEEP = điểm feasible=ok trong sweep_grid.json (trừ mult=1.0 và trừ chainstore) × 5 method; S/~S re-derive ở ξ(mult) (calibrate reuse, cache sweep_frozen_*.json).
- **Deadline hiding 2h/cell** (>2h ⇒ status=timeout, RT=cap 7200s, loại khỏi đường cong RT). AC re-mine SAU, không deadline. Ô tuần tự, checkpoint+push mỗi ô.
- Boundary audit (band 1e-6, float-decision vs exact Fraction) chạy mỗi cell — **0/175 mismatch.**

## Sanity gates (PASS)
- Mọi HFPriority HF=0: **True** (35/35). Mọi MCPriority_safeT MC=0: **True** (35/35, kể cả cell timeout — Safe giữ MC=0).
- Mọi n_boundary_mismatch=0: **True** (175/175). Không cell status=error, không NaN. summary.csv=175 dòng khớp JSON.

## TIMEOUT (8 cell — honest, RT=cap 2h, loại khỏi đường cong RT)
Trạng thái tại lúc cap (hiding chưa xong ⇒ HF>0 hợp lệ):

| dataset | mult | ξ | method | HF | MC | n_del | ghi chú |
|---|---|---|---|---|---|---|---|
| kosarak | m1.0 | 0.011 | MSU-MAU | 0.1818 | 0.2656 | 120326 | baseline chậm trên |D| lớn/dense |
| kosarak | m0.8 | 0.009 | MSU-MAU | 0.1212 | 0.3362 | 133448 | baseline chậm trên |D| lớn/dense |
| kosarak | m1.2 | 0.013 | MSU-MAU | 0.375 | 0.1351 | 97215 | baseline chậm trên |D| lớn/dense |
| kosarak | m1.4 | 0.015 | MSU-MAU | 0.3846 | 0.1611 | 88578 | baseline chậm trên |D| lớn/dense |
| accident | m1.0 | 0.751 | MSU-MAU | 0.6786 | 0.1697 | 12990 | baseline chậm trên |D| lớn/dense |
| accident | m0.8 | 0.601 | MCPriority_safeT | 0.875 | 0 | 27189 | safe-check dày (n_sblk=14317999) |
| accident | m0.8 | 0.601 | MSU-MAU | 0.625 | 0.1474 | 13770 | baseline chậm trên |D| lớn/dense |
| accident | m1.2 | 0.901 | MSU-MAU | 0.6 | 0.1905 | 13345 | baseline chậm trên |D| lớn/dense |

> Tất cả timeout là MSU-MAU (7) + accident MCPriority_safeT m0.8 (1), trên dataset lớn/dense (kosarak |D|=990k, accident |D|=340k). n_del bounded (không loop vô hạn) — chỉ chậm hơn 2h. Đúng dự đoán handoff (baseline/dense nghi timeout).

## BẢNG MAIN (35 cell — mult=1.0, ξ operating)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chess_fimi | m1.0 | 0.92 | HFPriority | 0 | 0.5849 | 0 | 0.306 | 0.179 | 3246 |  |  | 0 | 0 | ok |
| chess_fimi | m1.0 | 0.92 | MCPriority_safeT | 0.8214 | 0 | 0 | 5.666 | 0.322 | 215 | 1 | 109286 | 3 | 0 | ok |
| chess_fimi | m1.0 | 0.92 | MCPriority_safeF | 0 | 0.8642 | 0 | 1.865 | 0.117 | 18919 | 0 | 0 | 0 | 0 | ok |
| chess_fimi | m1.0 | 0.92 | MSU-MAU | 0 | 0.5547 | 0 | 0.611 | 0.194 | 251 |  |  | 0 | 0 | ok |
| chess_fimi | m1.0 | 0.92 | MSU-MIU | 0 | 0.5358 | 0 | 0.039 | 0.205 | 211 |  |  | 0 | 0 | ok |
| mushroom | m1.0 | 0.457 | HFPriority | 0 | 0.5166 | 0.007576 | 0.578 | 0.413 | 8142 |  |  | 0 | 0 | ok |
| mushroom | m1.0 | 0.457 | MCPriority_safeT | 1 | 0 | 0 | 28.29 | 0.476 | 3305 | 1 | 1028068 | 14 | 0 | ok |
| mushroom | m1.0 | 0.457 | MCPriority_safeF | 0 | 0.8708 | 0 | 3.481 | 0.128 | 47971 | 0 | 0 | 0 | 0 | ok |
| mushroom | m1.0 | 0.457 | MSU-MAU | 0.03571 | 0.4908 | 0 | 16.58 | 0.419 | 3815 |  |  | 0 | 0 | ok |
| mushroom | m1.0 | 0.457 | MSU-MIU | 0 | 0.524 | 0.03008 | 0.289 | 0.361 | 4019 |  |  | 0 | 0 | ok |
| retail | m1.0 | 0.008 | HFPriority | 0 | 0.1894 | 0 | 0.519 | 7.025 | 14961 |  |  | 1 | 0 | ok |
| retail | m1.0 | 0.008 | MCPriority_safeT | 0.07143 | 0 | 0 | 3.582 | 6.835 | 20039 | 1 | 34158 | 13 | 0 | ok |
| retail | m1.0 | 0.008 | MCPriority_safeF | 0 | 0.1145 | 0 | 1.547 | 6.556 | 24987 | 0 | 0 | 0 | 0 | ok |
| retail | m1.0 | 0.008 | MSU-MAU | 0.07143 | 0.185 | 0 | 58.82 | 7.106 | 15550 |  |  | 1 | 0 | ok |
| retail | m1.0 | 0.008 | MSU-MIU | 0 | 0.185 | 0.005376 | 0.362 | 6.726 | 12957 |  |  | 0 | 0 | ok |
| bms-pos | m1.0 | 0.021 | HFPriority | 0 | 0.2824 | 0 | 3.189 | 75.03 | 75068 |  |  | 1 | 0 | ok |
| bms-pos | m1.0 | 0.021 | MCPriority_safeT | 0.4762 | 0 | 0 | 67.44 | 74.48 | 80060 | 1 | 1407298 | 48 | 0 | ok |
| bms-pos | m1.0 | 0.021 | MCPriority_safeF | 0 | 0.3922 | 0 | 10.25 | 63.1 | 218579 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m1.0 | 0.021 | MSU-MAU | 0.1429 | 0.2745 | 0 | 1865 | 73.76 | 57270 |  |  | 2 | 0 | ok |
| bms-pos | m1.0 | 0.021 | MSU-MIU | 0.04762 | 0.2784 | 0 | 3.237 | 69.89 | 96238 |  |  | 2 | 0 | ok |
| kosarak | m1.0 | 0.011 | HFPriority | 0 | 0.361 | 0 | 7.107 | 44.33 | 171432 |  |  | 1 | 0 | ok |
| kosarak | m1.0 | 0.011 | MCPriority_safeT | 0.3182 | 0 | 0 | 121.9 | 42.91 | 226448 | 1 | 1997422 | 41 | 0 | ok |
| kosarak | m1.0 | 0.011 | MCPriority_safeF | 0 | 0.4274 | 0 | 19.94 | 33.34 | 399854 | 0 | 0 | 1 | 0 | ok |
| kosarak | m1.0 | 0.011 | MSU-MAU | 0.1818 | 0.2656 | 0 | 7200 | 43.4 | 120326 |  |  | 0 | 0 | timeout |
| kosarak | m1.0 | 0.011 | MSU-MIU | 0 | 0.2531 | 0 | 4.981 | 42.91 | 153154 |  |  | 1 | 0 | ok |
| accident | m1.0 | 0.751 | HFPriority | 0 | 0.6162 | 0 | 39.52 | 53.46 | 360753 |  |  | 0 | 0 | ok |
| accident | m1.0 | 0.751 | MCPriority_safeT | 0.7857 | 0 | 0 | 1655 | 109.3 | 68731 | 1 | 26356925 | 10 | 0 | ok |
| accident | m1.0 | 0.751 | MCPriority_safeF | 0 | 0.8598 | 0 | 228.6 | 16.68 | 2034590 | 0 | 0 | 0 | 0 | ok |
| accident | m1.0 | 0.751 | MSU-MAU | 0.6786 | 0.1697 | 0 | 7200 | 98.72 | 12990 |  |  | 0 | 0 | timeout |
| accident | m1.0 | 0.751 | MSU-MIU | 0 | 0.5387 | 0 | 8.104 | 59.88 | 71166 |  |  | 1 | 0 | ok |
| chainstore | m1.0 | 0.003 | HFPriority | 0 | 0 | 0 | 1.419 | 272.5 | 21409 |  |  | 1 | 0 | ok |
| chainstore | m1.0 | 0.003 | MCPriority_safeT | 0 | 0 | 0 | 2.855 | 270.9 | 22301 | 0 | 0 | 1 | 0 | ok |
| chainstore | m1.0 | 0.003 | MCPriority_safeF | 0 | 0 | 0 | 1.508 | 269.2 | 22301 | 0 | 0 | 1 | 0 | ok |
| chainstore | m1.0 | 0.003 | MSU-MAU | 0.1 | 0 | 0 | 55.73 | 273.4 | 8952 |  |  | 4 | 0 | ok |
| chainstore | m1.0 | 0.003 | MSU-MIU | 0.3 | 0 | 0 | 0.354 | 276 | 10185 |  |  | 5 | 0 | ok |

## BẢNG SWEEP (140 cell — điểm feasible=ok, ξ theo mult; chainstore loại)

### chess_fimi (10 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chess_fimi | m0.6 | 0.552 | HFPriority | 0 | 0.331 | 0.002178 | 88.59 | 166.5 | 378 |  |  | 6 | 0 | ok |
| chess_fimi | m0.6 | 0.552 | MCPriority_safeT | 1 | 0 | 0 | 191.4 | 191.5 | 0 | 1 | 48262 | 0 | 0 | ok |
| chess_fimi | m0.6 | 0.552 | MCPriority_safeF | 0 | 0.7651 | 0.003034 | 1710 | 47.09 | 7915 | 0 | 0 | 0 | 0 | ok |
| chess_fimi | m0.6 | 0.552 | MSU-MAU | 0 | 0.322 | 0.001823 | 88.37 | 156.4 | 394 |  |  | 3 | 0 | ok |
| chess_fimi | m0.6 | 0.552 | MSU-MIU | 0 | 0.2743 | 0.001722 | 61.57 | 160.3 | 254 |  |  | 11 | 0 | ok |
| chess_fimi | m0.8 | 0.736 | HFPriority | 0 | 0.3345 | 0.001205 | 3.299 | 12.25 | 238 |  |  | 0 | 0 | ok |
| chess_fimi | m0.8 | 0.736 | MCPriority_safeT | 1 | 0 | 0.00016 | 95.78 | 16.25 | 9 | 1 | 78352 | 0 | 0 | ok |
| chess_fimi | m0.8 | 0.736 | MCPriority_safeF | 0 | 0.7906 | 0 | 90.51 | 3.584 | 8087 | 0 | 0 | 0 | 0 | ok |
| chess_fimi | m0.8 | 0.736 | MSU-MAU | 0 | 0.3853 | 0.00163 | 5.063 | 11.38 | 311 |  |  | 2 | 0 | ok |
| chess_fimi | m0.8 | 0.736 | MSU-MIU | 0 | 0.3283 | 0.000895 | 2.976 | 10.94 | 221 |  |  | 0 | 0 | ok |

### mushroom (30 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mushroom | m0.4 | 0.183 | HFPriority | 0 | 0.5153 | 0.009968 | 60.31 | 3.648 | 3734 |  |  | 0 | 0 | ok |
| mushroom | m0.4 | 0.183 | MCPriority_safeT | 1 | 0 | 0 | 60.26 | 6.416 | 320 | 1 | 98978 | 14 | 0 | ok |
| mushroom | m0.4 | 0.183 | MCPriority_safeF | 0 | 0.4747 | 0.001259 | 60.7 | 4.134 | 3814 | 0 | 0 | 0 | 0 | ok |
| mushroom | m0.4 | 0.183 | MSU-MAU | 0 | 0.4104 | 0.001358 | 20.88 | 5.013 | 1057 |  |  | 0 | 0 | ok |
| mushroom | m0.4 | 0.183 | MSU-MIU | 0 | 0.301 | 0.000249 | 10.88 | 6.103 | 696 |  |  | 0 | 0 | ok |
| mushroom | m0.6 | 0.274 | HFPriority | 0 | 0.419 | 0.006672 | 3.762 | 2.278 | 3611 |  |  | 0 | 0 | ok |
| mushroom | m0.6 | 0.274 | MCPriority_safeT | 1 | 0 | 0 | 41.45 | 2.22 | 622 | 1 | 128697 | 16 | 0 | ok |
| mushroom | m0.6 | 0.274 | MCPriority_safeF | 0 | 0.4279 | 0.006775 | 6.162 | 1.61 | 6035 | 0 | 0 | 0 | 0 | ok |
| mushroom | m0.6 | 0.274 | MSU-MAU | 0 | 0.3113 | 0 | 2.786 | 2.062 | 614 |  |  | 0 | 0 | ok |
| mushroom | m0.6 | 0.274 | MSU-MIU | 0 | 0.2783 | 0.001799 | 0.686 | 2.246 | 583 |  |  | 0 | 0 | ok |
| mushroom | m0.8 | 0.366 | HFPriority | 0 | 0.5703 | 0.00655 | 1.556 | 0.948 | 8110 |  |  | 0 | 0 | ok |
| mushroom | m0.8 | 0.366 | MCPriority_safeT | 1 | 0 | 0 | 55.3 | 0.972 | 4680 | 1 | 737181 | 20 | 0 | ok |
| mushroom | m0.8 | 0.366 | MCPriority_safeF | 0 | 0.8763 | 0 | 8.779 | 0.225 | 47769 | 0 | 0 | 0 | 0 | ok |
| mushroom | m0.8 | 0.366 | MSU-MAU | 0 | 0.5449 | 0 | 13.46 | 0.935 | 3463 |  |  | 0 | 0 | ok |
| mushroom | m0.8 | 0.366 | MSU-MIU | 0 | 0.5137 | 0.003868 | 0.792 | 0.751 | 3948 |  |  | 0 | 0 | ok |
| mushroom | m1.2 | 0.548 | HFPriority | 0 | 0.3596 | 0 | 0.118 | 0.233 | 2740 |  |  | 0 | 0 | ok |
| mushroom | m1.2 | 0.548 | MCPriority_safeT | 1 | 0 | 0 | 6.388 | 0.254 | 3849 | 1 | 474504 | 12 | 0 | ok |
| mushroom | m1.2 | 0.548 | MCPriority_safeF | 0 | 0.7416 | 0 | 0.956 | 0.135 | 22821 | 0 | 0 | 0 | 0 | ok |
| mushroom | m1.2 | 0.548 | MSU-MAU | 0 | 0.3596 | 0 | 13.77 | 0.233 | 2739 |  |  | 0 | 0 | ok |
| mushroom | m1.2 | 0.548 | MSU-MIU | 0 | 0.5843 | 0.05128 | 0.139 | 0.303 | 4286 |  |  | 0 | 0 | ok |
| mushroom | m1.4 | 0.64 | HFPriority | 0 | 0.4839 | 0 | 0.222 | 0.221 | 9134 |  |  | 0 | 0 | ok |
| mushroom | m1.4 | 0.64 | MCPriority_safeT | 0.3 | 0 | 0 | 2.303 | 0.189 | 4407 | 1 | 223377 | 1 | 0 | ok |
| mushroom | m1.4 | 0.64 | MCPriority_safeF | 0 | 0.7742 | 0 | 0.597 | 0.192 | 22949 | 0 | 0 | 0 | 0 | ok |
| mushroom | m1.4 | 0.64 | MSU-MAU | 0.1 | 0.4839 | 0 | 22.71 | 0.166 | 4533 |  |  | 0 | 0 | ok |
| mushroom | m1.4 | 0.64 | MSU-MIU | 0 | 0.4516 | 0 | 0.122 | 0.241 | 4399 |  |  | 0 | 0 | ok |
| mushroom | m1.6 | 0.731 | HFPriority | 0 | 0.5238 | 0 | 0.21 | 0.199 | 9491 |  |  | 0 | 0 | ok |
| mushroom | m1.6 | 0.731 | MCPriority_safeT | 0 | 0 | 0 | 0.4 | 0.153 | 3625 | 0 | 29995 | 0 | 0 | ok |
| mushroom | m1.6 | 0.731 | MCPriority_safeF | 0 | 0.5238 | 0 | 0.277 | 0.129 | 9833 | 0 | 0 | 0 | 0 | ok |
| mushroom | m1.6 | 0.731 | MSU-MAU | 0.1 | 0.381 | 0 | 16.58 | 0.142 | 3099 |  |  | 0 | 0 | ok |
| mushroom | m1.6 | 0.731 | MSU-MIU | 0 | 0.4762 | 0 | 0.093 | 0.135 | 3008 |  |  | 0 | 0 | ok |

### retail (30 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| retail | m0.4 | 0.003 | HFPriority | 0 | 0.229 | 0.002941 | 1.512 | 107.8 | 14603 |  |  | 0 | 0 | ok |
| retail | m0.4 | 0.003 | MCPriority_safeT | 0.275 | 0 | 0.001502 | 43.04 | 106 | 17779 | 1 | 129174 | 61 | 0 | ok |
| retail | m0.4 | 0.003 | MCPriority_safeF | 0 | 0.1585 | 0.001799 | 3.291 | 100.4 | 30512 | 0 | 0 | 2 | 0 | ok |
| retail | m0.4 | 0.003 | MSU-MAU | 0.025 | 0.2373 | 0.00297 | 55.22 | 108.1 | 17088 |  |  | 0 | 0 | ok |
| retail | m0.4 | 0.003 | MSU-MIU | 0 | 0.2108 | 0.005731 | 1.332 | 105.3 | 14235 |  |  | 1 | 0 | ok |
| retail | m0.6 | 0.005 | HFPriority | 0 | 0.2406 | 0 | 1.012 | 27.47 | 18438 |  |  | 0 | 0 | ok |
| retail | m0.6 | 0.005 | MCPriority_safeT | 0.2571 | 0 | 0 | 17.68 | 25.52 | 24744 | 1 | 121523 | 37 | 0 | ok |
| retail | m0.6 | 0.005 | MCPriority_safeF | 0 | 0.1955 | 0 | 2.209 | 23.65 | 36813 | 0 | 0 | 0 | 0 | ok |
| retail | m0.6 | 0.005 | MSU-MAU | 0.02857 | 0.2387 | 0 | 60.83 | 27.61 | 18013 |  |  | 1 | 0 | ok |
| retail | m0.6 | 0.005 | MSU-MIU | 0 | 0.1842 | 0.002299 | 0.685 | 27.3 | 14602 |  |  | 1 | 0 | ok |
| retail | m0.8 | 0.006 | HFPriority | 0 | 0.2277 | 0.003378 | 0.82 | 16.25 | 17795 |  |  | 0 | 0 | ok |
| retail | m0.8 | 0.006 | MCPriority_safeT | 0.25 | 0 | 0.002571 | 9.578 | 14.52 | 23870 | 1 | 77327 | 22 | 0 | ok |
| retail | m0.8 | 0.006 | MCPriority_safeF | 0 | 0.2016 | 0.003268 | 1.688 | 13.88 | 33494 | 0 | 0 | 0 | 0 | ok |
| retail | m0.8 | 0.006 | MSU-MAU | 0.04167 | 0.2435 | 0.006849 | 61.13 | 16.51 | 17207 |  |  | 0 | 0 | ok |
| retail | m0.8 | 0.006 | MSU-MIU | 0 | 0.1832 | 0.009524 | 0.538 | 16.14 | 13993 |  |  | 0 | 0 | ok |
| retail | m1.2 | 0.01 | HFPriority | 0 | 0.1597 | 0 | 0.394 | 4.047 | 12911 |  |  | 0 | 0 | ok |
| retail | m1.2 | 0.01 | MCPriority_safeT | 0.1 | 0 | 0 | 2.838 | 3.517 | 16050 | 1 | 48344 | 8 | 0 | ok |
| retail | m1.2 | 0.01 | MCPriority_safeF | 0 | 0.125 | 0 | 0.71 | 3.333 | 21235 | 0 | 0 | 0 | 0 | ok |
| retail | m1.2 | 0.01 | MSU-MAU | 0.1 | 0.1875 | 0 | 58.2 | 3.757 | 14106 |  |  | 0 | 0 | ok |
| retail | m1.2 | 0.01 | MSU-MIU | 0 | 0.1806 | 0 | 0.266 | 3.683 | 11857 |  |  | 0 | 0 | ok |
| retail | m1.4 | 0.011 | HFPriority | 0 | 0.1705 | 0 | 0.379 | 3.268 | 12755 |  |  | 1 | 0 | ok |
| retail | m1.4 | 0.011 | MCPriority_safeT | 0.1 | 0 | 0 | 2.455 | 3.111 | 15206 | 1 | 44487 | 6 | 0 | ok |
| retail | m1.4 | 0.011 | MCPriority_safeF | 0 | 0.1628 | 0.009174 | 0.687 | 2.917 | 21144 | 0 | 0 | 0 | 0 | ok |
| retail | m1.4 | 0.011 | MSU-MAU | 0.1 | 0.1938 | 0 | 58.69 | 3.147 | 13832 |  |  | 0 | 0 | ok |
| retail | m1.4 | 0.011 | MSU-MIU | 0 | 0.1705 | 0 | 0.49 | 2.771 | 11611 |  |  | 0 | 0 | ok |
| retail | m1.6 | 0.013 | HFPriority | 0 | 0.2083 | 0 | 0.632 | 2.032 | 14127 |  |  | 0 | 0 | ok |
| retail | m1.6 | 0.013 | MCPriority_safeT | 0.2 | 0 | 0 | 2.377 | 1.97 | 17163 | 1 | 46745 | 9 | 0 | ok |
| retail | m1.6 | 0.013 | MCPriority_safeF | 0 | 0.1979 | 0 | 0.668 | 2.123 | 21919 | 0 | 0 | 0 | 0 | ok |
| retail | m1.6 | 0.013 | MSU-MAU | 0.1 | 0.2083 | 0 | 58.54 | 2.28 | 13505 |  |  | 0 | 0 | ok |
| retail | m1.6 | 0.013 | MSU-MIU | 0 | 0.1771 | 0.0125 | 0.469 | 2.042 | 11180 |  |  | 0 | 0 | ok |

### bms-pos (30 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bms-pos | m0.4 | 0.008 | HFPriority | 0 | 0.2864 | 0 | 5.728 | 303 | 36362 |  |  | 1 | 0 | ok |
| bms-pos | m0.4 | 0.008 | MCPriority_safeT | 0.8 | 0 | 0 | 553.1 | 306.2 | 27184 | 1 | 2441592 | 115 | 0 | ok |
| bms-pos | m0.4 | 0.008 | MCPriority_safeF | 0 | 0.4656 | 0 | 22.11 | 270.2 | 140705 | 0 | 0 | 2 | 0 | ok |
| bms-pos | m0.4 | 0.008 | MSU-MAU | 0.075 | 0.2916 | 0 | 627.6 | 296 | 35060 |  |  | 2 | 0 | ok |
| bms-pos | m0.4 | 0.008 | MSU-MIU | 0.05 | 0.2736 | 0.007011 | 5.984 | 290.9 | 42054 |  |  | 2 | 0 | ok |
| bms-pos | m0.6 | 0.013 | HFPriority | 0 | 0.3166 | 0 | 4.779 | 152 | 64587 |  |  | 1 | 0 | ok |
| bms-pos | m0.6 | 0.013 | MCPriority_safeT | 0.35 | 0 | 0 | 206.1 | 146.5 | 71937 | 1 | 2097734 | 82 | 0 | ok |
| bms-pos | m0.6 | 0.013 | MCPriority_safeF | 0 | 0.4958 | 0.006601 | 21.03 | 120.4 | 269934 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m0.6 | 0.013 | MSU-MAU | 0 | 0.2864 | 0 | 1643 | 150 | 63016 |  |  | 0 | 0 | ok |
| bms-pos | m0.6 | 0.013 | MSU-MIU | 0 | 0.2312 | 0.004338 | 4.908 | 145.9 | 76325 |  |  | 2 | 0 | ok |
| bms-pos | m0.8 | 0.017 | HFPriority | 0 | 0.3079 | 0 | 4.437 | 109.6 | 80650 |  |  | 0 | 0 | ok |
| bms-pos | m0.8 | 0.017 | MCPriority_safeT | 0.5152 | 0 | 0 | 131.7 | 104.8 | 86977 | 1 | 1939894 | 62 | 0 | ok |
| bms-pos | m0.8 | 0.017 | MCPriority_safeF | 0 | 0.4526 | 0.009524 | 16.25 | 87.98 | 277268 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m0.8 | 0.017 | MSU-MAU | 0.1818 | 0.2895 | 0 | 1864 | 107.2 | 63114 |  |  | 2 | 0 | ok |
| bms-pos | m0.8 | 0.017 | MSU-MIU | 0.06061 | 0.3105 | 0.01124 | 5.152 | 104.1 | 115587 |  |  | 1 | 0 | ok |
| bms-pos | m1.2 | 0.025 | HFPriority | 0 | 0.2202 | 0 | 2.488 | 53.95 | 63518 |  |  | 1 | 0 | ok |
| bms-pos | m1.2 | 0.025 | MCPriority_safeT | 0.4615 | 0 | 0 | 68.45 | 51.78 | 75151 | 1 | 1882802 | 25 | 0 | ok |
| bms-pos | m1.2 | 0.025 | MCPriority_safeF | 0 | 0.3036 | 0 | 7.081 | 45.72 | 175106 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m1.2 | 0.025 | MSU-MAU | 0.1538 | 0.1786 | 0 | 1687 | 52.48 | 46639 |  |  | 0 | 0 | ok |
| bms-pos | m1.2 | 0.025 | MSU-MIU | 0 | 0.1726 | 0 | 2.246 | 50.95 | 72656 |  |  | 2 | 0 | ok |
| bms-pos | m1.4 | 0.029 | HFPriority | 0 | 0.2015 | 0 | 2.058 | 42.74 | 54672 |  |  | 0 | 0 | ok |
| bms-pos | m1.4 | 0.029 | MCPriority_safeT | 0.3 | 0 | 0 | 32.24 | 42.36 | 60737 | 1 | 984006 | 24 | 0 | ok |
| bms-pos | m1.4 | 0.029 | MCPriority_safeF | 0 | 0.2836 | 0 | 5.765 | 37.51 | 153600 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m1.4 | 0.029 | MSU-MAU | 0.2 | 0.1493 | 0 | 1472 | 43.8 | 37901 |  |  | 1 | 0 | ok |
| bms-pos | m1.4 | 0.029 | MSU-MIU | 0.1 | 0.1343 | 0 | 1.591 | 42.86 | 53510 |  |  | 1 | 0 | ok |
| bms-pos | m1.6 | 0.034 | HFPriority | 0 | 0.1304 | 0 | 1.848 | 33.07 | 52412 |  |  | 0 | 0 | ok |
| bms-pos | m1.6 | 0.034 | MCPriority_safeT | 0 | 0 | 0 | 8.562 | 31.65 | 67375 | 0 | 218668 | 7 | 0 | ok |
| bms-pos | m1.6 | 0.034 | MCPriority_safeF | 0 | 0.1848 | 0 | 4.093 | 29.56 | 119632 | 0 | 0 | 1 | 0 | ok |
| bms-pos | m1.6 | 0.034 | MSU-MAU | 0.1 | 0.07609 | 0 | 1574 | 33.23 | 41145 |  |  | 1 | 0 | ok |
| bms-pos | m1.6 | 0.034 | MSU-MIU | 0.2 | 0.08696 | 0 | 1.089 | 32.91 | 46561 |  |  | 1 | 0 | ok |

### kosarak (30 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kosarak | m0.4 | 0.004 | HFPriority | 0 | 0.3616 | 0 | 10.51 | 324.1 | 50846 |  |  | 1 | 0 | ok |
| kosarak | m0.4 | 0.004 | MCPriority_safeT | 0.675 | 0 | 0 | 592.1 | 328.4 | 46329 | 1 | 1604388 | 126 | 0 | ok |
| kosarak | m0.4 | 0.004 | MCPriority_safeF | 0 | 0.3794 | 0 | 34.39 | 287.4 | 155128 | 0 | 0 | 2 | 0 | ok |
| kosarak | m0.4 | 0.004 | MSU-MAU | 0.125 | 0.3093 | 0 | 1281 | 314.3 | 58136 |  |  | 3 | 0 | ok |
| kosarak | m0.4 | 0.004 | MSU-MIU | 0 | 0.2834 | 0.007736 | 6.422 | 320.5 | 34793 |  |  | 2 | 0 | ok |
| kosarak | m0.6 | 0.007 | HFPriority | 0 | 0.3573 | 0 | 9.063 | 97.07 | 115061 |  |  | 1 | 0 | ok |
| kosarak | m0.6 | 0.007 | MCPriority_safeT | 0.55 | 0 | 0.001645 | 299.1 | 97.11 | 119621 | 1 | 2555670 | 81 | 0 | ok |
| kosarak | m0.6 | 0.007 | MCPriority_safeF | 0 | 0.4889 | 0 | 26.22 | 71.54 | 294969 | 0 | 0 | 1 | 0 | ok |
| kosarak | m0.6 | 0.007 | MSU-MAU | 0.1 | 0.3983 | 0 | 4866 | 95 | 131413 |  |  | 2 | 0 | ok |
| kosarak | m0.6 | 0.007 | MSU-MIU | 0 | 0.2701 | 0.02511 | 5.592 | 96.42 | 83655 |  |  | 1 | 0 | ok |
| kosarak | m0.8 | 0.009 | HFPriority | 0 | 0.3563 | 0 | 9.079 | 60.91 | 176820 |  |  | 1 | 0 | ok |
| kosarak | m0.8 | 0.009 | MCPriority_safeT | 0.4848 | 0 | 0.008174 | 171.6 | 59.57 | 224795 | 1 | 2069547 | 58 | 0 | ok |
| kosarak | m0.8 | 0.009 | MCPriority_safeF | 0 | 0.4828 | 0.005525 | 25.59 | 45.69 | 434005 | 0 | 0 | 1 | 0 | ok |
| kosarak | m0.8 | 0.009 | MSU-MAU | 0.1212 | 0.3362 | 0 | 7200 | 60.45 | 133448 |  |  | 0 | 0 | timeout |
| kosarak | m0.8 | 0.009 | MSU-MIU | 0 | 0.2931 | 0.004049 | 6.401 | 58.33 | 159300 |  |  | 1 | 0 | ok |
| kosarak | m1.2 | 0.013 | HFPriority | 0 | 0.3351 | 0 | 7.02 | 39.57 | 193047 |  |  | 1 | 0 | ok |
| kosarak | m1.2 | 0.013 | MCPriority_safeT | 0.3125 | 0 | 0 | 89.79 | 38.68 | 252662 | 1 | 1729461 | 37 | 0 | ok |
| kosarak | m1.2 | 0.013 | MCPriority_safeF | 0 | 0.3784 | 0 | 16.46 | 33.54 | 391655 | 0 | 0 | 1 | 0 | ok |
| kosarak | m1.2 | 0.013 | MSU-MAU | 0.375 | 0.1351 | 0 | 7200 | 40.24 | 97215 |  |  | 0 | 0 | timeout |
| kosarak | m1.2 | 0.013 | MSU-MIU | 0 | 0.2865 | 0.007519 | 5.052 | 36.76 | 175246 |  |  | 1 | 0 | ok |
| kosarak | m1.4 | 0.015 | HFPriority | 0 | 0.3154 | 0 | 5.626 | 32.46 | 160958 |  |  | 1 | 0 | ok |
| kosarak | m1.4 | 0.015 | MCPriority_safeT | 0.1538 | 0 | 0 | 57.97 | 34.95 | 202866 | 1 | 1243047 | 21 | 0 | ok |
| kosarak | m1.4 | 0.015 | MCPriority_safeF | 0 | 0.3691 | 0 | 12.71 | 28.14 | 313513 | 0 | 0 | 1 | 0 | ok |
| kosarak | m1.4 | 0.015 | MSU-MAU | 0.3846 | 0.1611 | 0 | 7200 | 35.84 | 88578 |  |  | 0 | 0 | timeout |
| kosarak | m1.4 | 0.015 | MSU-MIU | 0 | 0.2282 | 0 | 3.768 | 32.77 | 139909 |  |  | 1 | 0 | ok |
| kosarak | m1.6 | 0.018 | HFPriority | 0 | 0.2 | 0 | 3 | 26.24 | 68589 |  |  | 1 | 0 | ok |
| kosarak | m1.6 | 0.018 | MCPriority_safeT | 0.1 | 0 | 0 | 31.3 | 28.4 | 76696 | 1 | 847878 | 13 | 0 | ok |
| kosarak | m1.6 | 0.018 | MCPriority_safeF | 0 | 0.2435 | 0 | 6.159 | 26.54 | 123352 | 0 | 0 | 1 | 0 | ok |
| kosarak | m1.6 | 0.018 | MSU-MAU | 0.2 | 0.1391 | 0 | 3229 | 28.35 | 57142 |  |  | 1 | 0 | ok |
| kosarak | m1.6 | 0.018 | MSU-MIU | 0 | 0.1043 | 0 | 1.478 | 29.03 | 40023 |  |  | 2 | 0 | ok |

### accident (10 cell)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| accident | m0.8 | 0.601 | HFPriority | 0 | 0.4117 | 0.002435 | 46.14 | 367.9 | 63549 |  |  | 0 | 0 | ok |
| accident | m0.8 | 0.601 | MCPriority_safeT | 0.875 | 0 | 0 | 7200 | 589.6 | 27189 |  | 14317999 | 19 | 0 | timeout |
| accident | m0.8 | 0.601 | MCPriority_safeF | 0 | 0.8478 | 0.003135 | 837.6 | 97.38 | 1787884 | 0 | 0 | 0 | 0 | ok |
| accident | m0.8 | 0.601 | MSU-MAU | 0.625 | 0.1474 | 0 | 7200 | 522.2 | 13770 |  |  | 0 | 0 | timeout |
| accident | m0.8 | 0.601 | MSU-MIU | 0 | 0.3901 | 0.00313 | 29.09 | 396.3 | 49743 |  |  | 0 | 0 | ok |
| accident | m1.2 | 0.901 | HFPriority | 0 | 0.5238 | 0 | 13.18 | 8.849 | 362304 |  |  | 0 | 0 | ok |
| accident | m1.2 | 0.901 | MCPriority_safeT | 0 | 0 | 0 | 25.18 | 13.86 | 54203 | 0 | 2591397 | 6 | 0 | ok |
| accident | m1.2 | 0.901 | MCPriority_safeF | 0 | 0.5238 | 0 | 13.75 | 8.775 | 365115 | 0 | 0 | 0 | 0 | ok |
| accident | m1.2 | 0.901 | MSU-MAU | 0.6 | 0.1905 | 0 | 7200 | 13.16 | 13345 |  |  | 0 | 0 | timeout |
| accident | m1.2 | 0.901 | MSU-MIU | 0 | 0.4286 | 0 | 7.313 | 10.41 | 51151 |  |  | 0 | 0 | ok |

## Ghi chú kết quả (không framing — control làm B6)
- Baseline MSU-MAU/MIU có HF>0 ở nhiều cell (re-exposure do W_total coupling / Bẫy #1 khi ẩn tuần tự) — hợp lệ, ghi nguyên. MCP-safe có HF>0 (dừng no-op giữ MC=0) — hợp lệ.
- total_RT bao gồm 8 cell cap 2h (loại khỏi đường cong RT khi vẽ). RT một nguồn: toàn bộ 175 cell chạy bằng code cuối trên cùng VM.

## RESUME_CMD
```bash
cd ~/FWI_hiding_system && source .venv/bin/activate
python3 coordinator/run_coordinator.py        # resume idempotent (mọi cell đã có → COORD DONE)
python3 -c "import csv;rows=list(csv.DictReader(open('results/summary.csv')));print(len(rows),'rows')"
```

Artefact mang về control: `results/summary.csv` (175 dòng) + `results/result_*.json` + file này + `VIEC_SMOKE_1B_v2.md` + `calibration/sweep_grid.json`.

**SECTIONV OK: main=35 sweep=140 | timeouts=8 | boundary_mismatch=0 | total_RT=86788s**