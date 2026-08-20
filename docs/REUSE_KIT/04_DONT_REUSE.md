# REUSE_KIT — 04 DON'T REUSE

Danh sách **KHÔNG mang sang** repo mới, kèm lý do. Mục tiêu: tránh lẫn logic/kết quả của
luận văn cũ (bài toán "ẩn SFWUP") vào đóng góp thuật toán MỚI. Bài mới **chỉ** thừa kế
dataset + hạ tầng (xem `01_`, `02_`, `03_`).

---

## A. Thuật toán & đóng góp lõi của bài cũ — TUYỆT ĐỐI KHÔNG

| Thành phần | Ở đâu | Vì sao KHÔNG mang |
|---|---|---|
| **RISWU** (Relative Impact Score on Weighted Utility) | `run_experiments.py` (đo chọn victim) | Đóng góp đo lường LÕI của luận văn cũ — mang sang = trùng đóng góp, mất tính mới |
| **SWM** allocation mechanism `_apply_swm_to_hide()` | `run_experiments.py::HidingManager` | Cơ chế giảm utility để ẩn pattern — đặc thù bài toán hiding cũ |
| **SDIF / Max-RISWU / Min-RISWU** (3 chiến lược ẩn) | `run_experiments.py::StrategyComparator` | Là "method" của bài cũ; bài mới có method riêng |
| **Sub-Algorithm 3.4** HandleDeadlockEscalation (Tier1 xóa phẫu thuật / Tier2 xóa batch) | `run_experiments.py` | Bộ phá deadlock khi ẩn — chỉ có nghĩa trong quy trình ẩn cũ |
| **Baselines SMSE_adapted / MSU-MIU_adapted** (bản đã "adapt") | `run_experiments.py::BaselineSMSE/BaselineMSUMIU` | Thuật toán baseline literature nhưng đã **adapt cho bài toán ẩn cũ**; nếu bài mới cần baseline thì adapt LẠI từ gốc literature cho bài toán MỚI, đừng bê bản adapt cũ |
| Khái niệm **SFWUP / "sensitive pattern"** + cách chọn | `MyResults/sfwups_*.json`, `sfwup_selection` config | Định nghĩa "nhạy cảm" theo tiêu chí bài ẩn cũ; bài mới có định nghĩa đối tượng riêng |
| Metric **HF** (Hiding Failure) | `SanitizedDBEvaluator` | Chỉ có nghĩa khi mục tiêu là "ẩn". Bỏ hoặc định nghĩa lại. (MC/AC/DUS/IUS/TMR/DDI thì tái dùng được — xem `02`.) |

---

## B. Kết quả & số liệu bài cũ — KHÔNG (sẽ gây nhầm là kết quả bài mới)

| Thành phần | Vì sao KHÔNG mang |
|---|---|
| `MyResults/final_results.csv` / `.xlsx` | Bảng kết quả chính của bài cũ (7 tập × 3 chiến lược cũ) |
| `compare_xistd_results/compare_xistd.csv` + `result_*.json` | Kết quả GĐ1 (bảng so sánh ξ chuẩn) của bài cũ |
| Kết quả **GĐ1 / GĐ2** (sensitivity, so sánh method cũ) | Toàn bộ là số của thuật toán cũ |
| `MyResults/escalation_stats.csv`, `stress_test_subalg34.csv`, `stress_test_evidence.md` | Bằng chứng cho Sub-Alg 3.4 (đặc thù bài cũ) |
| `MyResults/results_*_<timestamp>.txt` | Log kết quả chạy cũ |
| `calibration_results/*` **giá trị pattern đóng băng** | ξ chuẩn (số) tái dùng được như tham khảo, nhưng **tập FWUP/SFWUP đóng băng** gắn định nghĩa bài cũ → re-mine lại cho bài mới, đừng bê `sfwup_patterns[]` |

> Lưu ý sắc thái: **giá trị ξ chuẩn** (chess 0.89, mushroom 0.40, …) là *tham số dataset* →
> tham khảo được. Nhưng **danh sách pattern** trong file calib/sfwups là *đầu ra thuật toán
> cũ* → không tái dùng như kết quả.

---

## C. Kế hoạch / tài liệu / gói nộp bài cũ — KHÔNG

| Thành phần | Vì sao KHÔNG mang |
|---|---|
| `submission/` (gói tái lập của luận văn) | Đóng gói nộp của bài cũ |
| `*.ipynb` (`Hiding_SFWUP_experiment.ipynb`, `sfwup_hiding_system_v5_11.ipynb`, …) | Notebook chạy thuật toán cũ |
| `README.md` mục "Key Contributions" | Mô tả đóng góp bài cũ — viết README mới (xem `03` §3) |
| `PROMPT_CLAUDE_CODE_BASELINE.md`, `CODEBASE_MAP.md` | Tài liệu điều phối/bản đồ code bài cũ |
| Mọi "plan"/"section export" của bài cũ | Nội dung viết bài của luận văn cũ |
| `generate_final_results.py`, `make_notebook.py`, `run_stress_test.py`, `test_baselines.py` | Script sinh kết quả/notebook/stress của bài cũ |

---

## D. Rác (không mang, mà cũng nên `.gitignore` ở repo mới)

`MyLogs/*.log`, `tools/*.log`, `*.lock`, `MyResults/fwups_cache_*.json`, `__pycache__/`,
`_sfwup_core.py`, `source_code.zip`, `Hiding_SFWUP_source_code.zip`.
> `_sfwup_core.py` / các `*.zip` code: **[CẦN NGƯỜI DÙNG XÁC NHẬN]** — là bản đóng gói/ẩn
> của source cũ; gần như chắc chắn không mang sang.

---

## Ranh giới 1 dòng để nhớ

> **Mang sang**: dataset (sạch) + loader + metric utility tổng quát (MC/AC/DUS/IUS/TMR/DDI)
> + khung coordinator/checkpoint/resume/watchdog + scheme kết quả + giá trị ξ chuẩn.
> **KHÔNG mang**: mọi thứ có tên RISWU / SWM / SDIF / Sub-Alg 3.4 / HF / SFWUP-đóng-băng,
> và mọi CSV/số liệu/notebook/plan kết quả của bài cũ.
