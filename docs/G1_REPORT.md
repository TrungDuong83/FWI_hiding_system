# G1_REPORT — Verify nền hiding (common / select_victim / preprocess)

> Gate G1: cấu trúc dữ liệu + Score + preprocess khớp CHÍNH XÁC running example (SPEC §6, CLAUDE §B.6).
> Backend Fraction (exact) cho phần golden; engine float64 chỉ dùng cho check /10-invariance.
> Mọi số là output THẬT của `python3 tests/test_g1.py` (exit 0 = PASS).

## Thành phần verify
- `src/hiding/common.py` — `HidingDB`: tw / ws / cover / **delete** (chỗ DUY NHẤT sửa DB: D, inv,
  tw_cache, W_total — Bẫy #1).
- `src/hiding/select_victim.py` — `score_hfp`, `score_mcp` (precompute per-item), `select_victim`
  (two-stage, tie-break id numeric), `sensitive_items_of`.
- `src/datautil/preprocess.py` — loader (bỏ qty), `load_weights` (/10, tùy chọn Fraction),
  `validate_sfwi` (cấm singleton), `validate_weights` (warn w≤0 / thiếu weight).

## Kết quả chạy (real)
```
[wtotal/ws] W_total=16/5 (exp 16/5) ok=True ; ws(AC)=3/4 (exp 3/4) ok=True
[fwi_count] #9 match=True diff=set()
[score_hfp] { A:9/10, B:0, C:7/5, D:0, E:1/5 } ok=True
[score_mcp] { A:1/4, B:1, C:1/4, D:1/5, E:1/2 } ok=True
[select_victim] victim(T3=ACD, HFP) = C (exp C) ok=True
[delete] inv/D ok=True ; W_total match fresh ok=True ; ws(AC) 3/4 -> 219/379 (exp 219/379) val_ok=True strict_dec=True
[preprocess] /10-invariant FWI ok=True ; validate_sfwi(singleton) raises=True ; validate_weights warns ok=True

G1 PASS - wtotal/ws=OK, fwi_count=OK, scores=OK, delete=OK, preprocess=OK
```

## Đối chiếu target (SPEC §6)
| Kiểm | Kỳ vọng | Kết quả | OK |
|---|---|---|---|
| `W_total` | 16/5 | 16/5 | ✓ |
| `ws(AC)` | 3/4 | 3/4 | ✓ |
| #FWI(0.55) qua `HidingDB.ws` | 9 `{A,C,D,E,AC,AD,CD,CE,ACD}` | 9, diff=∅ | ✓ |
| ScoreHFP | A=9/10,B=0,C=7/5,D=0,E=1/5 | khớp | ✓ |
| ScoreMCP | A=1/4,B=1,C=1/4,D=1/5,E=1/2 | khớp | ✓ |
| `select_victim(T3=ACD, HFP)` | C (max ScoreHFP) | C | ✓ |
| `delete(C,T1)` → inv/D | T1∉inv[C], C∉D[T1] | đúng | ✓ |
| `delete` → W_total | khớp recompute-from-scratch (Bẫy #1) | khớp | ✓ |
| `delete(C∈AC,T1)` → ws(AC) | giảm ngặt (A1); = 219/379 (≈0.5778) | 3/4→219/379, strict | ✓ |
| preprocess /10 | FWI(W)==FWI(W/10) tại ξ | khớp, #=9 | ✓ |
| `validate_sfwi` singleton | raise ValueError | raise | ✓ |
| `validate_weights` w≤0 / thiếu | cảnh báo | có | ✓ |

## Ghi chú
- `ws(AC)` sau `delete(C,T1)`: 219/379 = 0.57783… — trùng số A1 (0.75→0.5778) và trùng giá trị
  tính tay `(73/40) / (16/5 − 23/40 + tw(ADE))`, xác nhận `delete` cập nhật **W_total mới** đúng.
- Engine (float64) chỉ dùng cho check /10-invariance; phần exact hoàn toàn qua `HidingDB` (Fraction).
- CHƯA có thuật toán hiding (HFPriority/MCPriority) — đó là Đợt B. G1 chỉ khóa nền.

**VERDICT G1: PASS.**

## Tái lập
```
python3 tests/test_g1.py     # exit 0 = PASS
```
