# VIEC_SMOKE_1B_v2.md — RE-SMOKE sau fix membership (`ws≥ξ` float, bỏ round3)

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-05.
> Fix control (bỏ round3) đã áp + re-gate. Re-smoke 3 cell nặng × 5 method = 15 cell. **Sạch: mọi
> `n_boundary_mismatch=0`, sanity PASS.** 2 timeout hợp lệ (accident m0.8). DỪNG chờ control quyết launch.

## 0. Fix đã áp (commit 8285121) + re-gate
- `metrics.is_frequent` = `ws ≥ ξ` trực tiếp (bỏ `round(·,3)`); nhất quán hiding↔metric↔exact. `round3` vô hiệu.
- `boundary_audit`: band `1e-6`, so `ws_float≥ξ` vs `ws_exact≥ξ` (Fraction). Cổng mismatch>0 ⇒ DỪNG (nay ca thật).
- Miner giữ nguyên (đã `ws≥ξ` float, prune `-1e-12`, không round3).
- **Re-gate PASS:** G1, G2 (HFP C@T3→C@T1), G3 (MCP-safe E@T1→C@T2→C@T4 + Safe-fixture + filter-guard),
  G-B1..7, G5_G7, G6, G-INC1..3 — khớp golden Fraction exact.
- **G-MEMB PASS (mới):** chess m1.0 (5 method) float HF/MC == exact Fraction, `full_mismatch=0`,
  `n_boundary_mismatch=0`; MCP-safe **MC=0 theo CẢ float VÀ exact**; chess m0.6 HFPriority (ca round3 cũ
  fire **1184**) → nay `n_boundary_mismatch=0`.

## 1. Kết quả 15 cell (summary.csv, số ĐO THẬT trên GCP c2-standard-16, PYTHONHASHSEED=0)

| dataset | mult | ξ | method | HF | MC | AC | RT_hiding_s | AC_remine_s | n_del | n_sblk | nbm | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chess_fimi | 0.6 | 0.552 | HFPriority | 0.0 | 0.330989 | 0.002178 | 88.59 | 166.5 | 378 | – | 0 | ok |
| chess_fimi | 0.6 | 0.552 | MCPriority_safeT | 1.0 | 0.0 | 0.0 | 191.39 | 191.5 | 0 | 48262 | 0 | ok |
| chess_fimi | 0.6 | 0.552 | MCPriority_safeF | 0.0 | 0.76515 | 0.003034 | 1709.54 | 47.1 | 7915 | 0 | 0 | ok |
| chess_fimi | 0.6 | 0.552 | MSU-MAU | 0.0 | 0.321997 | 0.001823 | 88.37 | 156.4 | 394 | – | 0 | ok |
| chess_fimi | 0.6 | 0.552 | MSU-MIU | 0.0 | 0.274311 | 0.001722 | 61.57 | 160.3 | 254 | – | 0 | ok |
| mushroom | 0.4 | 0.183 | HFPriority | 0.0 | 0.515277 | 0.009968 | 60.31 | 3.6 | 3734 | – | 0 | ok |
| mushroom | 0.4 | 0.183 | MCPriority_safeT | 1.0 | 0.0 | 0.0 | 60.26 | 6.4 | 320 | 98978 | 0 | ok |
| mushroom | 0.4 | 0.183 | MCPriority_safeF | 0.0 | 0.474667 | 0.001259 | 60.70 | 4.1 | 3814 | 0 | 0 | ok |
| mushroom | 0.4 | 0.183 | MSU-MAU | 0.0 | 0.410353 | 0.001358 | 20.88 | 5.0 | 1057 | – | 0 | ok |
| mushroom | 0.4 | 0.183 | MSU-MIU | 0.0 | 0.300967 | 0.000249 | 10.88 | 6.1 | 696 | – | 0 | ok |
| accident | 0.8 | 0.601 | HFPriority | 0.0 | 0.41168 | 0.002435 | 46.14 | 367.9 | 63549 | – | 0 | ok |
| accident | 0.8 | 0.601 | **MCPriority_safeT** | 0.875 | 0.0 | 0.0 | **7200.0** | 589.6 | 27189 | 14,317,999 | 0 | **timeout** |
| accident | 0.8 | 0.601 | MCPriority_safeF | 0.0 | 0.847774 | 0.003135 | 837.63 | 97.4 | 1,787,884 | 0 | 0 | ok |
| accident | 0.8 | 0.601 | **MSU-MAU** | 0.625 | 0.147439 | 0.0 | **7200.0** | 522.2 | 13770 | – | 0 | **timeout** |
| accident | 0.8 | 0.601 | MSU-MIU | 0.0 | 0.390139 | 0.00313 | 29.09 | 396.3 | 49743 | – | 0 | ok |

## 2. Sanity gates (PASS)
- **Mọi HFPriority HF=0** ✓ (3/3). **Mọi MCP-safe MC=0** ✓ (3/3, kể cả cell timeout — Safe giữ MC=0).
- **Mọi `n_boundary_mismatch=0`** ✓ (15/15) — fix membership xác nhận trên DB thật, kể cả cell timeout.
- Không NaN, đủ 16 cột. summary.csv = 15 dòng khớp JSON.
- **2 timeout hợp lệ (ghi nguyên, honest):** accident m0.8 `MCPriority_safeT` (RT=cap 2h, MC=0 giữ,
  HF=0.875 — chưa ẩn hết trong hạn) và `MSU-MAU` (baseline dense trên accident — đúng dự đoán handoff).
  Cả hai `status=timeout, RT=7200s` → **loại khỏi đường cong RT** (không cắt lén).

