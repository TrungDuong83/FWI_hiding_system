# VIEC_SWEEP_GRID.md — PHA 1a: Feasibility grid cho SENSITIVITY SWEEP (mine + đếm)

> Repo `TrungDuong83/FWI_hiding_system` · branch `exp/v5-sectionV` · 2026-09-04.
> Chỉ MINE + ĐẾM + chọn S (đúng cơ chế operating). **KHÔNG hiding, KHÔNG RT, KHÔNG 5 method.**
> Output: `calibration/sweep_grid.json` (49 điểm) + file này. **Gates G-SW1..4 = PASS.** DỪNG chờ control.

## Cơ chế (tái dùng, KHÔNG sửa logic operating)
- `calibration/sweep_grid.py` import trực tiếp `calibrate.py` → dùng nguyên `mine_fwi` / `freeze` /
  `select_sfwi` / loaders. Cùng code đã freeze `calib_<ds>.json`. Chỉ THÊM sweep_grid + verify_sweep.
- Lưới 7 ds × mult∈{0.4,0.6,0.8,1.0,1.2,1.4,1.6}. `ξ(mult)=round(mult·ξ_chuẩn,3)` (≤3dp), ξ_chuẩn=`xi`
  trong calib (=mult 1.0). S re-derive riêng mỗi điểm (FWI đổi theo ξ). Backend freeze/select=Fraction exact.
- Phân loại: **ceiling** ξ≥1.0 (≥max_ws) hoặc #FWI<10 ; **floor** mine>1200s (SIGALRM=20min) hoặc worker
  OOM-kill ; monotonic: #FWI tăng khi ξ giảm ⇒ floor 1 điểm ⇒ mọi mult thấp hơn floor. **ok** = còn lại.
- Hạ tầng chịu-nổ: 1 worker subprocess/dataset (load 1 lần), checkpoint mỗi điểm, resume skip. Worker
  OOM → orchestrator (process nhẹ tách biệt) sống, đánh floor điểm dở + thấp hơn. Chạy nền: `setsid nohup`.

## GRID 7×7 (nf=#FWI, nc=#candidate, ns=#SFWI, t=mine_time_s)

Ký hiệu: **OK** = ok · **CE** = ceiling · **FL** = floor.

| dataset (ξ_chuẩn) | 0.4 | 0.6 | 0.8 | **1.0** | 1.2 | 1.4 | 1.6 |
|---|---|---|---|---|---|---|---|
| **chess_fimi** (0.92) | **FL** ξ.368 OOM | OK ξ.552 nf517719 ns40 t209 | OK ξ.736 nf24958 ns40 t14 | **OK** ξ.92 nf293 ns28 t0.3 | CE ξ1.104 | CE ξ1.288 | CE ξ1.472 |
| **mushroom** (0.457) | OK ξ.183 nf57415 ns40 t6 | OK ξ.274 nf4653 ns40 t2 | OK ξ.366 nf1099 ns40 t1 | **OK** ξ.457 nf299 ns28 t0.5 | OK ξ.548 nf99 ns10 | OK ξ.64 nf41 ns10 | OK ξ.731 nf31 ns10 |
| **retail** (0.008) | OK ξ.003 nf1359 ns40 t113 | OK ξ.005 nf567 ns35 t29 | OK ξ.006 nf406 ns24 t17 | **OK** ξ.008 nf241 ns14 t7 | OK ξ.01 nf154 ns10 | OK ξ.011 nf139 ns10 | OK ξ.013 nf106 ns10 |
| **accident** (0.751) | **FL** ξ.3 (monotonic) | **FL** ξ.451 timeout1200s | OK ξ.601 nf2129 ns40 t629 | **OK** ξ.751 nf299 ns28 t116 | OK ξ.901 nf31 ns10 t17 | CE ξ1.051 | CE ξ1.202 |
| **bms-pos** (0.021) | OK ξ.008 nf1597 ns40 t307 | OK ξ.013 nf637 ns40 t160 | OK ξ.017 nf413 ns33 t113 | **OK** ξ.021 nf276 ns21 t78 | OK ξ.025 nf181 ns13 | OK ξ.029 nf144 ns10 | OK ξ.034 nf102 ns10 |
| **kosarak** (0.011) | OK ξ.004 nf2009 ns40 t337 | OK ξ.007 nf625 ns40 t102 | OK ξ.009 nf381 ns33 t62 | **OK** ξ.011 nf263 ns22 t47 | OK ξ.013 nf201 ns16 | OK ξ.015 nf162 ns13 | OK ξ.018 nf125 ns10 |
| **chainstore** (0.003) | **FL** ξ.001 timeout1200s | OK ξ.002 nf463 ns10 t651 | OK ξ.002 nf463 ns10 t652 | **OK** ξ.003 nf264 ns10 t285 | OK ξ.004 nf187 ns6 | OK ξ.004 nf187 ns6 | OK ξ.005 nf133 ns1 |

