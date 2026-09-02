# SPEC — Calibration ξ + chọn SFWI (execution chạy trên VM) — FWI paper IoT-63257-2026

> Control chốt RULE; execution chạy sweep per-dataset. ξ cũ (utility+qty regime) KHÔNG tái dùng.
> Áp cho 7 dataset hiện có (chess_fimi, mushroom, accident, retail, bms-pos, kosarak, chainstore).
> IoT (Q7) hoãn — thực nghiệm bổ sung sau.

## RULE (đã chốt)
1. **Định nghĩa FWI mới:** `tw=Σw/|T|` (không qty), weight /10, `ws=Σtw/W_total`, FWI ⟺ `ws≥ξ`.
2. **#FWI mục tiêu ∈ [50, 300]** mỗi dataset (so sánh được; khớp dải HSHFWUPs Table 8 57–325).
   Sweep ξ (giảm dần từ điểm tham khảo), chọn ξ nhỏ nhất cho #FWI vào dải. **ξ lưu ≤ 3 dp.**
3. **Chọn SFWI (cơ chế HSHFWUPs — đã publish, defensible):**
   - Lọc candidate: `|X| ≥ 2` (cấm singleton, C5.2) ∧ `ws > ξ`.
   - **Overlap score(X)** = độ phổ biến item của X trong không gian NSFWI (NSCov-based).
   - Xếp giảm theo overlap score → lấy **top 10%**, **min 10, max 40** → S.
   - Deterministic (seed=42) cho tie; ghi rule rõ để tái lập (E6).
4. **Oracle maxlen>7:** khi ξ thấp, chạy miner không cap để chắc không rớt FWI dài >7; nếu có → nâng
   cap hoặc ghi giới hạn trong bài (cap mặc định `MAX_PATTERN_LENGTH=7`).
5. **Backend:** calibration = `Fraction` (exact); ngưỡng dùng `ws≥ξ` chính xác khi freeze.

## OUTPUT (freeze, phải push)
`calibration/calib_<ds>.json` = `{ dataset, xi (≤3dp), n_fwi, n_sfwi, fwi[], sfwi[] }`.
Đóng băng để mọi cell §V (5 cột) dùng CÙNG S/~S/ξ.

## VERIFY
- #FWI ∈ [50,300]; #SFWI = clamp(round(0.1·#FWI_candidate), 10, 40).
- Mọi SFWI có `|X|≥2` và `ws>ξ`.
- Oracle maxlen>7: 0 FWI dài bị rớt (hoặc ghi nhận rõ).
- Tái chạy calibrate 2 lần → cùng ξ + cùng S (determinism).
