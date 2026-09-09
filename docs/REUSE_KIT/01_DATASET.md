# REUSE_KIT — 01 DATASET  ★ FILE QUAN TRỌNG NHẤT (regime FWI, 9 dataset)

> Bài **FWI hiding** (Frequent Weighted Itemset). Mọi số dưới đây **tính trực tiếp từ file thật**
> (`datasets/*_quantities.txt`) và **ξ/#FWI/#SFWI lấy từ `calibration/calib_<ds>.json` đã freeze** —
> không nhớ, không bịa. Regime = **weighted support** (KHÔNG utility). 9 dataset = 7 FIMI + 2 IoT.

---

## 0. Regime FWI (định nghĩa lõi — KHÁC bản utility cũ)

- **Transaction weight:** `tw(T) = ( Σ_{i∈T} w(i) ) / |T|` — trung bình cộng item-weight, **KHÔNG nhân
  quantity**. Quantity trong file (`item:qty`) **bị bỏ qua** (Fix A của engine).
- **W_total = Σ_T tw(T)** trên toàn bộ giao dịch.
- **Weighted support:** `ws(X) = ( Σ_{T⊇X} tw(T) ) / W_total`.
- **FWI:** X là FWI ⟺ **`ws(X) ≥ ξ`** (membership float64 trực tiếp, không round3).
- SFWI (S) = itemset nhạy cảm cần ẩn; NSFWI (~S) = FWI \ S.
- (Bài KHÔNG dùng TU=Σw·qty, KHÔNG DUS/IUS/utility — đó là dự án cũ.)

---

## 1. Danh sách dataset & file (9 dataset)

Mỗi dataset gồm 2 file text định dạng **FIMI mở rộng**:
- `<ds>_quantities.txt` — mỗi dòng = 1 giao dịch, token `item:qty` cách nhau space (qty bị bỏ qua ở FWI).
- `<ds>_weights.txt` — mỗi dòng `item:weight`, **weight = số nguyên [1,10]**; loader `load_weights(normalize=10)`
  chia /10 → [0.1,1.0] ("item weight", KHÔNG phải external utility).

| Dataset | File | Nguồn/loại |
|---|---|---|
| chess_fimi | `chess_fimi_*` | FIMI dense (UCI chess) |
| mushroom | `mushroom_*` | FIMI dense (UCI mushroom) |
| bms-pos | `bms-pos_*` | Click-stream POS (sparse) — đã làm sạch, xem §4 |
| retail | `retail_*` | Belgian retail (sparse) |
| chainstore | `chainstore_*` | Chain-store (sparse, lớn) |
| accident | `accident_*` | Traffic accident (dense, lớn) |
| kosarak | `kosarak_*` | Hungarian news click-stream (sparse, lớn) |
| **mnc** (IoT) | `mnc_*` | **Mobile Network Coverage** (DIB, DOI 10.1016/j.dib.2024.111146) — discretize 14/33 feature |
| **rtvcq** (IoT) | `rtvcq_*` | **Voice Call Quality Experience** (TRAI/Kaggle, "Call Voice Quality Experience 2018-April") — discretize |

**2 dataset IoT** sinh từ CSV thô (`datasets/iot_raw/`) qua `src/datautil/iot_discretize.py` (rule R1–R6):
categorical→item; continuous→10 equal-width bins→item; **row = 1 giao dịch** (txn_key=null); qty=1;
weight **uniform int[1,10]** (cùng scheme 7 FIMI). MNC bỏ cột **hằng** (Location Status) + **non-discriminative**
(Latitude bin9=100%, Downstream Bandwidth bin0=99.48% — rule bin ≥99%) → 14 feature (6 cat + 8 cont).
RTVCQ: 6 cat + 2 cont (Latitude/Longitude), na `-1` loại (không sinh item).

---

## 2. Thống kê mỗi dataset (ĐỌC TỪ FILE THẬT — `coordinator/ds_features.py`)

Quét `*_quantities.txt`: #giao dịch (dòng không rỗng), #item phân biệt, độ dài, mật độ = avg_len/#item.

| Dataset | #Giao dịch | #Item | Độ dài TB | Độ dài max | Mật độ |
|---|---:|---:|---:|---:|---:|
| chess_fimi | 3,196 | 75 | 37.00 | 37 | 49.33% |
| mushroom | 8,416 | 119 | 23.00 | 23 | 19.33% |
| accident | 340,183 | 468 | 33.81 | 51 | 7.22% |
| bms-pos | 515,596 | 1,657 | 6.53 | 164 | 0.39% |
| retail | 88,162 | 16,470 | 10.31 | 76 | 0.063% |
| kosarak | 990,002 | 41,270 | 8.10 | 2,498 | 0.020% |
| chainstore | 1,112,949 | 46,086 | 7.23 | 170 | 0.016% |
| **mnc** (IoT) | 736,974 | 96 | 14.00 | 14 | 14.58% |
| **rtvcq** (IoT) | 63,336 | 76 | 7.25 | 8 | 9.54% |

Đọc nhanh: **dense** (mật độ cao, dài đều) = chess/mushroom/accident/mnc; **sparse** = retail/kosarak/
chainstore/bms-pos/rtvcq. chess/mushroom/mnc/rtvcq có độ dài (gần) cố định (37/23/14/7–8) do horizontal/
discretize. MNC lặp cao: 736,974 dòng nhưng chỉ 204,338 (Model, Current Date Time) phân biệt (~72% trùng;
txn_key=null ⇒ giữ nguyên row=txn).

