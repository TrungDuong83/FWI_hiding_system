# VIEC_SMOKE_1B.md — SMOKE 1b: CỔNG DỪNG boundary_mismatch (báo control)

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-04.
> **TRẠNG THÁI: DỪNG tại cell smoke đầu tiên do `n_boundary_mismatch>0`.** Coordinator tự halt (exit 3)
> đúng spec. KHÔNG tự sửa spec/calib/thuật toán/metric. Cần **control quyết** cách xử lý backend membership.

## 1. Sự việc
Chạy `run_coordinator.py --smoke` (3 cell nặng × 5 method). Cell #1:
```
[chess_fimi/m0.6/HFPriority] ok HF=0.0 MC=0.330222 AC=0.002174 RT=77.135s AC_rem=163.298s
    n_del=380  n_boundary=11133  n_boundary_mismatch=1184
[STOP] n_boundary_mismatch=1184 ⇒ DỪNG báo control
```
Boundary audit: itemset X có `|round3(ws_float)−ξ| ≤ 0.0015` → recompute exact Fraction; **1184/11133**
itemset cho quyết định membership `round3(ws)≥ξ` KHÁC `ws_exact≥ξ`.

## 2. Chẩn đoán (read-only, KHÔNG sửa gì) — 3 bước loại trừ

### (a) Trên DB GỐC (CHƯA hiding): mismatch = 0 kể cả ở ξ sweep
```
chess_fimi m1.0 ξ=0.92 : n_boundary=7      n_mismatch=0
chess_fimi m0.6 ξ=0.552: n_boundary=12142  n_mismatch=0     ← ξ sweep KHÔNG gây mismatch khi DB tươi
mushroom  m1.0 ξ=0.457 : n_boundary=4      n_mismatch=0
```
⇒ Không phải lỗi ξ sweep, không phải lỗi audit. FWI gốc đều có exact ws≥ξ (do freeze) nên round3 & exact
đồng thuận.

### (b) SAU hiding: mismatch xuất hiện — KHÔNG phải trôi số num_cache
So 3 cách tính ws cho itemset ở biên (chess m0.6 sau HFPriority):
```
n_boundary=11133  mismatch_INCREMENTAL(num_cache)=1184  mismatch_FRESH_float=1184   (BẰNG NHAU)
ví dụ: round3(incremental)=0.552  round3(fresh_float)=0.552  exact_ws=0.5517654  (ξ=0.552)
```
`fresh_float == incremental` ⇒ **KHÔNG phải trôi số `num_cache` incremental**. `num_cache` đúng.

### (c) Root cause = NGỮ NGHĨA `round(ws,3) ≥ ξ` của backend production (SPEC §B.1)
- `round(ws,3) ≥ ξ` phân loại **frequent** mọi itemset có exact ws ∈ **[ξ−0.0005, ξ)** (làm tròn LÊN tới ξ).
- **Trước hiding:** mọi FWI có exact ws ≥ ξ ⇒ không xung đột.
- **Sau hiding:** deletions làm ws tụt; itemset rơi vào "vùng bóng làm tròn" [ξ−0.0005, ξ) thì **exact = đã
  ẩn/mất** (ws<ξ) nhưng **round3 = còn lộ/còn frequent** (ws làm tròn = ξ). ⇒ **mismatch**.
- Hệ quả metric: round3 **đếm thiếu** MC (NSFWI thực đã mất bị coi là còn) và có thể lệch HF.

## 3. Blast radius — mismatch có ở CẢ MAIN (ξ calibrated), không chỉ sweep

`n_boundary_mismatch` SAU hiding (DB thật, 5 method):

| method | chess m1.0 | mushroom m1.0 | retail m1.0 | chess **m0.6 (sweep)** |
|---|---|---|---|---|
| HFPriority       | 1 (nb11) | 0 (nb4)  | 4 (nb67) | **1184 (nb11133)** |
| MCPriority_safeT | **23** (nb46) | **88** (nb90) | **30** (nb92) | (chưa chạy) |
| MCPriority_safeF | 1 (nb4)  | 0 (nb6)  | 2 (nb73) | (chưa chạy) |
| MSU-MAU          | 2 (nb11) | 4 (nb10) | 3 (nb75) | (chưa chạy) |
| MSU-MIU          | 2 (nb11) | 0 (nb6)  | 1 (nb73) | (chưa chạy) |

