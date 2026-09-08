# VIEC_IOT_SWEEP.md — Sweep IoT (mnc + rtvcq, 60 cell) — chặng cuối §V

> exp/v5-sectionV · VM hshfwup-run (RT một nguồn, cùng máy 7 dataset + IoT-main) · code cuối (ws≥ξ float, không round3) · PYTHONHASHSEED=0 · 2026-09-08.

**IOT SWEEP OK: 60/60 | timeouts=6 | boundary_mismatch=0 | total_RT_sweep=64627s (17.95h)**

## Gates (PASS)
- Mọi HFPriority HF=0 ✓ (12/12); mọi MCPriority_safeT MC=0 ✓ (12/12, kể cả cell timeout); mọi n_boundary_mismatch=0 ✓ (60/60).
- source=hshfwup-run ✓ (RT cùng máy). Không cell error/NaN. summary.csv=245 dòng (185 + 60).

## TIMEOUT (6 cell — honest, RT=cap 2h, loại khỏi đường cong RT)
| dataset | mult | ξ | method | HF | MC | n_del | ghi chú |
|---|---|---|---|---|---|---|---|
| mnc | m0.6 | 0.122 | MSU-MAU | 0.3 | 0.1341 | 35067 | baseline chậm trên MNC dày/lặp |
| mnc | m0.8 | 0.163 | MCPriority_safeT | 0.4 | 0 | 477362 | safe-check dày (n_sblk=78963724) |
| mnc | m0.8 | 0.163 | MSU-MAU | 0.975 | 0.02013 | 23564 | baseline chậm trên MNC dày/lặp |
| mnc | m1.2 | 0.245 | MSU-MAU | 1 | 0.02976 | 14141 | baseline chậm trên MNC dày/lặp |
| mnc | m1.4 | 0.286 | MSU-MAU | 0.8 | 0.02532 | 15494 | baseline chậm trên MNC dày/lặp |
| mnc | m1.6 | 0.326 | MSU-MAU | 0.9 | 0.04167 | 10668 | baseline chậm trên MNC dày/lặp |

> Tất cả timeout ở **mnc** (|D|=737k, 72% dòng trùng): MSU-MAU (m0.6/0.8/1.2/1.4/1.6) + MCP-safeT (m0.8). rtvcq (|D|=63k): KHÔNG timeout. Đúng dự báo grid — bằng chứng baseline không scale + giá bảo đảm MC=0 trên dữ liệu dày.

