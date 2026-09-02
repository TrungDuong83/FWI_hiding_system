# VIEC_COORD_PREP — §V coordinator (B1: CHUẨN BỊ, chưa chạy cell)

> Deliverable B1: `coordinator/run_coordinator.py` + verify lưới 35 cell + logging đủ cột.
> Branch: `exp/v5-sectionV` (tách từ `claude/fwi-part3-part4-setup-y7ex9h`, có sẵn code + 7 calib).
> Số dưới đây là output THẬT (static check + probe). CHƯA phóng.

## Lưới ô (35 = 7 dataset × 5 method)
- Methods: `HFPriority`, `MCPriority_safeT`, `MCPriority_safeF`, `MSU-MAU`, `MSU-MIU`.
- Datasets (fast→slow): chess_fimi, mushroom, retail, bms-pos, kosarak, accident, chainstore.
- Static check: `n_cells=35`, `GRID_OK=True`, deadline hiding=7200s, AC re-mine cap=20 (>7).
- Mỗi cell map đúng `calib_<ds>.json` (|sfwi|==n_sfwi verified ×7).

## Logging (đủ mọi cột §3)
`results/result_<ds>_<method>.json`:
`{dataset, method, xi, HF, MC, AC, RT_hiding_s, n_noop, n_safe_blocked, n_deletions, AC_remine_s, source, status}`
- `RT_hiding_s` = wall-clock CHỈ pha hiding (chốt TRƯỚC AC re-mine). `AC_remine_s` = thời gian re-mine (đo riêng).
- `n_noop`/`n_safe_blocked`: CHỈ MCPriority (method khác = null).
  - `n_safe_blocked` (safeT): đếm qua **monkeypatch `mcpriority.is_safe`** (KHÔNG sửa source frozen).
  - `n_deletions`: đếm qua **wrap `db.delete`** (sống sót cả khi timeout).
  - `n_noop` = 1 nếu HF>0 (dừng bằng no-op) else 0; safeF luôn ẩn hết ⇒ 0.
- `status ∈ {ok, timeout, error}`. `source` = hostname (RT một nguồn).
- `results/progress_<ds>.json` {done[], attempts}; `results/summary.csv` regenerate từ JSON.

## Backend + reuse
- §V backend = float64 + round(ws,3)≥ξ (SPEC_PART4 §2/§5). S=sfwi[], ~S=fwi[]\sfwi[] (frozen calib).
- Reuse KHÔNG sửa: hfpriority/mcpriority/baseline_ppum, metrics, miner, calib. MỘT git writer=coordinator,
  checkpoint+push mỗi ô (exp branch), resume idempotent (skip nếu result đã có).
- Deadline 2h CHỈ pha hiding (SIGALRM). AC re-mine KHÔNG deadline.

## ⚠️ PHÁT HIỆN RT (probe, TRƯỚC smoke) — CẦN CONTROL LƯU Ý
`common.HidingDB.ws(X)` (frozen) = O(|cover(X)|) mỗi lần gọi; hiding gọi ws O(#deletions × |S|) lần.
Chi phí phụ thuộc **kích thước cover** của SFWI (= #giao dịch chứa) → phụ thuộc ξ × mật độ × |D|.

| dataset | ξ | \|D\| | cover(SFWI) | Hiding khả thi? |
|---|---|---|---|---|
| chainstore | 0.003 | 1.11M | 3.3k–7.8k | ✔ (HFPriority 167s, 23.5k dels, HF=0) |
| accident | **0.751** | 340k | **258k–311k** | �’**KHÔNG** trong 2h |

- **accident** (ξ=0.751 cao × 340k dày): cover SFWI ≈ 260k–311k. Mỗi `ws` ≈ 0.77s; `exposed_any()`
  quét 28 SFWI ⇒ ~21s/deletion; hiding cần hàng nghìn deletion ⇒ **vượt xa 2h** (probe: 71 deletion/55s
  chỉ hạ ws 0.95→0.916, chưa ẩn nổi 1 SFWI). ⇒ 5 cell accident sẽ **status=timeout**.
- Các dataset ξ thấp (retail/bms-pos/kosarak/chainstore) cover nhỏ ⇒ nhanh dù |D| tới 1.1M.
- **KHÔNG tự sửa** `common.HidingDB` (frozen §4). **CẦN CONTROL QUYẾT** chiến lược accident, ví dụ:
  (a) chấp nhận accident timeout (ghi status=timeout); (b) cho phép tối ưu `HidingDB.ws` incremental
  (unfreeze common.py có kiểm gate lại); (c) re-calibrate accident ξ thấp hơn (cover nhỏ). — chờ duyệt.

## Smoke chọn dataset (B2)
Chọn **chainstore** (1M-tx — khâu AC re-mine đắt nhất mà prompt §5 nhắm; cover nhỏ nên hiding hoàn tất
⇒ validate ĐỦ plumbing: 5 method, counters, AC re-mine 1M-tx, push). accident RT-infeasible đã báo ở trên
(không smoke để tránh 2h×5 timeout vô ích; đã có bằng chứng probe).

## RESUME_CMD
```
# smoke 1 dataset (5 method):
setsid nohup python3 coordinator/run_coordinator.py chainstore >/dev/null 2>&1 </dev/null & disown
# phóng toàn bộ (SAU khi control duyệt smoke):
setsid nohup python3 coordinator/run_coordinator.py >/dev/null 2>&1 </dev/null & disown
```
