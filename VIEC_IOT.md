# VIEC_IOT.md — Sinh dataset IoT (RTVCQ ✅ + MNC ⚠️ chặn cột hằng)

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-07 · VM `hshfwup-run`
> (us-central1-a, GIỮ SỐNG). Raw kéo từ `origin/main` (trích blob ra working tree, KHÔNG merge main;
> `datasets/iot_raw/` đã gitignore). **RTVCQ hoàn chỉnh (sinh+verify+calibrate). MNC DỪNG: cột hằng
> `Location Status` → chờ control.**

## Nguồn raw (từ origin/main:datasets/iot_raw/)
| dataset | file raw | kích thước | #dòng data |
|---|---|---|---|
| RTVCQ | `CallVoiceQualityExperience-2018-April.csv` | 3.75 MB | 63,336 |
| MNC | `df_anonymized.csv.gz` → `df_anonymized.csv` | 13.4MB → 134.8MB | 736,974 |

*(URL gốc: lấy từ manifest control upload — tôi không có manifest, chỉ có 2 file trên. RTVCQ = "Call
Voice Quality Experience" (open telecom, 2018-April). MNC = df_anonymized. Điền URL khi control cấp.)*

## Feature giữ (theo cfg control — khớp §CFG)
- **RTVCQ (8 feature):** cat[Operator, Indoor_Outdoor_Travelling, Network Type, Rating, Call Drop
  Category, State Name] + cont[Latitude, Longitude]. na: Lat/Long=["-1"].
- **MNC (17/33 feature):** cat[Network Operator, Network Type, Band, Roaming, Location Status, Mobile
  Status, Level] + cont[RSRP/RSRQ/RSSI/SNR/CQI/ASU Level LTE, Latitude, Longitude, Downstream/Upstream
  Bandwidth]. na: Lat/Long=["-1"]. (16 cột raw khác bỏ theo cfg.)

## Fix đã áp (precondition-3, commit 01f2b95): weight scheme
`gen_weights` → **int [1,10]** (khớp 7-dataset; loader `normalize=10` → [0.1,1.0]). Script gốc viết
`/10.0` gây lệch scale ×10 + phá `use_fraction`. Verify: weight file `id:5` khớp `retail_weights.txt`.

---

## ✅ RTVCQ — HOÀN CHỈNH
**Sinh:** 63,336 giao dịch (=#dòng, row=txn), **76 item**, qty=1, weight int[1,10], seed=42, 10 bins.
**Verify (verify_iot.py) — TẤT CẢ PASS:**
- qty=1 ✓; không dòng rỗng ✓; weight int[1,10] ✓ (distinct 1..10); mọi quantity-item có weight ✓;
  mọi weight-item ∈ itemmap ✓; avg-len=7.25 (min5/max8).
- **row=txn:** 63,336 = 63,336 ✓.
- **-1 KHÔNG lọt** ✓: Latitude valid=47,676 / na(-1)=15,660 → txn có item Latitude = **47,676** (đúng =
  #valid; 15,660 dòng -1 sinh 0 item). Longitude tương tự.
- **Không cột hằng số** ✓.
- Format khớp `retail_quantities.txt` (`id:1`) ✓.

**Calibrate:** ξ=**0.057** · #FWI=**295** (∈[50,300]) · #candidate=265 · #SFWI=**26** (∈[10,40]) · freeze
`calib_rtvcq.json` (41s). SFWI |X|≥2 hợp lệ. → **committed+pushed (c038d07).**

---

## ⚠️ MNC — DỪNG (cột hằng số) — cần control quyết
**Sinh:** 736,974 giao dịch (=#dòng), **106 item** (handoff ước ~150–180 → thực 106), qty=1, weight
int[1,10]. **Files `datasets/mnc_*` đang provisional (untracked), CHƯA commit** (chờ quyết cfg).

**Verify:** qty=1 ✓; weight int[1,10] ✓; coverage ✓; row=txn 736,974=736,974 ✓; MNC không có -1 ở
Lat/Long (valid=736,974, na=0) ✓.

**🛑 BLOCKER — cột HẰNG SỐ (van dừng handoff, KHÔNG tự sửa cfg):**
- **`Location Status` = 1 giá trị duy nhất (`True`) trên CẢ 736,974 giao dịch** → item `Location
  Status=True` có mặt MỌI giao dịch ⇒ vô dụng (vào mọi FWI, không phân biệt). Đúng ví dụ handoff nêu.
- Hệ quả: avg-len = **17 cố định** (mọi feature luôn có mặt, không missing) → nếu bỏ Location Status còn
  16/txn, 105 item.

**Phân bố item/feature MNC (17 feature):**
```
RSRP/RSRQ/RSSI/SNR/CQI/ASU LTE: 10 mỗi cột   Band/Downstream/Upstream: 7   Longitude: 8
Level: 5   Network Type: 3   Network Operator/Mobile Status/Roaming/Latitude: 2   Location Status: 1  ← HẰNG
```

**Ghi chú chất lượng (không phải blocker, để control cân nhắc):**
- **Latitude chỉ 2 bin** (bin0, bin9) — equal-width bins gộp phần lớn giá trị về 2 cực (có thể do outlier
  kéo range). Longitude 8 bin (ok). Control cân nhắc có giữ Latitude không.
- #item 106 thấp hơn ước handoff (150–180) — do cardinality thực (nhiều cột LTE chỉ 10 bin, categorical 2–7).

**→ CẦN CONTROL QUYẾT (KHÔNG tự sửa cfg):**
1. **Bỏ `Location Status` khỏi `cfg_mnc.json`** (cột hằng vô dụng) → tôi regenerate MNC → verify → calibrate.
2. (Tùy) xử Latitude 2-bin?
Sau khi control chốt → tôi chạy tiếp MNC (regenerate nếu đổi cfg) → calibrate → commit.

---

## Trạng thái repo
- Committed+pushed (c038d07): `datasets/rtvcq_*`, `calib_rtvcq.json`, `calibrate.py` (+rtvcq,mnc entries),
  `verify_iot.py`, `.gitignore` (iot_raw).
- Untracked provisional: `datasets/mnc_*` (chờ quyết cfg — nếu bỏ Location Status sẽ regenerate).
- Raw `datasets/iot_raw/` gitignore (không commit vào exp/v5-sectionV; đã có trên main).
- VM `hshfwup-run` **GIỮ SỐNG** (còn chạy 5 method IoT sau). Không đụng 7 dataset/engine/metric.

## RESUME (sau khi control quyết MNC)
```bash
cd ~/FWI_hiding_system && source .venv/bin/activate
# nếu control bỏ Location Status: sửa cfg_mnc.json (control) rồi:
python3 src/datautil/iot_discretize.py --csv datasets/iot_raw/df_anonymized.csv --ds mnc --cfg src/datautil/cfg_mnc.json --out datasets/
python3 coordinator/verify_iot.py mnc datasets/iot_raw/df_anonymized.csv src/datautil/cfg_mnc.json
python3 calibration/calibrate.py mnc     # nếu mine >~20min → báo control
```

**DỪNG — RTVCQ xong (ξ=0.057/#FWI295/#SFWI26). MNC chờ control quyết cột hằng `Location Status`.**
