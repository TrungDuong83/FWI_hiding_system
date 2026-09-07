# VIEC_IOT_RUN.md — 5 method cho IoT (mnc + rtvcq) tại operating ξ — cùng VM §V

> Repo exp/v5-sectionV · VM hshfwup-run (RT một nguồn, cùng máy 7 dataset) · code cuối (ws≥ξ float, không round3) · PYTHONHASHSEED=0 · 2026-09-07.

**IOT RUN OK: mnc 5/5 rtvcq 5/5 | timeouts=1 (mnc/MSU-MAU) | boundary_mismatch=0**

## Gates (PASS)
- Mọi HFPriority HF=0 ✓; mọi MCPriority_safeT MC=0 ✓ (kể cả cell chậm); mọi n_boundary_mismatch=0 ✓ (10/10).
- source=hshfwup-run (RT cùng máy 7 dataset) ✓. Baseline MSU-MAU/MIU HF>0 (re-exposure) + MCP-safe HF>0 (no-op) — hợp lệ, ghi nguyên.
- summary.csv = 185 dòng (175 §V + 10 IoT).

## Bảng 10 cell (số đo THẬT, mọi cột)
| dataset | method | ξ | HF | MC | AC | RT_hiding_s | AC_remine_s | n_del | n_noop | n_sblk | nb | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mnc | HFPriority | 0.204 | 0.0 | 0.455556 | 0.051613 | 42.387 | 75.686 | 720691 |  |  | 1 | 0 | ok |
| mnc | MCPriority_safeT | 0.204 | 0.444444 | 0.0 | 0.0 | 1644.477 | 110.437 | 454309 | 1 | 38283165 | 30 | 0 | ok |
| mnc | MCPriority_safeF | 0.204 | 0.0 | 0.666667 | 0.1 | 153.625 | 44.104 | 2418719 | 0 | 0 | 0 | 0 | ok |
| mnc | MSU-MAU | 0.204 | 0.888889 | 0.011111 | 0.0 | 7200.0 | 109.105 | 16032 |  |  | 0 | 0 | timeout |
| mnc | MSU-MIU | 0.204 | 0.0 | 0.462963 | 0.026846 | 28.825 | 80.353 | 498099 |  |  | 2 | 0 | ok |
| rtvcq | HFPriority | 0.057 | 0.0 | 0.394052 | 0.012121 | 1.472 | 2.39 | 37795 |  |  | 0 | 0 | ok |
| rtvcq | MCPriority_safeT | 0.057 | 0.576923 | 0.0 | 0.0 | 30.69 | 2.968 | 17122 | 1 | 556454 | 11 | 0 | ok |
| rtvcq | MCPriority_safeF | 0.057 | 0.0 | 0.513011 | 0.022388 | 3.212 | 2.036 | 60537 | 0 | 0 | 0 | 0 | ok |
| rtvcq | MSU-MAU | 0.057 | 0.076923 | 0.260223 | 0.019512 | 166.873 | 2.725 | 22852 |  |  | 1 | 0 | ok |
| rtvcq | MSU-MIU | 0.057 | 0.038462 | 0.297398 | 0.005236 | 1.047 | 2.509 | 23836 |  |  | 0 | 0 | ok |

## Ghi chú (không framing — control làm B6)
- **mnc MSU-MAU timeout 2h** (RT=cap): HF=0.889 tại cap, n_del=16032 — baseline chậm trên MNC dày/lặp (737k txn, 72% dòng trùng), giống accident/kosarak §V. Loại khỏi đường cong RT.
- mnc MCPriority_safeT: RT=1644s (~27min, KHÔNG timeout), MC=0, n_safe_blocked=38.3M, HF=0.444 (no-op giữ MC=0).
- ξ operating: rtvcq=0.057 (#FWI295/#SFWI26), mnc=0.204 (#FWI297/#SFWI27). Sweep IoT: CHƯA (control quyết sau).

## Trạng thái
- 10 result JSON + summary.csv (185) committed+pushed (32930ea, merged control cfg_mnc). Branch synced. Coordinator DONE, pgrep sạch. VM GIỮ SỐNG.
- **IOT RUN OK: mnc 5/5 rtvcq 5/5 | timeouts=1 (mnc/MSU-MAU) | boundary_mismatch=0**