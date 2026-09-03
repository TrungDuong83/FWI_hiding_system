# VIEC_SAFE_INCREMENTAL — Safe/ws incremental (num_cache, SPEC §3.3) + re-gate + re-smoke

> Mục tiêu: gỡ chặn RT (MCP-safe timeout 1M-tx) bằng **num_cache incremental** đúng SPEC §3.3.
> KHÔNG đổi thuật toán/kết quả/ξ/S/~S — chỉ tăng tốc. Số dưới đây là output THẬT.
> Sửa `common.py`/`mcpriority.is_safe` trên `claude/fwi-part3-part4-setup-y7ex9h` (re-gate),
> merge sang `exp/v5-sectionV` (re-smoke 2 cell). MỘT git writer, checkpoint+push.

## Thay đổi (surgical, chỉ đường ws/Safe)
- `common.HidingDB.__init__(track=None)`: build `num_cache[X]=Σ_{T⊇X} tw(T)` cho X∈S∪~S (O(|track|·cover), 1 lần).
- `delete(v,t)`: cập nhật incremental (Bẫy #1) — 3-case SPEC §3.3: `v∈X ⇒ -tw_old`; `X⊆t ∧ v∉X ⇒ +（tw_new-tw_old)`.
- `ws(X)`: X∈track ⇒ `num_cache[X]/W_total` **O(1)**; ngoài track ⇒ đường cũ O(cover) (fallback, kết quả y hệt).
- `mcpriority.is_safe`: dùng `num_cache[ns]` (O(1)/ns ⇒ **O(|~S|)**); db không track ⇒ fallback O(cover) **y hệt oracle cũ**.
- `coordinator`: dựng `HidingDB(D, Wf, track=S+NS)`.
> Không đụng logic HFP/MCP/baseline, không đổi ξ/S/~S/metric. AC vẫn re-mine đầy đủ.

## Quyết định dtype num_cache: **FLOAT** (G-INC2 chứng minh zero drift)
G-INC2 chess_fimi MCP-safe: `num_cache` **Fraction (exact)** vs **float64+round3** → HF/MC/AC + lost/residual
**KHỚP CHÍNH XÁC** (HF=0.821429, MC=0, AC=0, cùng 23 residual). Không có drift lật biên round3 ⇒ dùng float
(nhanh). (Cùng bản chất parity G5 đã có, nay xác nhận ở quy mô + num_cache incremental.)

## Re-gate (output THẬT, 2 vòng sạch liên tiếp)
Fast suite ×2 vòng — tất cả PASS: `miner`, `metrics unit`, `G1`, `G2 (C@T3→C@T1)`, `G3 (E@T1→C@T2→C@T4 +
nosafe + Safe fixture + filter-guard)`, `G5 (float↔Fraction)`, `G6 (oracle chess 584/mushroom 57)`,
`G7`, `G-B1..B7 (baseline)`. Calib re-gate (nền): `CALIB gates PASS` (G-C1..C4 ×7).
```
[G-INC1 hfp]   trace/HF/MC/lost/resid oracle==incremental: True (C@T3 -> C@T1 HF=0 MC=3/7)
[G-INC1 safeT] ...: True (E@T1 -> C@T2 -> C@T4 HF=1/2 MC=0)
[G-INC1 safeF] ...: True (E@T1 -> E@T2 -> A@T3 HF=0 MC=4/7)
[G-INC1] num_cache[X]==Σtw(T⊇X) ∀ tracked X: True
[G-INC1 safe-fixture] is_safe oracle=False incremental=False: True
[G-INC2] Fraction==float64+round3 (HF/MC/AC/lost/resid): True -> numcache=float
[G-INC3] run1==run2 (HF/MC/AC/lost/resid/n_del): True (HF=0.8214 MC=0 AC=0 n_del=161)
```
> G-INC1 parity: incremental tái tạo Y HỆT oracle (3 golden trace + Safe fixture + bất biến num_cache).
> KHÔNG lệch 1 itemset. (oracle/Fraction là chuẩn — incremental khớp ⇒ incremental đúng.)

## Re-smoke 2 cell khó × MCPriority(safe=True) — output THẬT
| cell | RT_hiding (oracle cũ) | RT_hiding (incremental) | status | HF | MC | AC | AC_remine | n_del | n_safe_blocked |
|---|---|---|---|---|---|---|---|---|---|
| chainstore | **timeout 7200s** | **5.385s** | ok | 0.0 | 0.0 | 0.0 | 310.8s | 29304 | 0 |
| accident | (infeasible) | **2730.5s** (< 7200s) | ok | 0.785714 | 0.0 | 0.0 | 103.7s | 70379 | 26,331,107 |

- **chainstore:** timeout → 5.4s (~1300×). Ẩn hết an toàn (HF=0, MC=0, n_safe_blocked=0: không nước nào bị veto).
- **accident:** LỌT 2h (2730s). MCPriority ẩn an toàn 6/28 SFWI, **veto 26.3M nước** để bảo toàn NSFWI rồi
  dừng no-op ⇒ HF=0.786 nhưng **MC=0 BY CONSTRUCTION** (đúng bản chất MCPriority: chấp nhận HF>0 giữ MC=0).
  Không đụng ξ. (Với oracle O(|~S|·cover): 26.3M×271×270k ⇒ ~10^15 ⇒ vô vọng; incremental O(|~S|): ~7×10^9 ⇒ 2730s.)
- AC=0 cả hai; AC re-mine đo được (103–311s).

## Kết luận
Cả HAI chặn RT ở VIEC_SMOKE (A: MCP-safeT timeout ≥500k tx; B: accident vô vọng) **đã gỡ** bằng incremental
đúng SPEC §3.3, kết quả bất biến (re-gate + parity). Coordinator sẵn sàng phóng 35 cell.
→ **DỪNG chờ control duyệt** trước khi phóng toàn bộ.

## RESUME_CMD
```
# re-gate:
PYTHONHASHSEED=0 python3 tests/test_ginc.py         # G-INC PASS
for t in tests/test_g1 tests/test_g2_hfp tests/test_g3_mcp tests/test_g5_g7 tests/test_g6 tests/test_baseline_golden; do PYTHONHASHSEED=0 python3 $t.py; done
# phóng 35 cell (SAU khi control duyệt):
PYTHONHASHSEED=0 setsid nohup python3 coordinator/run_coordinator.py >/dev/null 2>&1 </dev/null & disown
```
