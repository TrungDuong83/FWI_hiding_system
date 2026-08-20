# REUSE_KIT — 01 DATASET  ★ FILE QUAN TRỌNG NHẤT

Bài mới **dùng lại đúng 7 dataset này**. Toàn bộ số liệu dưới đây được **tính trực tiếp
từ file dữ liệu thật** trên branch hiện tại (`datasets/*_quantities.txt`), không phải nhớ.

---

## 1. Danh sách dataset & file

Mỗi dataset gồm 2 file text định dạng **FIMI mở rộng**:
- `<ds>_quantities.txt` — mỗi dòng = 1 giao dịch, token `item:quantity` cách nhau bởi space.
  Ví dụ (bms-pos): `0:4 1:5 2:3 3:5 4:2 …`
- `<ds>_weights.txt` — mỗi dòng = `item:weight` (trọng số item, dùng cho utility). Ví dụ: `1:10`.

| Dataset | File transactions | File weights | Nguồn/loại |
|---|---|---|---|
| chess | `chess_fimi_quantities.txt` | `chess_fimi_weights.txt` | FIMI dense (UCI chess) |
| mushroom | `mushroom_quantities.txt` | `mushroom_weights.txt` | FIMI dense (UCI mushroom) |
| bms-pos | `bms-pos_quantities.txt` | `bms-pos_weights.txt` | Click-stream POS (sparse) — **đã làm sạch, xem §4** |
| retail | `retail_quantities.txt` | `retail_weights.txt` | Belgian retail (sparse) |
| chainstore | `chainstore_quantities.txt` | `chainstore_weights.txt` | Chain-store (sparse, lớn) |
| accident | `accident_quantities.txt` | `accident_weights.txt` | Traffic accident (dense, lớn) |
| kosarak | `kosarak_quantities.txt` | `kosarak_weights.txt` | Hungarian news click-stream (sparse, lớn) |

Ba dataset lớn còn có bản nén nguồn: `datasets/accident.zip`, `chainstore.zip`, `kosarak.zip`.

---

## 2. Thống kê mỗi dataset (ĐỌC TỪ FILE THẬT)

Tính bằng cách quét từng dòng `*_quantities.txt`: đếm giao dịch, tập item phân biệt (phần
trước dấu `:`), độ dài giao dịch, mật độ = avg_len / distinct_items.

| Dataset | #Giao dịch | #Item phân biệt | Độ dài TB | Độ dài max | Mật độ | File qty |
|---|---:|---:|---:|---:|---:|---:|
| chess | 3,196 | 75 | 37.00 | 37 | 49.33% | 0.6 MB |
| mushroom | 8,416 | 119 | 23.00 | 23 | 19.33% | 1.0 MB |
| accident | 340,183 | 468 | 33.81 | 51 | 7.22% | 59.3 MB |
| bms-pos | 515,596 | 1,657 | 6.53 | 164 | 0.39% | 17.9 MB |
| retail | 88,162 | 16,470 | 10.31 | 76 | 0.063% | 6.0 MB |
| kosarak | 990,002 | 41,270 | 8.10 | 2,498 | 0.020% | 48.9 MB |
| chainstore | 1,112,949 | 46,086 | 7.23 | 170 | 0.016% | 62.4 MB |

Đọc nhanh: **chess/mushroom/accident = dense** (mật độ cao, giao dịch dài đều), **retail/
kosarak/chainstore/bms-pos = sparse** (nhiều item, giao dịch ngắn). chess & mushroom có độ
dài cố định (37, 23) → dataset "horizontal" chuẩn để test thuật toán trên dữ liệu dày.

---

## 3. Calibration — ngưỡng ξ chuẩn per-dataset

Mỗi dataset chạy ở một **ngưỡng utility ξ (`min_wus_mining`)** riêng, chọn sao cho số
FWUP (Frequent Weighted Utility Patterns) khai thác được ở mức "vừa phải" để so sánh công
bằng. Giá trị ξ chuẩn + số pattern (đọc từ `MyResults/final_results.csv`, thật):

| Dataset | ξ chuẩn (config) | ξ dùng ở kết quả | #FWUP | #SFWUP |
|---|---:|---:|---:|---:|
| chess | 0.89 | 0.89 | 159 | 14 |
| mushroom | 0.40 | 0.40 | 325 | 30 |
| bms-pos | 0.05 | 0.05 | 57 | 10 |
| retail | 0.014 | 0.014 | 72 | 10 |
| accident | 0.75 | 0.75 | 82 | 10 |
| kosarak | 0.022 | 0.022 | 65 | 10 |
| chainstore | **0.007** (config) | **0.003** (final_results.csv) | 263 | 10 |

