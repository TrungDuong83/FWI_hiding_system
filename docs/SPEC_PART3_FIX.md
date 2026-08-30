# SPEC_PART3_FIX — Sửa engine PART 3 (đúng 2 chỗ)

> Deliverable cho Đợt A. Engine PART 3 = **weighted N-list / SWU-N-list** (KHÔNG phải WIT-tree),
> tái dùng từ `fwi_hiding_system_v38 (3).py`. Được control cho phép sửa PART 3 **CHỈ ĐÚNG 2 chỗ
> dưới** (nới Q9 "chỉ sửa tw"). Mọi thay đổi khác trong PART 3 = ngoài phạm vi → DỪNG, ghi
> "CẦN QUYẾT ĐỊNH".

## Bối cảnh (đã audit + verify)
- **Bug đã tìm ra:** `swunl_intersection_optimized` **over-prune khi tạo itemset k≥3** (giao hai
  N-list dẫn-xuất bằng pre/post của node gốc → so mã node ở độ sâu khác nhau → rơi hết). Trên
  chess_fimi ξ=0.90 engine cũ **rớt ~504/584 FWI**. Golden lộ 1 (thiếu `ACD`).
- **Bug thứ hai:** `compute_tw_optimized` nhân `qty` (sai định nghĩa FWI: `tw=Σw/|T|`, không quantity).
- **Bản vá đã verify:** golden 9/9 + fixture 7/7 + brute-force oracle khớp chính xác trên
  chess_fimi (584, tới k=7) và mushroom (57). 0 missing / 0 extra.

---

## FIX A — `compute_tw_optimized` (dòng ~214): bỏ `* qty`

```python
# TRƯỚC:
#   utility = sum(weights.get(item, 0.0) * qty for item, qty in t.items())
# SAU:
utility = sum(weights.get(item, 0.0) for item in t)
```
`s_tk = len(t)` giữ nguyên ( = |T| = số item phân biệt). Không đụng gì khác trong hàm.

---

## FIX B — `swunl_intersection_optimized`: giao theo **tidset**

Thay TOÀN BỘ thân hàm bằng bản dưới (giữ nguyên chữ ký). `tids` đã có sẵn trong mỗi entry
`swunl` = `(pre, weight, tids)`; ta chỉ dùng `tids` + `tw_map` để tính lại ws đúng cho mọi k.

```python
def swunl_intersection_optimized(self, swunl_y, swunl_x, ws_y, ws_x, sumtw, min_ws):
    if not swunl_x or not swunl_y:
        return None
    tids_y = set().union(*(t for _, _, t in swunl_y))
    tids_x = set().union(*(t for _, _, t in swunl_x))
    common = tids_y & tids_x
    if not common:
        return None
    weight = sum(self.tw_map[t] for t in common)      # Σ tw trên giao dịch chứa CẢ hai
    if weight / sumtw < min_ws - 1e-12:               # prune raw + tolerance
        return None
    return [(0, weight, common)]                       # 1 entry: ws = weight/sumtw ; tids = common
```

### Wiring `tw_map` (bắt buộc, để Fix B có `self.tw_map`)
Trong `OptimizedWUNTree_v1`:
```python
def __init__(self, item_weights):
    ...
    self.tw_map = {}                                   # THÊM

def insert_transaction_batch(self, transactions_batch, utilities_batch, tids_batch):
    self.tw_map = dict(zip(tids_batch, utilities_batch))   # THÊM dòng đầu (utilities_batch = tw_list)
    for i, (transaction, utility, tid) in enumerate(zip(...)):
        ...
```
(`utilities_batch` trong core chính là `tw_list` = tw mỗi giao dịch → `tw_map[tid] = tw(tid)`.)

---

## RÀNG BUỘC (không được vi phạm)
1. **CHỈ 2 chỗ trên + wiring `tw_map`.** KHÔNG đụng `find_fwi_optimized`,
   `find_fwi_same_ws_optimized`, `build_node_index_optimized`, tree build, hay logic khác.
2. **Ngưỡng/backend:**
   - Prune nội bộ (Fix B) dùng **raw float + tolerance** `< min_ws - 1e-12`. **KHÔNG** `round` ở
     prune — round-rồi-drop một itemset biên sẽ làm mất mọi superset (hỏng anti-monotone).
   - `round(ws, 3) ≥ ξ` chỉ áp ở **quyết định membership FWI cuối** (production float64).
   - Golden / calibration verify bằng `Fraction` (exact).
3. **Determinism:** tập FWI dedup theo `tuple(sorted(pattern))` ⇒ **bất biến theo thứ tự worker**
   (MP hay đơn luồng ra cùng SET). Không cần tie-break cho tập FWI.
4. **Trade-off (biết trước):** tidset chậm hơn N-list trên dataset dày / ξ thấp. Chấp nhận: RT
   mining KHÔNG phải metric của bài (RT = thời gian *hiding*), chạy 1 lần/config. **Correctness
   trước, tối ưu sau** — chỉ khôi phục fast-path nếu smoke thấy mining quá lâu VÀ fast-path đã
   được kiểm đúng bằng oracle.

---

## VERIFY (Gate G6 — golden + brute-force oracle, thay parity)
Engine coi là đúng **chỉ khi** cả hai:
1. **Golden (Fraction):** mine running example ξ=0.55 → FWI set == 9 tập
   `{A,C,D,E,AC,AD,CD,CE,ACD}`. + fixture (W={A:.4,B:.1,C:.8,D:.4}, ξ=11/25,
   D={T1:AB,T2:BD,T3:ABC}) → 7 tập (có `ABC`).
2. **Brute-force oracle (`tests/oracle_bruteforce.py`):** MATCH CHÍNH XÁC (0 missing / 0 extra,
   per-len khớp) trên **≥2 dataset**:
   - chess_fimi ξ=0.90 → 584 (per-len {1:13, 2:67, 3:159, 4:193, 5:117, 6:32, 7:3})
   - mushroom  ξ=0.60 → 57  (per-len {1:8, 2:18, 3:19, 4:10, 5:2})

Lặp propose→verify→rebut→fix tới khi **2 vòng liên tiếp không thêm lỗi** thì G6 PASS.
