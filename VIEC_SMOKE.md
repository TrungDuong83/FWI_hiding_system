# VIEC_SMOKE — §V coordinator SMOKE (B2), DỪNG chờ control duyệt

> Smoke dataset = **chainstore** (1M-tx: khâu AC re-mine đắt nhất; cover nhỏ nên hiding chạy được ⇒
> validate đủ plumbing). 5/5 cell chạy qua coordinator nền (PID 1749, PPID=1), checkpoint+push mỗi ô.
> Số dưới đây là output THẬT (results/summary.csv + logs/coord_smoke.log). CHƯA phóng 30 cell còn lại.

## Kết quả 5 cell (chainstore, ξ=0.003, |S|=10, |~S|=254)
| method | status | HF | MC | AC | RT_hiding_s | AC_remine_s | n_deletions | n_noop | n_safe_blocked |
|---|---|---|---|---|---|---|---|---|---|
| HFPriority | ok | 0.0 | 0.0 | 0.0 | 174.1 | 336.0 | 23474 | – | – |
| MCPriority_safeT | **timeout** | 1.0 | 0.0 | 0.0 | 7200.0 | 370.2 | 4388 | – | 0 |
| MCPriority_safeF | ok | 0.0 | 0.0 | 0.0 | 369.4 | 377.5 | 29304 | 0 | 0 |
| MSU-MAU | ok | 0.0 | 0.0 | 0.0 | 151.6 | 422.1 | 13027 | – | – |
| MSU-MIU | ok | 0.3 | 0.0 | 0.0 | 56.8 | 415.6 | 14515 | – | – |

*(n_noop cho MCPriority_safeT hiện là `1` trong result cũ — đã SỬA code: timeout ⇒ n_noop=null; xem §Fix.)*

## Gates (§6)
- **Logging đủ cột:** ✔ mọi cột §3 xuất hiện, không NaN; counter null đúng chỗ (chỉ MCPriority có n_noop/n_safe_blocked).
- **HFPriority HF=0:** ✔ (0.0).
- **MCPriority-safe MC=0:** ✔ (0.0 cả safeT lẫn safeF — KHÔNG có bug MC>0).
- **Grid map calib:** ✔ chainstore dùng đúng ξ=0.003, |S|=10, |~S|=254.
- **AC re-mine 1M-tx đo được:** ✔ ~336–422s/cell (khâu đắt nhất, như dự đoán prompt §5).
- **Determinism:** HF/MC/AC tái lập CHÍNH XÁC (MSU-MIU chạy lại HF=0.3 khớp). n_deletions lệch ±1
  (14515 vs 14514) do **float-sum theo thứ tự set phụ thuộc hash seed** ở biên round(ws,3). → đã fix
  (PYTHONHASHSEED=0). Metric báo cáo (HF/MC/AC) không đổi.

## PHÁT HIỆN KHOA HỌC (thật, không suy diễn)
**1. MSU-MIU HF=0.3 là HÀNH VI ĐÚNG (không phải bug).** Instrument xác nhận: cả 10 SFWI ĐỀU bị ẩn
NGAY khi xử lý (#hidden_at_processing=10), nhưng **3 SFWI bị LỘ LẠI** ở cuối
(`{1374316967, 1696716975, 1696739684}`). Cơ chế = Weight Transformation: MSU-MIU xóa item NHẸ ⇒
W_total TĂNG ⇒ ws của SFWI đã ẩn (ở giao dịch bị đụng khi xử lý SFWI sau) bị đẩy LẠI ≥ξ; baseline
duyệt mỗi SFWI ĐÚNG 1 LẦN (không while re-check) ⇒ không sửa lại ⇒ HF>0. MSU-MAU xóa item NẶNG ⇒
W_total GIẢM ⇒ không lộ lại ⇒ HF=0. **⇒ Tuyên bố "baseline luôn HF=0" chỉ đúng cho MAU, KHÔNG đúng
cho MIU** (golden nhỏ không lộ ra; dữ liệu thật lộ ra). Trung thực khi viết §V.

## ⚠️ HAI CHẶN RT — CẦN CONTROL QUYẾT (trước khi phóng 30 cell)
Gốc chung: `common.HidingDB.ws(X)` (frozen §4) = **O(|cover(X)|)** mỗi lần gọi; hiding gọi ws rất nhiều
lần. Chi phí bùng nổ khi cover lớn HOẶC khi Safe quét toàn ~S.

**(A) MCPriority_safeT KHÔNG kịp 2h trên dữ liệu lớn.** chainstore safeT **timeout**: chỉ 4388 deletion
trong 7200s (~1.6s/deletion) vs HFPriority 23474 deletion/174s (~0.007s). `Safe(v,t)` = full-check O(|~S|×cover)
mỗi candidate ⇒ chậm ~230×. HF=1.0 (chưa ẩn nổi SFWI nào), n_safe_blocked=0 (không bị veto, chỉ CHẬM).
⇒ safeT trên kosarak/bms-pos (cũng ~1M/515k tx) nhiều khả năng cũng timeout.

**(B) accident (mọi method) KHÔNG khả thi trong 2h.** ξ=0.751 cao × 340k dày ⇒ cover(SFWI)=258k–311k;
mỗi ws ≈0.77s; hiding cần hàng nghìn deletion ⇒ ≫2h (probe: 71 deletion/55s chỉ hạ ws 0.95→0.916).
⇒ 5 cell accident sẽ timeout.

**Không tự sửa `common.py` (frozen).** Lựa chọn cho control (chọn 1):
1. **Tối ưu `HidingDB.ws` sang incremental O(1)** (duy trì num(X)/W_total tăng dần) — cần unfreeze
   common.py + chạy lại G1/G2/G3/G5/G7 để bảo toàn đúng. Đây là cách gỡ CẢ (A) và (B) mà giữ ξ/S/~S.
2. **Chấp nhận timeout** cho các cell nặng (status=timeout ghi trung thực; §V báo "timeout tại 2h").
3. **Giảm phạm vi/ξ:** re-calibrate accident ξ thấp hơn (cover nhỏ); và/hoặc bỏ safeT trên dataset ≥500k.
→ Chờ control chốt. Coordinator đã sẵn sàng phóng ngay khi có quyết định (resume idempotent, skip cell đã xong).

## Fix đã áp (cho lần phóng sau; KHÔNG đụng hiding/metric/miner/calib)
- `PYTHONHASHSEED=0` (re-exec guard đầu coordinator) ⇒ float-sum tất định (counter reproducible).
- `n_noop = null` khi `status=timeout` (timeout ≠ no-op). Cell safeT cũ giữ nguyên (sẽ chạy lại khi
  control chốt chiến lược Safe).

## Chi phí tham chiếu (chainstore, để control ước lượng)
- load+build HidingDB 1M-tx ≈ 44s; AC re-mine 1M-tx ≈ 336–422s/cell.
- 4 cell "khả thi" (HFP/safeF/MAU/MIU) hiding 57–369s; safeT timeout 7200s.

## RESUME_CMD
```
# phóng toàn bộ 35 cell (SAU khi control duyệt + chốt chiến lược safeT/accident):
PYTHONHASHSEED=0 setsid nohup python3 coordinator/run_coordinator.py >/dev/null 2>&1 </dev/null & disown
pgrep -af run_coordinator ; ps -o ppid= -p $(pgrep -f run_coordinator|head -1)   # PPID=1
# 1 dataset: python3 coordinator/run_coordinator.py <ds>
```