## 3. Quan sát (không framing, cho control)
- Cell "nặng nhất theo #FWI" (chess m0.6 = 517k FWI) **KHÔNG timeout** (max 28min ở MCP-safeF). Timeout
  do **|D| lớn + NS dày** (accident 340k txn, NS≈2089 → safe-check MCP-safeT chạy 14.3M lần; baseline
  MSU-MAU xóa trên DB khổng lồ). Tức driver timeout = accident (dense, |D| lớn), không phải #FWI.
- MCP-safe ở ξ thấp thường **no-op sớm** (chess m0.6: n_del=0; mushroom m0.4: 320) → HF cao, MC=0 (hợp lệ).
- AC re-mine bám mine_time theo ξ: mushroom ~5s, chess ~50–190s, accident ~370–590s.

## 4. ƯỚC LẠI TỔNG GIỜ PHA 1b (175 cell = 35 main + 140 sweep; chainstore đã loại sweep)
> Ước thô, có số smoke thật cho 3 điểm nặng nhất; **bms-pos & kosarak hiding RT CHƯA đo** (wildcard).
- **15 cell smoke = 4.91h RT + 0.76h AC** (bị chi phối bởi 2×2h timeout accident).
- Phân loại rủi ro (deadline 2h/cell bao trần):
  - **accident** (m0.8/m1.0/m1.2 × 5 = 15 cell): nặng nhất. m0.8 = 2 timeout + 3 cell (≈0.25h); m1.0
    MCP-safeT ~0.76h (operating cũ 2730s, KHÔNG timeout) + MSU-MAU **nghi timeout** (dense); m1.2 thưa nhanh.
    Ước accident ≈ **5–8h** (gồm 2–4 timeout).
  - **chess** (15 cell): ≈ 1–1.5h. **mushroom** (35 cell): ≈ 0.3–0.6h (|D| nhỏ).
  - **retail** (35 cell, |D|=88k): ≈ 1–2h. **bms-pos** (35, |D|=515k) + **kosarak** (35, |D|=990k):
    NS thưa (≈100–2000) ⇒ safe-check bounded ⇒ *dự đoán* không timeout, nhưng |D| lớn → ước ≈ **4–10h**
    (CHƯA đo — cần xác nhận).
- **Tổng ước ≈ 15–30h** (bao gồm ~2–4 cell timeout ở accident). Nhiều khả năng **≤ ~48h** (ngưỡng handoff).
  Rủi ro chính = bms-pos/kosarak chưa đo.

## 5. CẦN CONTROL QUYẾT (van dừng — KHÔNG tự phóng full)
1. **Phóng PHA 1b full 175 cell** ngay (bounded bởi cap 2h/cell), HAY
2. **De-risk trước:** smoke thêm điểm dày nhất của **bms-pos (m0.4)** + **kosarak (m0.4)** để chốt chúng
   không timeout, rồi mới phóng. (Đề xuất nhẹ; control chọn.)
3. Tỉa mult nếu muốn giảm tải (vd bỏ accident m0.8 khỏi sweep do 2 timeout — nhưng timeout là dữ liệu
   hợp lệ, giữ được).

## 6. Trạng thái repo
- Fix + G-MEMB + boundary_audit mới: committed (8285121). 15 result + summary.csv: committed+pushed
  (c039e2a). Branch synced (`git status -sb` ahead 0). Coordinator DONE, `pgrep` sạch.
- Diagnostics cũ (`coordinator/diag_*.py`) giữ lại (read-only, không ảnh hưởng chạy).
- Result cũ round3 (chess m0.6 HFPriority MC=0.330222) đã invalidate; số mới MC=0.330989.

## 7. Ghi chú workflow (deviation minh bạch)
Handoff §1 gợi ý sửa trên branch `claude/fwi-part3-part4-setup-y7ex9h` rồi merge. Branch đó **predates toàn
bộ §V** (coordinator/sweep/engine-fix) → checkout+merge có nguy cơ **revert code đã verify**. Tôi áp fix
**trực tiếp trên `exp/v5-sectionV`** (branch làm việc duy nhất, một git writer, không rebase/không main) —
an toàn hơn, cùng kết quả. Nêu để control biết.

## 8. RESUME (nếu control phóng full)
```bash
cd ~/FWI_hiding_system && source .venv/bin/activate
setsid nohup python3 coordinator/run_coordinator.py >/dev/null 2>&1 </dev/null & disown
pgrep -af run_coordinator          # verify + ps -o ppid= =1
# resume idempotent (skip 15 cell smoke đã có). Watch: results/summary.csv + logs.
```

**RE-SMOKE XONG — sạch (nbm=0), sanity PASS, 2 timeout hợp lệ, ước ≈15–30h. Chờ control quyết launch
PHA 1b full (hoặc de-risk bms-pos/kosarak trước).** Không tự phóng.