> ⚠️ **mushroom = 8,416 giao dịch = 8,124 item-set phân biệt + 292 record lặp item-set** (chỉ khác
> quantity — FWI bỏ qua). Giữ 8,416 (row=transaction, đồng nhất mọi dataset như MNC giữ giao dịch trùng);
> 8,124 = số item-set distinct, khớp mushroom FIMI chuẩn. Không dedup.

---

## 3. Calibration — ngưỡng ξ FWI per-dataset (từ `calib_<ds>.json` đã freeze)

Mỗi dataset calib để **50 ≤ #FWI ≤ 300**; **#SFWI = clamp(round(0.1·#candidate), 10, 40)** theo overlap-score
(top-10%, |X|≥2 ∧ ws>ξ); ξ ≤ 3 chữ số thập phân. Backend freeze = `Fraction` (exact).

| Dataset | ξ (FWI) | #FWI | #SFWI |
|---|---:|---:|---:|
| chess_fimi | 0.920 | 293 | 28 |
| mushroom | 0.457 | 299 | 28 |
| accident | 0.751 | 299 | 28 |
| retail | 0.008 | 241 | 14 |
| bms-pos | 0.021 | 276 | 21 |
| kosarak | 0.011 | 263 | 22 |
| chainstore | 0.003 | 264 | 10 |
| **mnc** (IoT) | 0.204 | 297 | 27 |
| **rtvcq** (IoT) | 0.057 | 295 | 26 |

(Số khớp CHÍNH XÁC 9 file `calib_<ds>.json`. chainstore ξ = **0.003** — đã chốt, KHÔNG còn "0.007 vs 0.003".)

**Sensitivity sweep:** mỗi dataset còn calib ở bội số `mult ∈ {0.4,0.6,0.8,1.0,1.2,1.4,1.6}` quanh ξ
(`ξ(mult)=round3(mult·ξ)`), feasibility grid ở `calibration/sweep_grid.json` (7 FIMI) + `sweep_grid_iot.json`
(mnc, rtvcq). Điểm `feasible=ok` được chạy sweep (chainstore loại khỏi sweep do round3 collapse). Chi tiết
đường cong: `results/summary.csv` (245 cell = 45 main + 140 sweep-7 + 60 sweep-IoT).

**Chạy lại calibration:** `python3 calibration/calibrate.py [<ds>...]` (nạp dataset → mine FWI ở ξ → freeze
JSON). IoT: sinh dataset trước bằng `iot_discretize.py`.

---

## 4. Loader & format nội bộ (code đọc dataset)

`src/datautil/preprocess.py`:
- `load_transactions(path)` → `dict{ tid : set(item) }`. Đọc token `item:qty`, **bỏ qty** (FWI dùng
  `tw=Σw/|T|`, không quantity). Item giữ dạng **string**.
- `load_weights(path, normalize=10, use_fraction=False)` → `dict{ item : w/10 }`. Weight file là **số
  nguyên [1,10]** ⇒ /10 → [0.1,1.0] (exact với `Fraction`). `use_fraction=True` cho golden/calibration.
- **tw / ws** (regime FWI, §0) cài ở `src/hiding/common.py::HidingDB` (num_cache incremental) + membership
  `ws≥ξ` ở `src/metrics/metrics.py::is_frequent` (float64, **không round3**).

**Quirk:** item = string key (không cast int khi so pattern); weight dùng `W.get(i,0)` (item thiếu weight
→ 0); dataset lớn (chainstore 62MB, accident 59MB, kosarak 49MB, mnc 135MB) nạp full RAM → cần ≥16GB
(máy chạy: GCP c2-standard-16, 64GB).

### bms-pos — đã làm sạch (khi tái dùng)
Bản gốc thô header lỗi KHÔNG đọc trực tiếp. Đã chuẩn hóa CSV→FIMI + sinh qty/weight uniform[1,10] →
`bms-pos_{quantities,weights}.txt` sạch: **515,596 giao dịch, 1,657 item**. Hai file `.txt` sạch là đủ để dùng.

---

## 5. Dataset dùng cho mục đích gì

| Dataset | So sánh main | Sweep | Dày/stress | Ghi chú |
|---|:---:|:---:|:---:|---|
| chess_fimi | ✓ | ✓ | ✓ | Nhanh, dense, ξ cao (0.92) |
| mushroom | ✓ | ✓ | ✓ | Dense vừa |
| retail | ✓ | ✓ | | Sparse vừa |
| chainstore | ✓ | (loại sweep) | | Sparse rất lớn; round3 collapse ở ξ nhỏ |
| accident | ✓ | ✓ | ✓ | Dense + lớn; baseline nghi timeout |
| kosarak | ✓ | ✓ | | Sparse lớn, txn max 2,498 item |
| bms-pos | ✓ | ✓ | | Sparse lớn |
| **mnc** (IoT) | ✓ | ✓ | ✓ | Dense/lặp; baseline MSU-MAU + MCP-safe (ξ thấp) nghi timeout 2h |
| **rtvcq** (IoT) | ✓ | ✓ | | Nhẹ, không timeout |

> **Weight scheme (cả 9 dataset) = uniform int[1,10] → /10** (xác nhận bằng histogram, xem
> `VIEC_PACKAGING.md` §A3). Bài cũ mô tả "normal" là SAI — thực nghiệm dùng **uniform**. IoT sinh uniform
> ⇒ nhất quán với 7 FIMI.
