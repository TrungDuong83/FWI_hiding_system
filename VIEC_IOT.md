# VIEC_IOT.md — Sinh dataset IoT (MNC + RTVCQ) — **DỪNG: thiếu raw data**

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-07 · VM `hshfwup-run` (GIỮ SỐNG).
> **TRẠNG THÁI: DỪNG ở PRECONDITION 1 — raw CSV IoT KHÔNG có trên GitHub.** Script + cfg đã sẵn + đã fix
> scheme weight + verify trên synthetic. Chờ control chuyển raw data. Chưa sinh/verify/calibrate (thiếu data).

## 🛑 BLOCKER (cần control) — raw IoT CSV thiếu
`git pull` + `git fetch --all` xong. **KHÔNG có `datasets/iot_raw/`** (thư mục không tồn tại):
- Tìm toàn repo: không có `df_anonymized.csv[.gz]`, không có `rtvcq.csv` (chỉ `results/summary.csv`).
- `git log --all -- datasets/iot_raw/` = rỗng (không commit/branch nào chứa).
- Không gitignore chặn, không git-LFS. → Raw **chưa được push** (có thể quá lớn: MNC 737k dòng, RTVCQ 63k).

**Cần:** chuyển 2 file raw lên VM `~/FWI_hiding_system/datasets/iot_raw/` (vd `scp`, hoặc `gsutil cp` từ
GCS, hoặc push kèm LFS). Nếu `.gz`: sẽ `gunzip -k`. Sau khi có → tôi chạy tiếp SINH → VERIFY → CALIBRATE.

## ✅ Đã kiểm & sẵn sàng (precondition 2–3)
- **Script** `src/datautil/iot_discretize.py`: có mặt (control cấp). R1 cat→item, R2 cont→10 equal-width
  bins (range tính trên toàn file, bỏ ô na), R4 txn_key=None→mỗi dòng 1 giao dịch, R5 qty=1, R6 weight.
- **cfg** `src/datautil/cfg_mnc.json` + `cfg_rtvcq.json`: có mặt, **khớp CHÍNH XÁC §CFG inline** của handoff
  (MNC 7 cat + 10 cont = 17 feature; RTVCQ 6 cat + 2 cont; na Latitude/Longitude=["-1"]).

## ⚠️ Đã SỬA: scheme weight (precondition-3 pre-authorize) — báo control
7-dataset lưu weight **NGUYÊN [1,10]** trong file (vd `retail_weights.txt`: `1:5`,`2:7`); loader
`preprocess.load_weights(normalize=10)` chia /10 → [0.1,1.0]. `calibrate.py` gọi `normalize=10` cho MỌI
dataset.
- Script gốc `gen_weights` viết `randint(1,10)/10.0` = `0.1..1.0` vào file → loader /10 lần nữa = `0.01..0.10`
  (lệch scale ×10 so 7-dataset; và `use_fraction` freeze cũng lệch).
- **Fix (commit 01f2b95):** `gen_weights` → `randint(1,10)` (nguyên), file lưu `id:5` khớp retail. KHÔNG
  đụng 7-dataset/engine/loader. (ws bất biến scale nên FWI/calib không đổi về bản chất, nhưng biểu diễn +
  use_fraction nay khớp 7-dataset.)

## ✅ Verify script + fix trên synthetic (RTVCQ mini, 5 dòng, có 1 dòng Latitude/Longitude=-1)
```
rtvcqmini: 5 giao dịch, 21 item, 10 bins, seed=42
weights: 1:2 2:1 3:5 ... 10:10 ...   → NGUYÊN [1,10] ✓ (khớp scheme 7-dataset)
quantities: "3:1 4:1 8:1 ..."         → mọi qty=1 ✓, format khớp retail ✓
row=txn: 5 dòng CSV → 5 giao dịch ✓
-1 handling: dòng Lat/Long=-1 KHÔNG sinh item Latitude/Longitude ✓ (quantities dòng đó không có bin Lat/Long)
```

## Kế hoạch khi raw data về (chưa chạy — thiếu data)
1. `datasets/iot_raw/` + (nếu .gz) `gunzip -k`.
2. SINH: `python3 src/datautil/iot_discretize.py --csv datasets/iot_raw/rtvcq.csv --ds rtvcq --cfg
   src/datautil/cfg_rtvcq.json --out datasets/` ; tương tự `mnc`.
3. VERIFY: qty=1; weight nguyên [1,10]; không dòng rỗng; item∈quantities đều có weight; **-1 không lọt**
   (grep itemmap); #giao dịch≈#dòng CSV; #item (MNC ~150–180, RTVCQ ~vài chục); byte-format vs retail;
   **kiểm cột hằng số** (Location Status? Level?) → nếu hằng trên toàn file ⇒ báo control (KHÔNG tự bỏ cột).
4. CALIBRATE: `calibrate.py` cho mnc+rtvcq (#FWI∈[50,300], #SFWI top-10% clamp[10,40], ξ≤3dp) → freeze
   `calib_mnc.json`+`calib_rtvcq.json`. MNC 737k dòng: nếu mine >~20min → báo control.
5. Commit+push datasets/itemmaps/calib → cập nhật VIEC_IOT.md → DỪNG chờ control verify.

## RANH GIỚI (giữ)
KHÔNG stop VM (còn chạy 5 method IoT sau — RT một nguồn). KHÔNG đụng 7 dataset/engine/metric. KHÔNG bịa.
Van dừng đã kích hoạt: **thiếu raw data** → chờ control.

**DỪNG — cần control chuyển raw IoT CSV lên `datasets/iot_raw/`. Mọi thứ khác (script/cfg/scheme-fix) đã
sẵn + verify.**
