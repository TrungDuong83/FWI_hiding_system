# REUSE_KIT — 00 INDEX

Bộ khung chuẩn trích xuất từ repo `Hiding_SFWUP` để mang sang **repo bài báo MỚI**
(cùng lĩnh vực utility/weighted pattern mining, **dùng lại dataset**, nhưng
thuật toán & đóng góp KHÁC).

- Phân loại: **[TÁI DÙNG]** = mang sang được nguyên/gần nguyên; **[ĐẶC THÙ BÀI CŨ]** =
  gắn với đóng góp thuật toán của luận văn cũ, KHÔNG mang sang; **[RÁC]** = log/cache/
  tạm, bỏ.
- Số liệu dataset trong kit này được **đọc & tính từ file dữ liệu thật** (xem `01_DATASET.md`),
  không phải nhớ áng chừng.
- Ghi chú môi trường: kit này được soạn trên branch `claude/review-hiding-system-ZxMay`
  (một ảnh chụp CŨ hơn của repo). Một số thành phần "thế hệ mới" (coordinator GĐ1
  `tools/run_compare_xistd.py`, `tools/run_sensitivity_full.py`, `calibration_results/all_xi/…`)
  **nằm trên branch `exp/sensitivity-hide-eval`** — được mô tả theo nội dung đã đọc thực tế
  ở các phiên trước, và được đánh dấu rõ nguồn branch. Chỗ nào không kiểm chứng được trên
  branch hiện tại → ghi **[CẦN NGƯỜI DÙNG XÁC NHẬN]**.

---

## Bảng phân loại tổng

| Thành phần | Loại | Mô tả 1 dòng |
|---|---|---|
| `datasets/*_quantities.txt`, `*_weights.txt` | **[TÁI DÙNG]** | 7 dataset FIMI đã chuẩn hóa (transaction+quantity, item weight) — đầu vào bài mới |
| `datasets/*.zip` (accident/chainstore/kosarak) | **[TÁI DÙNG]** | Bản nén nguồn của 3 dataset lớn |
| Thống kê dataset (số txn/item/mật độ) | **[TÁI DÙNG]** | Xem `01_DATASET.md` — tính từ file thật |
| Loader `load_transactions_from_file` / `load_weights_from_file` (`run_experiments.py`) | **[TÁI DÙNG]** | Đọc format `item:qty` / `item:weight` → dict nội bộ |
| Calibration (ξ chuẩn per-dataset + sweep ×0.4…×1.6) | **[TÁI DÙNG]** | Cách chọn ngưỡng ξ để có số pattern hợp lý; giá trị ξ chuẩn ở `01_DATASET.md` |
| `calibration_results/all_xi/calib_*.json` | **[TÁI DÙNG]** | 32 ô calib (7 tập × các ×mult) — *trên branch `exp/sensitivity-hide-eval`* |
| Metric evaluator `SanitizedDBEvaluator.comprehensive_evaluation` | **[TÁI DÙNG]** (một phần) | HF đặc thù bài ẩn; MC/AC/IUS/DUS/TMR/DDI là metric utility-mining tổng quát — xem `02_INFRASTRUCTURE.md` |
| Coordinator pattern (chạy tuần tự + checkpoint + resume + push) | **[TÁI DÙNG]** | `tools/run_all_batteries.py` (branch này) / `tools/run_compare_xistd.py` (exp) làm mẫu |
| Watchdog auto-restart (`tools/*watchdog*.sh`, `monitor_and_intervene.sh`) | **[TÁI DÙNG]** | Khởi động lại coordinator khi crash; sống sót VM recycle |
| Scheme kết quả (`*_results/`, CSV tổng hợp, per-cell JSON) | **[TÁI DÙNG]** | Cấu trúc thư mục + đặt tên file kết quả |
| `.gitignore` (log/cache/lock) | **[TÁI DÙNG]** | Chuẩn bỏ log runtime, giữ checkpoint dữ liệu — xem `03_REPO_STRUCTURE.md` |
| `run_experiments.py::ExperimentManager` (config per-dataset) | **[TÁI DÙNG]** (khung) | Bảng config tên file + ξ mining; **bỏ** phần gọi thuật toán ẩn |
| **RISWU** measure (Relative Impact Score on Weighted Utility) | **[ĐẶC THÙ BÀI CŨ]** | Đo chọn victim item — đóng góp lõi luận văn cũ |
| **SWM** allocation mechanism (`_apply_swm_to_hide`) | **[ĐẶC THÙ BÀI CŨ]** | Cơ chế giảm utility để ẩn pattern |
| Chiến lược **SDIF / Max-RISWU / Min-RISWU** | **[ĐẶC THÙ BÀI CŨ]** | 3 chiến lược ẩn của bài cũ |
| **Sub-Algorithm 3.4** (HandleDeadlockEscalation, Tier1/Tier2) | **[ĐẶC THÙ BÀI CŨ]** | Bộ phá deadlock khi ẩn |
| Baselines **SMSE_adapted / MSU-MIU_adapted** | **[ĐẶC THÙ BÀI CŨ]** (bản adapt) | Thuật toán baseline literature, đã "adapt" cho bài toán ẩn cũ |
| `MyResults/final_results.csv`, `compare_xistd.csv`, kết quả GĐ1/GĐ2, sensitivity/stress CSV | **[ĐẶC THÙ BÀI CŨ]** | Số liệu kết quả của bài cũ — KHÔNG mang sang |
| `MyResults/sfwups_*.json` (frozen SFWUP) | **[ĐẶC THÙ BÀI CŨ]** | Tập pattern "nhạy cảm" chọn theo tiêu chí bài cũ |
| `submission/`, `*.ipynb`, `README.md` (mục Contributions) | **[ĐẶC THÙ BÀI CŨ]** | Gói nộp + notebook + mô tả đóng góp luận văn cũ |
| `MyLogs/*.log`, `tools/*.log`, `*.lock`, `MyResults/fwups_cache_*.json`, `__pycache__/` | **[RÁC]** | Log runtime, cache mining, lock — regenerate được |
| `_sfwup_core.py`, `source_code.zip`, `Hiding_SFWUP_source_code.zip` | **[RÁC]** / [CẦN NGƯỜI DÙNG XÁC NHẬN] | Bản đóng gói/ẩn của code cũ |

---

## Các file trong REUSE_KIT

| File | Nội dung |
|---|---|
| `00_INDEX.md` | (file này) mục lục + phân loại tổng |
| `01_DATASET.md` | **Quan trọng nhất** — dataset, thống kê thật, calibration, loader, quirk (bms-pos) |
| `02_INFRASTRUCTURE.md` | Coordinator/checkpoint/resume, metric framework, scheme kết quả, môi trường |
| `03_REPO_STRUCTURE.md` | Cây thư mục đề xuất cho repo mới + `.gitignore` chuẩn + mục README |
| `04_DONT_REUSE.md` | Danh sách KHÔNG mang sang + lý do (tránh lẫn logic bài cũ) |
