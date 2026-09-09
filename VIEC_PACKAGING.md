# VIEC_PACKAGING.md — Doc hygiene + đóng gói exp→main

> exp/v5-sectionV · VM hshfwup-run · 2026-09-09. (A) doc hygiene trên exp; (B) squash exp→main + verify.
> Số từ file thật / calib, không bịa. VERIFY sau mỗi thao tác git.

## A1. Đặc trưng 9 dataset (recompute TỪ FILE THẬT — `coordinator/ds_features.py`)

| Dataset | #Giao dịch | #Item | Độ dài TB | max | Mật độ | ξ (calib) | #FWI | #SFWI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| chess_fimi | 3,196 | 75 | 37.00 | 37 | 49.33% | 0.920 | 293 | 28 |
| mushroom | **8,416** | 119 | 23.00 | 23 | 19.33% | 0.457 | 299 | 28 |
| accident | 340,183 | 468 | 33.81 | 51 | 7.22% | 0.751 | 299 | 28 |
| bms-pos | 515,596 | 1,657 | 6.53 | 164 | 0.39% | 0.021 | 276 | 21 |
| retail | 88,162 | 16,470 | 10.31 | 76 | 0.063% | 0.008 | 241 | 14 |
| kosarak | 990,002 | 41,270 | 8.10 | 2,498 | 0.020% | 0.011 | 263 | 22 |
| chainstore | 1,112,949 | 46,086 | 7.23 | 170 | 0.016% | 0.003 | 264 | 10 |
| mnc (IoT) | 736,974 | 96 | 14.00 | 14 | 14.58% | 0.204 | 297 | 27 |
| rtvcq (IoT) | 63,336 | 76 | 7.25 | 8 | 9.54% | 0.057 | 295 | 26 |

- **ξ/#FWI/#SFWI khớp CHÍNH XÁC 9 file `calib_<ds>.json`** (đối chiếu trước khi ghi — 0 lệch).
- ⚠️ **mushroom = 8,416** (đếm thật từ file, = số mọi thí nghiệm + calib + G6 đã dùng). FIMI "chuẩn"
  thường 8,124 → **lệch 292 dòng**. Kết quả nội bộ nhất quán trên 8,416. **Báo control:** giữ 8,416
  (dữ liệu đã chạy) hay điều tra nguồn 292 dòng thừa? (KHÔNG tự đổi — van dừng mushroom.)

## A3. Phân phối weight 7-dataset (giải Blocker B2: bài ghi "normal")

Histogram `*_weights.txt` (int 1–10, %/giá trị):
```
chess_fimi  n=75   mean=5.36 | 1:10.7 2:14.7 3:8.0 4:10.7 5:5.3 6:6.7 7:14.7 8:9.3 9:14.7 10:5.3
mushroom    n=119  mean=4.96 | 1:14.3 2:7.6 3:10.9 4:16.8 5:6.7 6:12.6 7:10.9 8:8.4 9:4.2 10:7.6
accident    n=468  mean=5.40 | 1:9.4 2:11.5 3:11.1 4:9.2 5:12.0 6:8.5 7:10.3 8:8.3 9:9.0 10:10.7
retail      n=16470 mean=5.47 | 1:9.9 2:10.1 3:10.3 4:10.4 5:10.1 6:9.9 7:9.7 8:9.8 9:10.3 10:9.5
bms-pos     n=1657 mean=5.44 | 1:10.4 2:9.7 3:10.6 4:10.8 5:11.1 6:9.3 7:9.0 8:8.4 9:10.3 10:10.5
kosarak     n=41270 mean=5.50 | ~10.0 mỗi giá trị (9.7–10.3)
chainstore  n=46086 mean=5.49 | ~10.0 mỗi giá trị (9.8–10.3)
```

**VERDICT: UNIFORM** (mỗi giá trị 1–10 ≈ 10%, mean ≈ 5.4–5.5 = uniform mean 5.5). Dataset lớn (retail/
kosarak/chainstore/bms-pos/accident) phẳng rõ; chess/mushroom nhiễu hơn chỉ do n nhỏ (75/119), vẫn quanh
uniform. → Scheme thật = **uniform int[1,10] / 10**. **KHÔNG phải normal.**
- **Hệ quả:** IoT sinh weight uniform ⇒ **nhất quán** với 7 FIMI ✓ (KHÔNG cần regenerate weight IoT).
- **Writing:** sửa mô tả bài "normal" → **"uniform[1,10]/10"**.

## A1/A2. Thay đổi doc
- **`docs/REUSE_KIT/01_DATASET.md`** viết lại (regime FWI):
  - §0 mới: `tw=Σw/|T|`, `ws=Σtw/W_total`, FWI ⟺ ws≥ξ (bỏ TU=Σw·qty / DUS / IUS).
  - §1: mô tả weight = item-weight int[1,10]/10 (không "external utility"); thêm 2 dòng IoT (mnc, rtvcq)
    + đoạn discretize R1–R6.
  - §2: thêm 2 hàng IoT; giữ 7 hàng FIMI (số đã đúng); note mushroom 8,416 vs 8,124.
  - §3: thay bảng ξ utility cũ (0.89/0.40/… #FWUP) bằng **ξ FWI 9 dataset** (từ calib); bỏ note
    "chainstore 0.007 vs 0.003" (chốt 0.003); bỏ các "[CẦN NGƯỜI DÙNG XÁC NHẬN]" đã resolve.
  - §4: loader FWI (bỏ qty, /10), tw/ws ở common/metrics (ws≥ξ không round3).
  - §5: thêm IoT; note weight uniform (không normal).
- **`src/datautil/cfg_mnc.json`**: đã có `_note` (6 cat + 8 cont) — control đã thêm, không sửa thêm.

## B. Squash exp→main + verify
(điền sau khi thực thi — xem §B-RESULT cuối file + báo cáo chat)

### Inventory verify (trên exp = nội dung main sau squash-additive)
- `results/`: **245 result JSON** + `summary.csv` **245 dòng** ✓
- `calibration/`: **9 calib_*.json** (7 FIMI + mnc + rtvcq) + `sweep_grid.json` + `sweep_grid_iot.json` ✓
- `datasets/`: **9** `*_quantities.txt` (7 FIMI + mnc + rtvcq) + weights ✓ (iot_raw gitignore — raw đã ở main)
- `src/`: 9 module (hiding/metrics/mining/datautil) ✓
- docs: 01_DATASET (mới), CLAUDE.md, SPEC_PART4… giữ nguyên ✓

## B-RESULT
(cập nhật sau squash: `git diff exp main` rỗng? main ahead 0? commit hash main)
