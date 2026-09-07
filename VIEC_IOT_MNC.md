# VIEC_IOT_MNC.md — MNC hoàn chỉnh (bỏ cột hằng + non-discriminative) → calibrate

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-07 · VM `hshfwup-run` (GIỮ SỐNG).
> Raw `df_anonymized.csv` (736,974 dòng) từ `origin/main:datasets/iot_raw/`. **MNC generate+verify+calibrate
> XONG.** DỪNG chờ control.

## Feature cuối: 14 (6 categorical + 8 continuous)
**Giữ:**
- cat (6): Network Operator, Network Type, Band, Roaming, Mobile Status, Level.
- cont (8): RSRP LTE, RSRQ LTE, RSSI LTE, SNR LTE, CQI LTE, ASU Level LTE, Longitude, Upstream Bandwidth.

**BỎ (3 cột) — theo control:**
| cột bỏ | lý do | bằng chứng |
|---|---|---|
| Location Status | cột HẰNG (control chốt bỏ) | 1 value `True` trên cả 736,974 giao dịch |
| Latitude | non-discriminative (rule ≥99%) | bin9 = **1.0000** (100% giao dịch 1 bin) |
| Downstream Bandwidth | non-discriminative (rule ≥99%) | bin0 = **0.9948** (99.48%) |

## RULE non-discriminative (control) — tỉ lệ bin đã kiểm (mọi cột continuous)
Bin nào ≥99% #giao dịch ⇒ bỏ cột. Sau khi bỏ, re-check: **mọi cột giữ đều <99%** ✓.
| cột | #bin | max_bin_ratio | quyết định |
|---|---|---|---|
| RSRP LTE | 10 | 0.2588 | giữ |
| RSRQ LTE | 10 | 0.2698 | giữ |
| RSSI LTE | 10 | 0.2200 | giữ |
| SNR LTE | 10 | 0.3530 | giữ |
| CQI LTE | 10 | 0.3023 | giữ |
| ASU Level LTE | 10 | 0.2472 | giữ |
| Longitude | 8 | 0.7191 | giữ |
| Upstream Bandwidth | 7 | 0.9633 | giữ (96.33% <99%) |
| ~~Latitude~~ | 2 | **1.0000** | **BỎ** |
| ~~Downstream Bandwidth~~ | 7 | **0.9948** | **BỎ** |

## Output + VERIFY (verify_iot.py — PASS)
- **736,974 giao dịch** (=#dòng CSV, row=txn) · **96 item** · avg-len = **14 cố định** (14 feature, không missing).
- qty=1 ✓ · weight int[1,10] ✓ · mọi quantity-item có weight ✓ · không dòng rỗng ✓.
- **Không cột hằng số** ✓ (Location Status đã bỏ). -1 không lọt (MNC không có -1) ✓.
- Format khớp `retail_*.txt` (`id:1`) ✓.

## CALIBRATE (y hệt 7 dataset)
- ξ = **0.204** · #FWI = **297** (∈[50,300]) · #candidate = 271 · #SFWI = **27** (∈[10,40], top-10% clamp).
- SFWI |X|≥2 ✓. Freeze exact → `calib_mnc.json`.
- **Mine time:** max 1 mine = **119s** (ξ=0.204) — **<20min** ✓ (không cần báo control theo van dừng).

## Số dòng trùng (control yêu cầu)
- Khóa (Model, Current Date Time): **736,974 dòng → 204,338 distinct → 532,636 dòng trùng (72.1%)**.
- txn_key=null (control) ⇒ **row=txn, KHÔNG dedup** → DB có nhiều giao dịch lặp (weighted support phản
  ánh lặp). Ghi nguyên; nếu control muốn dedup theo khóa này → cần đổi cfg `txn_key` + regenerate (chờ quyết).

## ⚠️ DIVERGENCE cfg_mnc.json (đã resolve — báo control để đối chiếu)
Trong lúc tôi chạy, control push commit `2a10d16` với `cfg_mnc.json` = **6 cat + 10 cont** (chỉ bỏ Location
Status, GIỮ Latitude + Downstream Bandwidth). Bản của tôi (đang dùng) = **6 cat + 8 cont** (bỏ thêm
Latitude + Downstream BW **theo đúng RULE #2 control giao trong handoff này**).
- Tôi **merge, giữ bản 8-cont** (rule-correct; MNC dataset/calib dựa trên nó). `iot_discretize.py` lấy bản
  control (giống hệt chức năng: weight int[1,10]).
- **Nếu control CHỦ Ý giữ 10 cont** (ghi đè rule, giữ Latitude 100% + Downstream 99.48%) → báo tôi, tôi
  regenerate MNC + recalibrate. Mặc định tôi theo rule (8 cont).

## Trạng thái repo
- committed+pushed (b76c7b5): `datasets/mnc_*`, `calib_mnc.json`, `cfg_mnc.json` (8 cont), `analyze_bins.py`.
- Branch synced (ahead 0). VM GIỮ SỐNG. Không đụng 7 dataset/RTVCQ/engine/metric. Không tiến trình chạy.

## Tổng IoT (2 dataset)
| ds | #txn | #item | avg-len | ξ | #FWI | #SFWI |
|---|---|---|---|---|---|---|
| rtvcq | 63,336 | 76 | 7.25 | 0.057 | 295 | 26 |
| mnc | 736,974 | 96 | 14.0 | 0.204 | 297 | 27 |

**DỪNG — MNC + RTVCQ đã sinh/verify/calibrate. Chờ control verify (đặc biệt: cfg divergence 8-vs-10 cont;
dup 72%). Sau đó → handoff chạy 5 method IoT trên cùng VM.**