Nhận định:
- Mismatch **pervasive** ở MAIN (nhỏ, 0–4) và **khuếch đại mạnh** ở điểm sweep dày/ξ thấp (chess m0.6 =
  1184) — tỉ lệ thuận mật độ itemset gần ngưỡng.
- **MCPriority-safe luôn cao nhất** (23/88/30): thuật toán xóa tới khi NSFWI **đúng ngay ngưỡng round3**,
  nên để lại nhiều NSFWI trong vùng bóng ⇒ exact nói một số NSFWI đã tụt <ξ. Tức **đảm bảo MC=0 chỉ đúng
  theo round3, KHÔNG đúng theo exact**.
- ⇒ **Cổng `n_boundary_mismatch>0 ⇒ DỪNG` như đặc tả là bất khả thi với backend round3**: nó sẽ fire ở
  gần như MỌI cell (kể cả 35 MAIN). Đây là mâu thuẫn spec, không phải lỗi code.

## 4. ĐÂY LÀ QUYẾT ĐỊNH CONTROL (van dừng — tôi KHÔNG tự quyết/sửa)
Các hướng khả dĩ (nêu trung tính, control chọn; mỗi hướng đụng SPEC nên vượt phạm vi thực thi):
1. **Metric membership → exact Fraction** cho HF/MC cuối (module metrics đã có `round3=False`). Thuật toán
   hiding có thể giữ round3 nội bộ (quyết định vận hành) nhưng SỐ báo cáo = exact ⇒ mismatch = 0 theo định
   nghĩa. Cần chốt AC re-mine (miner dùng float round3) cho nhất quán. *Đụng SPEC §5 (production=round3).*
2. **Boundary audit thành CHỈNH SỬA, không phải cổng chặn**: recompute exact cho các itemset ở biên và
   dùng quyết định exact cho metric; `n_boundary_mismatch` chỉ log chẩn đoán, bỏ hard-stop.
3. **Giữ round3 là định nghĩa membership chính thức của bài** (ghi rõ trong paper), **bỏ/nới cổng** — chấp
   nhận HF/MC theo round3 nhất quán với định nghĩa round3 đã tuyên bố. exact chỉ dùng cho calibration.
4. **Nudge ξ** khỏi lưới round3 để exact≡round3 — đổi ξ, phá freeze calibration (nhiều khả năng không nên).

> Tôi KHÔNG chọn hướng nào. KHÔNG sửa metrics/spec/calib. Chờ control chốt rồi mới tiếp.

## 5. Mission smoke (đo timeout) — BỊ CHẶN
Smoke halt ở cell #1 nên CHƯA đo được RT/timeout của MCPriority trên các cell nặng. Điểm dữ liệu duy nhất:
`chess m0.6 HFPriority RT_hiding=77.135s, AC_remine=163.298s, n_del=380`. Ước lại tổng giờ PHA 1b **hoãn**
tới khi control chốt backend membership (vì metric có thể tính lại).

## 6. Artefact & trạng thái repo
- `results/result_chess_fimi_m0.6_HFPriority.json` + `summary.csv` (1 dòng) đã commit (9998705) — dữ liệu
  THẬT nhưng metric theo round3 đang bị đặt câu hỏi; **nên invalidate sau khi control chốt hướng** (sẽ tính lại).
- Diagnostics (read-only, không đụng logic): `coordinator/diag_boundary.py`, `diag_drift.py`, `diag_main.py`
  + logs `logs/diag_*.log`.
- Coordinator (đã dừng, `pgrep` sạch). KHÔNG cell nào khác chạy. Branch synced.

## 7. RESUME (sau khi control chốt)
```bash
cd ~/FWI_hiding_system && source .venv/bin/activate
# tuỳ quyết định control (vd exact metric) → điều chỉnh, re-verify golden G1/G2/G3, rồi:
python3 coordinator/run_coordinator.py --smoke      # smoke lại 3 cell nặng
```

**DỪNG — chờ control quyết hướng xử lý cổng round3 vs exact.** Không launch, không sửa spec/calib/metric.