> ⚠️ **[CẦN NGƯỜI DÙNG XÁC NHẬN]** chainstore: `run_experiments.py::ExperimentManager`
> ghi `min_wus_mining = 0.007`, nhưng `final_results.csv` báo `xi = 0.003`. Hai nguồn lệch
> nhau — khi tái dùng cần chốt lại ξ chuẩn cho chainstore.

**Nguồn ξ**: `run_experiments.py` → `ExperimentManager.experiments[<ds>]["min_wus_mining"]`.

**Sweep độ nhạy** (branch `exp/sensitivity-hide-eval`): mỗi dataset còn được calib ở nhiều
bội số ×mult quanh ξ chuẩn (ví dụ chess ×0.4/0.6/0.8/1.0; kosarak ×0.8…×1.6), lưu ở
`calibration_results/all_xi/calib_<ds>_<mult>.json` (32 ô tổng). Mỗi file JSON chứa:
`dataset, multiplier, xi_value, n_fwups, n_sfwups, fwups[], sfwup_patterns[], below_design_floor, source`.
→ Bài mới có thể tái dùng đúng **cách chọn ξ theo bội số** này để làm biểu đồ sensitivity.

**Chạy lại calibration**: dùng script calib per-dataset (thế hệ mới nằm ở branch
`exp/sensitivity-hide-eval`, thư mục `tools/`). Nguyên tắc: nạp dataset → mine FWUP ở ξ ứng
với ×mult → đếm/đóng băng tập pattern → ghi JSON. **[CẦN NGƯỜI DÙNG XÁC NHẬN]** đường dẫn
script calib chính xác (không có mặt trên branch hiện tại).

---

## 4. Loader & format nội bộ (code đọc dataset)

Trong `run_experiments.py`:

- `load_transactions_from_file(path)` → `dict{ tid(int) : dict{ item(str) : qty(float/int) } }`.
  Đọc từng dòng, tách token theo space, mỗi token `item:qty`.
- `load_weights_from_file(path)` → `dict{ item(str) : weight(float) }`. Tách mỗi dòng theo
  `:` (hoặc `,`), lấy 2 phần `item`, `weight`.
- **Utility 1 giao dịch** (TU): `TU(t) = Σ_{i∈t} weight(i) · qty(i,t)` — công thức lõi dùng
  lại ở mọi metric utility (DUS/IUS). Xem `02_INFRASTRUCTURE.md`.

**Quirk cần biết:**
- Item là **string key** (không cast int) — giữ nguyên khi so khớp pattern.
- Weights file có item **không xuất hiện** trong transactions và ngược lại → luôn dùng
  `weights.get(i, 0.0)` (default 0) để không KeyError.
- Dataset lớn (chainstore 62 MB, accident 59 MB, kosarak 49 MB): nạp vào RAM dạng dict →
  cần máy ≥ 8–16 GB. Không có streaming; toàn bộ DB giữ trong bộ nhớ.

### bms-pos — lỗi số liệu đã sửa (QUAN TRỌNG khi tái dùng)
- Bản gốc thô (`BMS-POS.csv` / `bms-pos.txt`, header lỗi) **KHÔNG** được code đọc trực tiếp.
- Pipeline làm sạch: `tools/bmspos_normalize_csv_to_fimi.py` (chuẩn hóa CSV→FIMI) +
  `tools/bmspos_generate_iu_eu.py` (sinh quantity/weight uniform[1,10]) → tạo ra
  `bms-pos_quantities.txt` + `bms-pos_weights.txt` **SẠCH**.
- Bản sạch: **515,596 giao dịch**, 1,657 item. Đây là bản đúng để dùng lại.
- Hai script pipeline nằm ở branch `fix/bms-pos-data` (không có trên branch hiện tại).
  Chỉ cần khi muốn tái tạo lại từ đầu; nếu chỉ dùng dữ liệu thì 2 file `.txt` sạch là đủ.

---

## 5. Dataset dùng cho mục đích gì

| Dataset | So sánh chính | Sensitivity (quét ξ) | Stress / dày | Ghi chú |
|---|:---:|:---:|:---:|---|
| chess | ✓ | ✓ | ✓ (dense) | Nhanh (~0.3s mine), test nóng |
| mushroom | ✓ | ✓ | ✓ (dense) | Nhanh (~1.5s), dense vừa |
| retail | ✓ | ✓ | | Sparse vừa, ~9s |
| chainstore | ✓ | | | Sparse rất lớn, mine ~114s |
| accident | ✓ | ✓ | ✓ (dense lớn) | Dense + lớn → tốn RAM/CPU |
| kosarak | ✓ | ✓ | | Sparse lớn, giao dịch max 2,498 item |
| bms-pos | ✓ | ✓ | | Sparse lớn, ξ=0.05, mine ~31 phút bản gốc |

> Bảng mục đích tổng hợp từ config (thứ tự chạy fast→slow) + comment mining-time trong
> `run_experiments.py`. Cột "So sánh chính" = mọi dataset đều dùng cho bảng so sánh method.