## BẢNG 60 CELL (số đo THẬT)
| dataset | mult | ξ | method | HF | MC | AC | RT_s | ACrem_s | n_del | noop | sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mnc | 0.4 | 0.082 | HFPriority | 0 | 0.252 | 0.02539 | 107.1 | 365.9 | 120345 |  |  | 0 | 0 | ok |
| mnc | 0.4 | 0.082 | MCPriority_safeT | 1 | 0 | 0 | 2637 | 394.2 | 64494 | 1 | 4360877 | 292 | 0 | ok |
| mnc | 0.4 | 0.082 | MCPriority_safeF | 0 | 0.3348 | 0.003649 | 223.5 | 347.5 | 301257 | 0 | 0 | 8 | 0 | ok |
| mnc | 0.4 | 0.082 | MSU-MAU | 0 | 0.1842 | 0.006163 | 6960 | 390.7 | 38160 |  |  | 24 | 0 | ok |
| mnc | 0.4 | 0.082 | MSU-MIU | 0 | 0.1709 | 0.005171 | 43.23 | 421.7 | 55419 |  |  | 0 | 0 | ok |
| mnc | 0.6 | 0.122 | HFPriority | 0 | 0.3878 | 0.02537 | 77.39 | 182.4 | 373949 |  |  | 0 | 0 | ok |
| mnc | 0.6 | 0.122 | MCPriority_safeT | 0.9 | 0 | 0 | 5555 | 266 | 174348 | 1 | 28589745 | 73 | 0 | ok |
| mnc | 0.6 | 0.122 | MCPriority_safeF | 0 | 0.6826 | 0 | 271.6 | 127.1 | 1392014 | 0 | 0 | 2 | 0 | ok |
| mnc | 0.6 | 0.122 | MSU-MAU | 0.3 | 0.1341 | 0.002274 | 7200 | 235.9 | 35067 |  |  | 0 | 0 | timeout |
| mnc | 0.6 | 0.122 | MSU-MIU | 0 | 0.3606 | 0.04842 | 43 | 213.1 | 208332 |  |  | 1 | 0 | ok |
| mnc | 0.8 | 0.163 | HFPriority | 0 | 0.4446 | 0.006006 | 50.44 | 116.7 | 499294 |  |  | 1 | 0 | ok |
| mnc | 0.8 | 0.163 | MCPriority_safeT | 0.4 | 0 | 0 | 7200 | 161.5 | 477362 |  | 78963724 | 46 | 0 | timeout |
| mnc | 0.8 | 0.163 | MCPriority_safeF | 0 | 0.8104 | 0 | 304.7 | 43.69 | 3123415 | 0 | 0 | 1 | 0 | ok |
| mnc | 0.8 | 0.163 | MSU-MAU | 0.975 | 0.02013 | 0 | 7200 | 164.9 | 23564 |  |  | 0 | 0 | timeout |
| mnc | 0.8 | 0.163 | MSU-MIU | 0 | 0.4966 | 0.006623 | 52.03 | 114 | 584366 |  |  | 1 | 0 | ok |
| mnc | 1.2 | 0.245 | HFPriority | 0 | 0.3988 | 0 | 21.3 | 54.9 | 433010 |  |  | 1 | 0 | ok |
| mnc | 1.2 | 0.245 | MCPriority_safeT | 0.625 | 0 | 0 | 2791 | 79.11 | 177028 | 1 | 88844430 | 17 | 0 | ok |
| mnc | 1.2 | 0.245 | MCPriority_safeF | 0 | 0.6607 | 0 | 89.77 | 31.35 | 1859261 | 0 | 0 | 1 | 0 | ok |
| mnc | 1.2 | 0.245 | MSU-MAU | 1 | 0.02976 | 0.005556 | 7200 | 75.25 | 14141 |  |  | 0 | 0 | timeout |
| mnc | 1.2 | 0.245 | MSU-MIU | 0.0625 | 0.3869 | 0.009524 | 19.91 | 59.82 | 392595 |  |  | 1 | 0 | ok |
| mnc | 1.4 | 0.286 | HFPriority | 0 | 0.3544 | 0 | 14.22 | 33.89 | 396872 |  |  | 1 | 0 | ok |
| mnc | 1.4 | 0.286 | MCPriority_safeT | 0.5 | 0 | 0 | 445.6 | 46.53 | 135674 | 1 | 22245667 | 8 | 0 | ok |
| mnc | 1.4 | 0.286 | MCPriority_safeF | 0 | 0.5949 | 0.0303 | 48.66 | 22.51 | 1335744 | 0 | 0 | 1 | 0 | ok |
| mnc | 1.4 | 0.286 | MSU-MAU | 0.8 | 0.02532 | 0 | 7200 | 43.27 | 15494 |  |  | 0 | 0 | timeout |
| mnc | 1.4 | 0.286 | MSU-MIU | 0 | 0.3797 | 0 | 13.33 | 34.34 | 329794 |  |  | 1 | 0 | ok |
| mnc | 1.6 | 0.326 | HFPriority | 0 | 0.3125 | 0 | 14.15 | 25.08 | 434639 |  |  | 1 | 0 | ok |
| mnc | 1.6 | 0.326 | MCPriority_safeT | 0.6 | 0 | 0 | 406 | 32.64 | 441017 | 1 | 26318023 | 8 | 0 | ok |
| mnc | 1.6 | 0.326 | MCPriority_safeF | 0 | 0.7083 | 0 | 55.36 | 12.14 | 1924490 | 0 | 0 | 0 | 0 | ok |
| mnc | 1.6 | 0.326 | MSU-MAU | 0.9 | 0.04167 | 0 | 7200 | 34.29 | 10668 |  |  | 0 | 0 | timeout |
| mnc | 1.6 | 0.326 | MSU-MIU | 0.1 | 0.4167 | 0 | 14.11 | 24.19 | 507505 |  |  | 0 | 0 | ok |
| rtvcq | 0.4 | 0.023 | HFPriority | 0 | 0.284 | 0.01157 | 2.585 | 3.868 | 24433 |  |  | 0 | 0 | ok |
| rtvcq | 0.4 | 0.023 | MCPriority_safeT | 0.675 | 0 | 0 | 111 | 4.433 | 11548 | 1 | 561145 | 29 | 0 | ok |
| rtvcq | 0.4 | 0.023 | MCPriority_safeF | 0 | 0.4385 | 0.00495 | 4.763 | 3.276 | 42125 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 0.4 | 0.023 | MSU-MAU | 0.1 | 0.175 | 0.01001 | 90.71 | 4.044 | 13865 |  |  | 2 | 0 | ok |
| rtvcq | 0.4 | 0.023 | MSU-MIU | 0 | 0.1676 | 0.007769 | 1.669 | 3.942 | 14416 |  |  | 1 | 0 | ok |
| rtvcq | 0.6 | 0.034 | HFPriority | 0 | 0.3233 | 0.007371 | 2.121 | 3.334 | 30252 |  |  | 0 | 0 | ok |
| rtvcq | 0.6 | 0.034 | MCPriority_safeT | 0.575 | 0 | 0 | 70.69 | 3.838 | 17091 | 1 | 571187 | 15 | 0 | ok |
| rtvcq | 0.6 | 0.034 | MCPriority_safeF | 0 | 0.4841 | 0.01597 | 4.863 | 2.664 | 62091 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 0.6 | 0.034 | MSU-MAU | 0.025 | 0.268 | 0.01794 | 158.5 | 3.369 | 24095 |  |  | 1 | 0 | ok |
| rtvcq | 0.6 | 0.034 | MSU-MIU | 0 | 0.2848 | 0.01839 | 1.258 | 3.229 | 21370 |  |  | 0 | 0 | ok |
| rtvcq | 0.8 | 0.046 | HFPriority | 0 | 0.3934 | 0.01333 | 1.922 | 2.728 | 39148 |  |  | 0 | 0 | ok |
| rtvcq | 0.8 | 0.046 | MCPriority_safeT | 0.5676 | 0 | 0 | 59.08 | 3.269 | 23297 | 1 | 816551 | 18 | 0 | ok |
| rtvcq | 0.8 | 0.046 | MCPriority_safeF | 0 | 0.5383 | 0.02312 | 3.99 | 2.132 | 69368 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 0.8 | 0.046 | MSU-MAU | 0.02703 | 0.2842 | 0.01498 | 186.2 | 2.982 | 28041 |  |  | 0 | 0 | ok |
| rtvcq | 0.8 | 0.046 | MSU-MIU | 0.05405 | 0.2568 | 0.01083 | 1.184 | 2.794 | 22482 |  |  | 0 | 0 | ok |
| rtvcq | 1.2 | 0.068 | HFPriority | 0 | 0.335 | 0 | 1.093 | 2.392 | 33202 |  |  | 0 | 0 | ok |
| rtvcq | 1.2 | 0.068 | MCPriority_safeT | 0.4737 | 0 | 0 | 20.68 | 2.72 | 21130 | 1 | 425395 | 7 | 0 | ok |
| rtvcq | 1.2 | 0.068 | MCPriority_safeF | 0 | 0.4924 | 0 | 2.709 | 1.966 | 55876 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 1.2 | 0.068 | MSU-MAU | 0.2105 | 0.198 | 0 | 153.9 | 2.616 | 18790 |  |  | 0 | 0 | ok |
| rtvcq | 1.2 | 0.068 | MSU-MIU | 0.05263 | 0.1878 | 0.01227 | 0.759 | 2.562 | 16078 |  |  | 0 | 0 | ok |
| rtvcq | 1.4 | 0.08 | HFPriority | 0 | 0.3522 | 0 | 0.892 | 2.104 | 31281 |  |  | 1 | 0 | ok |
| rtvcq | 1.4 | 0.08 | MCPriority_safeT | 0.06667 | 0 | 0 | 9.6 | 2.314 | 18161 | 1 | 220608 | 5 | 0 | ok |
| rtvcq | 1.4 | 0.08 | MCPriority_safeF | 0 | 0.3585 | 0.009709 | 1.636 | 1.999 | 42898 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 1.4 | 0.08 | MSU-MAU | 0.1333 | 0.1635 | 0 | 140.8 | 2.234 | 15205 |  |  | 0 | 0 | ok |
| rtvcq | 1.4 | 0.08 | MSU-MIU | 0.06667 | 0.1887 | 0 | 0.618 | 2.236 | 16440 |  |  | 0 | 0 | ok |
| rtvcq | 1.6 | 0.091 | HFPriority | 0 | 0.3175 | 0.02273 | 0.728 | 2.042 | 26855 |  |  | 0 | 0 | ok |
| rtvcq | 1.6 | 0.091 | MCPriority_safeT | 0.08333 | 0 | 0 | 8.469 | 2.14 | 15728 | 1 | 238940 | 2 | 0 | ok |
| rtvcq | 1.6 | 0.091 | MCPriority_safeF | 0 | 0.3571 | 0 | 1.383 | 1.853 | 38184 | 0 | 0 | 0 | 0 | ok |
| rtvcq | 1.6 | 0.091 | MSU-MAU | 0.08333 | 0.1746 | 0.01869 | 123.6 | 2.058 | 12190 |  |  | 0 | 0 | ok |
| rtvcq | 1.6 | 0.091 | MSU-MIU | 0.08333 | 0.1508 | 0.009174 | 0.325 | 2.066 | 10771 |  |  | 0 | 0 | ok |

## Ghi chú (không framing — control làm B6)
- Baseline MSU-MAU/MIU HF>0 (re-exposure/timeout); MCP-safe HF>0 (no-op) — hợp lệ, ghi nguyên.
- total_RT_sweep bao 6 cell cap 2h. RT một nguồn (cùng VM, cùng code cho cả 245 cell §V).

## §V COMPLETE — tổng 245 cell (9 dataset)
| phần | #cell |
|---|---|
| MAIN (9 ds × 5) | 45 |
| SWEEP 7-dataset | 140 |
| SWEEP IoT (mnc+rtvcq) | 60 |
| **TỔNG** | **245** |

## Checklist trước stop VM (control quyết stop sau verify)
- [x] 60/60 IoT sweep có result; summary.csv=245; boundary_mismatch=0.
- [x] committed+pushed exp/v5-sectionV (ahead 0).
- [x] VIEC_IOT_SWEEP.md (bảng 60 cell + timeout + total RT).
- [x] In dòng IOT SWEEP OK.

**IOT SWEEP OK: 60/60 | timeouts=6 | boundary_mismatch=0**