**#điểm ok mỗi dataset:** chess=3 · mushroom=7 · retail=7 · accident=3 · bms-pos=7 · kosarak=7 · chainstore=6
→ **Σ ok = 40** (ceiling=5, floor=4, tổng 49 = 7×7).

## GATES (đều PASS — số từ output thật)
- **G-SW1** (mult=1.0 khớp `calib_<ds>.json` đã freeze): PASS 7/7 — xi/n_fwi/n_sfwi/n_candidate khớp
  CHÍNH XÁC mọi dataset (vd accident 299/285/28, chainstore 264/13/10).
- **G-SW2** (điểm ok: n_sfwi=clamp(round(0.1·n_cand),10,40) capped n_cand): PASS. |X|≥2∧ws>ξ đảm bảo
  do tái dùng `select_sfwi`/`freeze` (cùng code G-C2 đã verify).
- **G-SW3** (phân loại ceiling/floor/ok đúng định nghĩa): PASS toàn bộ 49 điểm.
- **G-SW4** (determinism, re-mine 2×): PASS — mushroom mult1.2 nf=99==99, chess mult0.8 nf=24958==24958,
  khớp giá trị đã lưu.

## QUAN SÁT (cho control — KHÔNG tự quyết)

1. **floor thật (trần/sàn kỹ thuật, không cắt "cho đẹp"):**
   - `chess_fimi mult=0.4` (ξ=0.368): worker OOM-kill (exit=-9) — nổ bộ nhớ >62GB khi mine/freeze
     (mult=0.6 đã 517,719 FWI). Monotonic ⇒ floor.
   - `accident mult=0.6` (ξ=0.451): mine >1200s (timeout 20min). `mult=0.4` floor monotonic.
   - `chainstore mult=0.4` (ξ=0.001): mine >1200s (timeout 20min).
2. **ceiling:** chess 1.2/1.4/1.6 và accident 1.4/1.6 có ξ(mult)≥1.0>max_ws ⇒ 0 pattern (đúng ví dụ
   handoff "chess mult>1.0").
3. **ok nhưng #FWI KHỔNG LỒ (nặng cho hiding PHA 1b — control cân nhắc tỉa):**
   - `chess_fimi 0.6`: **517,719 FWI** (ns=40). `mushroom 0.4`: 57,415 FWI. `chess 0.8`: 24,958.
   Về mine thì "ok" (<20min), nhưng hiding + AC re-mine trên #FWI cỡ này sẽ RẤT nặng / nghi timeout.
4. **Collapse ξ do làm tròn 3dp ở dataset ξ_chuẩn nhỏ (độ phân giải sweep kém):**
   - `chainstore`: mult 1.2 & 1.4 đều ξ=0.004 (trùng, nf=187 ns=6); mult 0.6 & 0.8 đều ξ=0.002 (trùng,
     nf=463 ns=10). ξ phân biệt thực chỉ {0.005,0.004,0.003,0.002,0.001}. `mult 1.6` ns=1 (S suy biến).
   → Đường cong sweep chainstore gần như phẳng/trùng điểm; control cân nhắc bỏ chainstore khỏi sweep
     hoặc dùng lưới mult khác. **Đề xuất, KHÔNG tự quyết.**
5. **Ghi chú kỹ thuật (defensibility):** SIGALRM 1200s trong worker chỉ bọc `mine_fwi`, chưa bọc
   `freeze`+`select`. Trong run này KHÔNG gây treo: điểm nổ hoặc OOM (bị bắt→floor) hoặc hoàn tất với số
   thật (G-SW3 PASS xác nhận mọi floor là timeout/OOM, mọi ok có số thật). Cho PHA 1b nên bọc timeout
   cả điểm. Không ảnh hưởng tính đúng phân loại ở đây.

