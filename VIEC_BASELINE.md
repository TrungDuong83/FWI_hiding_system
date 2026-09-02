# VIEC_BASELINE — baseline_ppum (MSU-MAU + MSU-MIU), verify golden

> Deliverable: `src/hiding/baseline_ppum.py` + `tests/test_baseline_golden.py`.
> Faithful SPEC_BASELINE.md §3 (port Alg 1/2 EAAI 2016 sang tw/ws, chỉ xóa item). Verify `Fraction`.
> Mọi số dưới đây là output THẬT của `python3 tests/test_baseline_golden.py` (2 vòng sạch liên tiếp).
> KHÔNG git, KHÔNG §V — chỉ implement + verify.

## Trace golden (running example ξ=0.55, S={AC,CE})
| Method | victim | trace | HF | MC (lost) | AC | W_total 3.2 → |
|---|---|---|---|---|---|---|
| MSU-MAU (động, max w) | AC:A, CE:C | `A@T3 → C@T1` | 0 | 4/7 `{A,AD,CD,ACD}` | 0 | 367/120 ≈ **3.058 ↓** |
| MSU-MIU (tĩnh, min w) | AC:C, CE:E | `C@T3 → E@T1` | 0 | 2/7 `{CD,ACD}` | 0 | 399/120 ≈ **3.325 ↑** |

Khớp CHÍNH XÁC SPEC_BASELINE §5 (kể cả chiều dịch W_total: MAU heavy→↓ regime AC; MIU light→↑ regime MC).

## Output thật (7 gates)
```
[G-B1 MAU] trace=A@T3 -> C@T1 HF=0 MC=4/7 lost=['A', 'ACD', 'AD', 'CD'] AC=0 ok=True
[G-B1 MIU] trace=C@T3 -> E@T1 HF=0 MC=2/7 lost=['ACD', 'CD'] AC=0 ok=True
G-B1 PASS
[G-B2] MAU=['A@T3', 'C@T1'] MIU=['C@T3', 'E@T1'] | HFP=['C@T3', 'C@T1'] MCP_T=['E@T1', 'C@T2', 'C@T4'] MCP_F=['E@T1', 'E@T2', 'A@T3'] ok=True
G-B2 PASS
[G-B3] MAU=['A@T1', 'A@T2'] (2 xóa, txn2=T2) MIU=['B@T1'] (1 xóa, không txn2) khác=True ok=True
G-B3 PASS
[G-B4] v*max before={'AC': 'A', 'CE': 'C'} after={'AC': 'A', 'CE': 'C'} inv=True ; v*min={'AC': 'C', 'CE': 'E'} ; order|SCov|=['AC', 'CE'] order_dbfreq=['CE', 'AC'] victim_f_indep=True
G-B4 PASS
[G-B5 run_msu_mau] HF=0 (exp 0) items_removed=2==2=len(trace) pure_item_delete=True
[G-B5 run_msu_miu] HF=0 (exp 0) items_removed=2==2=len(trace) pure_item_delete=True
[G-B5] no Safe/no-op import: True
G-B5 PASS
[G-B6] metric funcs from 'metrics'=True ; AC=0 == |phantom|/|FWI(san)|=0/3=0 ok=True
G-B6 PASS
[G-B7 run_msu_mau] run1==run2 = True
[G-B7 run_msu_miu] run1==run2 = True
G-B7 PASS

BASELINE gates = 7/7 : G-B1=OK, G-B2=OK, G-B3=OK, G-B4=OK, G-B5=OK, G-B6=OK, G-B7=OK
```
2 vòng sạch liên tiếp (chạy lại từ clean): cả hai đều `gates = 7/7`.

## Từng gate
| Gate | Nội dung | Kết quả |
|---|---|---|
| G-B1 | Golden trace exact + HF/MC/AC (Fraction) | PASS — MAU `A@T3→C@T1`, MIU `C@T3→E@T1` |
| G-B2 | Non-collapse ≠ HFP/MCP(safe=T/F) | PASS — 4 trace đôi một khác |
| G-B3 | Động vs tĩnh (fixture ≥2 xóa) | PASS — MAU 2 lần (txn2=T2), MIU 1 lần (không txn2) |
| G-B4 | Invariance victim + độc lập f | PASS — v* bất biến qua giao dịch; đổi f đổi thứ tự (|SCov|→[AC,CE] vs DB-freq→[CE,AC]) nhưng victim mỗi X không đổi |
| G-B5 | Fairness (no Safe/no-op, no quantity) | PASS — không import Safe; HF=0; Σ\|D\| giảm đúng len(trace) ⇒ thuần xóa item |
| G-B6 | Metric parity (dùng chung metrics; AC denom=\|FWI(san)\|) | PASS — 3 hàm `__module__=='metrics'`; AC=0=0/3 |
| G-B7 | Deterministic | PASS — 2 lần y hệt |

## Ghi chú trung thực (theo SPEC_BASELINE §5 "HAI CẢNH BÁO")
- **Golden KHÔNG chứng minh contrast AC** — cả 4 method AC=0 (DB 5-item quá đặc). Contrast là empirical
  (chess/mushroom/IoT). Golden xác nhận cơ chế qua chiều W_total: MAU heavy→↓ (regime AC), MIU light→↑
  (regime MC) — cặp bracket 2 failure-mode qua Weight Transformation.
- **Bất đối xứng động/tĩnh trong FWI item-deletion:** xóa `v*∈X` luôn làm `T*` rời `cover(X)` và chỉ
  đổi `tw(T*)`; tw các giao dịch còn lại bất biến ⇒ "re-max động" (MAU) và "sort tĩnh" (MIU) cho **cùng
  thứ tự transaction khi victim item giống nhau**. Khác biệt quan sát được MAU vs MIU đến từ **item nặng
  vs nhẹ** (quỹ đạo ws khác ⇒ số lần xóa khác — G-B3 minh họa). Cấu trúc động/tĩnh vẫn giữ **đúng bản
  gốc Alg 1/2** dù ở regime này không đổi output cho cùng victim; đây là ghi chú, không phải sai lệch.
- **Baseline không yếu tầm thường** — golden MIU MC(2/7) < HFPriority MC(3/7). Mạnh/yếu là empirical,
  KHÔNG kết luận trước số §V.

## RANH GIỚI đã giữ
- Reuse: `HidingDB`/`delete` (`common.py`, Bẫy #1 qua `delete()`), `is_frequent`/`hiding_failure`/
  `missing_cost`/`artificial_cost` (`metrics.py`), `mine_fwi` (`miner.py`) cho AC. KHÔNG sửa các module này.
- KHÔNG dùng `select_victim` (baseline có victim-rule riêng). KHÔNG Safe()/no-op/né-non-sensitive.
  KHÔNG nhánh giảm-quantity. `if __name__=="__main__"` guard.
- CHƯA chạy §V/coordinator/dataset thật. CHƯA git.

## RESUME_CMD
```
python3 tests/test_baseline_golden.py     # exit 0 = 7/7 PASS
python3 src/hiding/baseline_ppum.py       # smoke: MAU A@T3→C@T1 ; MIU C@T3→E@T1
```
