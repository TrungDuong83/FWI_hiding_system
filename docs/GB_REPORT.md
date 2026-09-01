# GB_REPORT — Verify Đợt B (hiding layer + metrics): G2 / G3 / G5 / G7 + filter-guard

> Đợt B code lại PART 4 hiding (HFPriority/MCPriority) + 4 metric FWI, reuse nguyên
> `common.HidingDB` / `select_victim` / `preprocess` / `miner` (frozen Đợt A). Mọi số dưới đây là
> output THẬT của các test entry-guarded (không bịa). Golden verify bằng `Fraction` (exact).

## Thành phần
- `src/metrics/metrics.py` — HF, MC, AC, RT (SPEC §5). HF/MC qua `HidingDB.ws` (W_total hiện tại,
  Bẫy #1); AC set-diff (caller mine bằng `miner.mine_fwi`); membership `round3` cho production.
- `src/hiding/hfpriority.py` — Max-Conflict (SPEC §3.2): T_sensitive CÓ filter `ws(s)≥ξ`,
  order tw↓ tie TID↑ numeric, `select_victim(score_hfp, safe=None)`, 1 delete/giao dịch, Φ0-guard.
- `src/hiding/mcpriority.py` — Min-Side-Effect (SPEC §3.3): `safe_check`/`order` tham số hóa;
  `Safe(v,t)` FULL-check TOÀN ~S theo W'_total mới; dừng **no-op** (full-pass-no-move).

## G2 — HFPriority (tests/test_g2_hfp.py)
```
[g2_hfp] trace=C@T3 -> C@T1 ok=True
[g2_hfp] HF=0 (exp 0) ok=True ; MC=3/7 (exp 3/7) lost=['ACD', 'C', 'CD'] ok=True
[g2_hfp] AC=0 (exp 0) ok=True
G2 PASS
```

## G3 — MCPriority (tests/test_g3_mcp.py)
```
[g3 safe=True]  trace=E@T1 -> C@T2 -> C@T4 ; HF=1/2 MC=0 AC=0 residual=['AC'] ok=True
[g3 safe=False] trace=E@T1 -> E@T2 -> A@T3 ; HF=0 MC=4/7 AC=0 lost=['A', 'ACD', 'AD', 'E'] ok=True
[g3 safe-fixture] Safe_full(B,T2)=False (exp False) ; Safe_reduced(B,T2)=True (exp True) ns⊆T2=['B'] ok=True
[g3 filter-guard] trace=A@T1 -> A@T2 -> C@T4 ; HF=1/2 (exp 1/2) MC=0 (exp 0) AC=0 (exp 0; nếu 1/9 ⇒ filter hỏng) |~S|=7 ok=True
G3 PASS
```
- **Safe fixture** chứng minh `Safe` full-check ≠ reduced: reduced chỉ thấy `ns⊆T2={B}` (→True, SAI),
  full-check bắt AC/BC/C ở T3 tụt dưới ξ (→False, ĐÚNG). Code dùng full.
- **filter-guard** (`W={A:3/10,B:1/10,C:3/10,D:4/5}`, ξ=41/100, S={AC,BC}): filter `ws(s)≥ξ` cho **AC=0**;
  nếu bỏ filter sẽ có deletion thừa → phantom → AC=1/9 (FAIL). AC=0 xác nhận filter còn.

## G5 — Parity float64+round3 ↔ Fraction (tests/test_g5_g7.py)
```
[G5 HFP] parity(float↔frac)=True match_golden=True trace=C@T3 -> C@T1 HF=0 MC=3/7 AC=0
[G5 MCP_safeT] parity(float↔frac)=True match_golden=True trace=E@T1 -> C@T2 -> C@T4 HF=1/2 MC=0 AC=0
[G5 MCP_safeF] parity(float↔frac)=True match_golden=True trace=E@T1 -> E@T2 -> A@T3 HF=0 MC=4/7 AC=0
G5 PASS
```
Ba trace + HF/MC/AC (kèm tập lost/residual) của backend **float64 + round(ws,3)≥ξ** khớp CHÍNH XÁC
backend **Fraction** — ZERO mismatch — và khớp giá trị golden đã chốt.

## G7 — Determinism (tests/test_g5_g7.py)
```
[G7 HFP] run1==run2 = True
[G7 MCP_safeT] run1==run2 = True
[G7 MCP_safeF] run1==run2 = True
[G7 mining] single==MP set = True (#=9)
GB(G5+G7) PASS
```
Chạy 2 lần cùng input → trace + toàn bộ metric y hệt. Mining bật MP (`use_mp=True`) cho cùng SET FWI
với đơn luồng (dedup theo `tuple(sorted(pattern))` ⇒ bất biến thứ tự worker — SPEC_PART3_FIX §3).

## Bảng tổng hợp (số THẬT)
| Config | Trace | HF | MC (lost) | AC | residual |
|---|---|---|---|---|---|
| HFPriority | C@T3 → C@T1 | 0 | 3/7 {C,CD,ACD} | 0 | — |
| MCPriority safe=True (mc_tid) | E@T1 → C@T2 → C@T4 | 1/2 | 0 | 0 | {AC} |
| MCPriority safe=False (mc_tid) | E@T1 → E@T2 → A@T3 | 0 | 4/7 {A,AD,ACD,E} | 0 | — |
| Safe fixture | — | — | — | — | full=False≠reduced=True |
| filter-guard (safe=True) | A@T1 → A@T2 → C@T4 | 1/2 | 0 | **0** (không 1/9) | — |

| Gate | Nội dung | Kết quả |
|---|---|---|
| G2 | HFPriority golden | PASS |
| G3 | MCPriority golden ×2 + Safe fixture + filter-guard | PASS |
| G5 | Parity float64+round3 ↔ Fraction (3 trace) | PASS, zero mismatch |
| G7 | Determinism (2 lần + mining MP) | PASS |

**VERDICT Đợt B: PASS.** (CHƯA baseline_ppum — việc riêng sau.)

## Tái lập
```
python3 src/metrics/metrics.py     # METRICS UNIT PASS
python3 tests/test_g2_hfp.py       # G2 PASS
python3 tests/test_g3_mcp.py       # G3 PASS
python3 tests/test_g5_g7.py        # GB(G5+G7) PASS
```