## ƯỚC TÍNH TẢI PHA 1b (thô — cần smoke RT để chốt, KHÔNG bịa số)

**Số cell (chính xác):**
- `Σ ok × 5 method = 40 × 5 = **200 cell**`. Trong đó cột mult=1.0 (7 ds × 5) = **35 = MAIN**;
  còn **165** cell là SWEEP bổ sung (33 điểm ok ngoài mult=1.0 × 5). *(Lưu ý: 35 main đã nằm trong 200,
  không cộng chồng.)*

**AC re-mine (bám số mine_time_s ĐO THẬT — re-mine DB đã tẩy ≈ mine gốc cùng ξ):**
- Σ mine_time_s trên 40 điểm ok = **4,631 s ≈ 1.29 h/lượt mine**. Mỗi cell tẩy 1 DB → re-mine 1 lần:
  `≈ 5 method × 1.29 h ≈ **6.4 h**` (cận trên; DB đã xóa item → thường ≤ mine gốc).
- *(Nếu dùng anchor phẳng ~400s/cell của handoff: 200×400/3600 ≈ 22 h — ước cao hơn; số đo-thật 6.4h
  đáng tin hơn vì bám mine_time thực, nhưng phân bố lệch: chainstore/accident/bms-pos/kosarak/chess-0.6
  chiếm hầu hết; chess/mushroom rẻ.)*

**RT hiding (metric đầu bài) — KHÔNG chốt được trước smoke:**
- Anchor operating có sẵn chênh **~180×** giữa dataset: accident MCP-safe ≈ **2,730 s/cell** (~0.76h,
  |D|=340k, dense) vs chainstore MCP-safe ≈ **5.4 s/cell** (|D|=1.1M nhưng thưa). Không thể ngoại suy 1
  con số tổng tin cậy từ 2 anchor. Ước thô toàn cục: **~40–100h+** (rất không chắc), do nhiều cell dense
  nghi chạm cap 2h.
- **Cell NGHI TIMEOUT 2h (ưu tiên smoke trước khi phóng):**
  - `accident 0.8` (ξ=0.601, ns=40, nf=2129) — mọi method, **nhất là baseline MSU-MAU/MIU** (không
    Safe/no-op, xóa tới ws<ξ ⇒ nặng nhất trên accident dense). Operating accident đã 2730s; dày hơn →
    dễ vượt 2h.
  - `chess_fimi 0.6` (517,719 FWI) — mọi method (số membership-check khổng lồ mỗi lần xóa).
  - `chainstore 0.6/0.8`, `kosarak 0.4`, `bms-pos 0.4` — |D| lớn + ns=40, RT hiding chưa biết.

**Dòng tóm tắt:**
`SWEEP GRID: chess_fimi=3/7 mushroom=7/7 retail=7/7 accident=3/7 bms-pos=7/7 kosarak=7/7 chainstore=6/7`
`| est_cells=200 (35 main + 165 sweep) | est_hours≈40–100h hiding (thô, cần smoke) | est_AC_remine_h≈6.4h (đo-thật) / ~22h (anchor phẳng)`

## CẦN CONTROL QUYẾT (van dừng — KHÔNG tự quyết)
1. **Tỉa điểm/dataset?** — bỏ chess 0.6 (517k FWI) & mushroom 0.4 (57k)? bỏ chainstore khỏi sweep (ξ
   collapse)? giữ nguyên 40 ok?
2. **AC re-mine cho sweep hay chỉ main?** (chi phí thêm ≈ 6.4h nếu full).
3. **Smoke RT PHA 1b trên cell nghi-timeout** (accident 0.8, chess 0.6, chainstore 0.6/0.8) trước khi
   phóng nền — xác nhận deadline 2h/cap.
4. Sau khi control duyệt → phát spec PHA 1b (full run MAIN+SWEEP 5 method) → mới phóng.

## RESUME / TÁI TẠO
```bash
cd ~/FWI_hiding_system && source .venv/bin/activate
python3 calibration/sweep_grid.py       # resume idempotent (skip điểm đã có trong sweep_grid.json)
python3 calibration/verify_sweep.py     # G-SW2/3/4
```
Artefact mang về control: `calibration/sweep_grid.json` + file này.

**PHA 1a XONG — chờ control.** Không hiding, không RT, không 5 method. 4 gate PASS.
