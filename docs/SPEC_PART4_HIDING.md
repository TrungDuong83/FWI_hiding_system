# SPEC — Code lại PART 4 (Hiding Algorithms) — Repo FWI (IoT-63257-2026)

> Tài liệu THIẾT KẾ. Bản hoàn thiện sau 4 vòng propose–verify–rebut–fix. Mọi con số verified bằng
> `Fraction`. Nguồn chốt: CONTEXT_HANDOFF_PHA2 §3–§6; complexity từ FORMALISM_COMPLEXITY §B2; công
> thức metric từ bản thảo v3_7. Mang về conversation control để duyệt trước khi tạo repo thật.

---

## 0. Phạm vi & nguyên tắc
Sửa **PART 4** (hiding) + **bước chuẩn hóa weight /10** + **metrics FWI**. Engine PART 3 = **weighted
N-list / SWU-N-list [21]** (N-list gốc [22]) — **KHÔNG phải WIT-tree**; giữ nguyên logic, chỉ gỡ Colab.
Engine đã áp **2 fix (control duyệt):** **Fix A** (tw bỏ qty) + **Fix B** (`swunl_intersection_optimized`
giao tidset — vá over-prune k≥3 làm rớt ~504/584 FWI @ chess 0.90). Tách module để test độc lập; mỗi
hàm có tiêu chí verify. Golden test §6 là chuẩn cuối — code chưa tái tạo được golden thì chưa coi là xong.

---

## 1. Module tách
```
src/
├── mining/            # PART 3 = weighted N-list/SWU-N-list [21] (KHÔNG WIT-tree); gỡ Colab
│                       #   + 2 fix engine đã áp: Fix A (tw bỏ qty), Fix B (intersection over-prune)
├── hiding/
│   ├── common.py      # tw / ws / delete / inverted index / backend số  §2
│   ├── select_victim.py   # helper two-stage dùng chung hai thuật toán  §3.5
│   ├── hfpriority.py  # §3.2
│   ├── mcpriority.py  # §3.3 (Safe + no-op)
│   └── baseline_ppum.py   # Q10 — adapt PPUM-HUIM (spec riêng, sau)
├── metrics/
│   └── metrics.py     # HF, MC, AC, RT trên tw/ws — KHÔNG dùng metric utility cũ  §5
└── datautil/
    └── preprocess.py  # load + /10 + bỏ qty + kiểm định dạng  §4
```

---

## 2. Cấu trúc dữ liệu dùng chung — `hiding/common.py`

```
D : dict[tid -> set[item]]     # item là string key (KHÔNG cast int khi lưu)
W : dict[item -> num]          # weight đã chuẩn hóa /10  ∈ [0,1]
inv : dict[item -> set[tid]]   # inverted index; cập nhật khi xóa
tw_cache : dict[tid -> num]
W_total : num                  # biến chạy, cập nhật MỖI lần xóa
```

Hàm lõi (bắt buộc dùng chung để không lệch định nghĩa):
```
tw(t)      = sum(W[i] for i in D[t]) / len(D[t])
ws(X)      = sum(tw_cache[t] for t in ⋂_{i∈X} inv[i]) / W_total
delete(v,t):                       # CHỖ DUY NHẤT được sửa DB
    D[t].discard(v); inv[v].discard(t)
    tw_old = tw_cache[t]; tw_new = tw(t)
    W_total += tw_new - tw_old; tw_cache[t] = tw_new
```

> **Bẫy #1 (hay sai nhất):** xóa một item đổi `tw(T_k)` ⇒ đổi `W_total` ⇒ **mọi** `ws` dịch, kể cả
> itemset không liên quan. Gom toàn bộ cập nhật `W_total / tw / inv` vào `delete()`; không sửa DB nơi
> khác.

### Backend số — ĐÃ CHỐT
| Ngữ cảnh | Kiểu | Ngưỡng FWI |
|---|---|---|
| Golden / calibration / verify | `Fraction` (exact) | `ws >= ξ` (chính xác) |
| Production run | `float64` | `round(ws, 3) >= ξ` |

`ξ` mỗi dataset lưu ≤ 3 chữ số thập phân. float64 + `round(ws,3) >= ξ` đã verify tái tạo cả ba
golden trace và toàn bộ HF/MC/AC **khớp Fraction, không lệch một itemset nào**. Đây là **quy ước phân
loại tường minh** (không phải "float có sai số rồi vá") — nêu rõ trong Experimental Setup của bài.

---

## 3. Đặc tả thuật toán

### 3.1 Ràng buộc chung (cả hai) — bất biến correctness
- **Victim ∈ SFWI:** `Cand(T_k) = { i ∈ T_k | ∃ s∈S, i∈s }`. Lemma A1: xóa item∈X làm `ws(X)` giảm
  ngặt; xóa item∉X không đảm bảo (phản ví dụ `ws` tăng — Weight Transformation Paradox). Code cấm
  victim ∉ SFWI.
- **Cấu trúc chọn victim = TWO-STAGE per-(item, giao dịch):** vòng NGOÀI duyệt *giao dịch*; vòng TRONG
  chọn item score cao nhất **có mặt trong chính giao dịch đó**; xóa item đó khỏi giao dịch đó. Một
  deletion mỗi lần thăm một giao dịch. (KHÔNG cài "một victim toàn cục xóa khỏi nhiều giao dịch".)
- **Score precompute MỘT LẦN, per-item, bất biến** qua giao dịch và iteration (`S, ~S, w` cố định).
  KHÔNG tính lại per-(item,txn); KHÔNG re-mine `~S` giữa chừng (`~S` đóng băng ở đầu).
- **|X| ≥ 2 ∀X∈S**; `w(i) > 0`; **"ẩn" = `ws(X) < ξ`** (không phải count = 0).
- **Tie-break (D2): id tăng dần** — item-id nhỏ hơn thắng (vòng trong); TID nhỏ hơn xử trước (vòng
  ngoài). Deterministic cho E6 multi-seed.

### 3.2 HFPriority — `hfpriority.py`
```
Input: D, S (|X|≥2), ξ ; ScoreHFP (precomputed)
While (∃ s∈S : ws(s) ≥ ξ):
    T_sensitive = { T_k | ∃ s∈S : s ⊆ T_k }
    Sort T_sensitive theo tw GIẢM DẦN (tie: TID tăng dần)         # Def 10
    For each T_k in T_sensitive:
        v* = select_victim(D[T_k], sensitive_items, ScoreHFP, safe=None)
        If v* ≠ null:
            delete(v*, T_k)                                        # §2
            If (∀ s∈S : ws(s) < ξ): break
Output: sanitized D
```
- Không safe-check ⇒ HF→0, MC có thể cao (đặc tính chấp nhận được của HFPriority).
- **Termination:** Φ = tổng số vị trí (item-của-S) trong DB; mỗi `delete` giảm Φ ≥ 1; hễ còn `s` lộ
  thì luôn tồn tại candidate ⇒ tiến triển ⇒ hữu hạn. Không cần no-op.
- **Verify (golden):** `C@T3 → C@T1` ; HF=0 ; MC lost {C,CD,ACD}=3/7 ; AC=0.

### 3.3 MCPriority — `mcpriority.py` (Safe deletion + no-op, tham số hóa)

**Safe Deletion (định nghĩa hình thức V0):**
$$\text{Safe}(v,T_k) \iff \forall\, ns\in \tilde S :\ ws'(ns)\ge\xi$$
`ws'` = weighted support **sau khi giả định** xóa `v` khỏi `T_k` **trên toàn DB** (phải tính lại
`W_total`). MCPriority chỉ thực hiện safe deletion.

```
Input: D, S (|X|≥2), ~S, ξ, safe_check∈{T,F}, order∈{mc_tid,tw_desc} ; ScoreMCP (precomputed)
1  While (∃ s∈S : ws(s) ≥ ξ):
2      T_sensitive = { T_k | ∃ s∈S : s⊆T_k ∧ ws(s)≥ξ }           # chỉ SFWI CÒN LỘ (filter — xem ⚑)
3      order=mc_tid  → duyệt theo TID (KHÔNG sort)     # D1 — cấu hình chính thức
       order=tw_desc → sort tw giảm (tie TID↑)          # dành ablation E5
4      movedThisPass = false
5      For each T_k in T_sensitive:
6          safe = (λ v: Safe(v, T_k)) if safe_check else None
7          victim = select_victim(D[T_k], sensitive_items, ScoreMCP, safe)
8          If victim ≠ null:
9              delete(victim, T_k) ; movedThisPass = true
10             If (∀ s∈S : ws(s) < ξ): break
11     If (not movedThisPass): break        # NO-OP minh bạch → DỪNG (HF>0 hợp lệ)
Output: sanitized D    # safe_check=True: có thể còn s lộ (HF>0); MC=0 BY CONSTRUCTION (Safe). AC=0 KHÔNG đảm bảo (xem ghi chú)
```

**Hàm `Safe(v, T_k, ~S, ξ)` — đặc tả đầy đủ (điểm chết người, spec rõ để không tái diễn code≠bài):**

Tiền điều kiện: `v∈T_k`; `|T_k|≥2` (T_k chứa SFWI |s|≥2) ⇒ mẫu `(|T_k|−1) ≥ 1`.

Đại lượng chung (n=|T_k|, `Ssum` = tổng weight của T_k):
$$tw_{old}=\frac{Ssum}{n},\quad tw_{new}=\frac{Ssum-w(v)}{n-1},\quad
\Delta=\frac{tw_{old}-w(v)}{n-1},\quad W'_{total}=W_{total}+\Delta$$

Ba case tử số `num(ns)=Σ_{T⊇ns} tw(T)` — **bắt buộc đúng cả ba**:
```
for ns in ~S:
    if   ns ⊄ T_k :  num' = num(ns)                       # T_k không đóng góp
    elif v ∉ ns   :  num' = num(ns) - tw_old + tw_new     # T_k vẫn ⊇ ns, đổi tw
    else          :  num' = num(ns) - tw_old              # v∈ns ⇒ T_k không còn ⊇ ns
    if num' / W'_total < ξ:  return False
return True
```
> Phải chia cho `W'_total`, KHÔNG phải `W_total` (Bẫy #1). Mặc định **quét toàn bộ ~S**.

**Micro-opt (tùy chọn, đã chứng minh):** nếu `Δ ≤ 0` (victim nặng/trung tính, `W_total` không tăng)
thì mọi `ns⊄T_k` có `ws'(ns) ≥ ws(ns) ≥ ξ` (invariant MC=0) ⇒ không thể tụt ⇒ chỉ cần lặp `ns⊆T_k`.
Nếu `Δ > 0` ⇒ **bắt buộc** quét toàn ~S. Bật fast-path chỉ khi có cờ, và phải test bằng oracle.

**Oracle (chuẩn verify):** copy DB → xóa `v@T_k` → tính lại `ws(ns)` từ đầu → so `Safe_fast ==
Safe_oracle` trên golden + fixture §6.

- **Escalation = NO-OP (dòng 11):** mọi candidate bị Safe chặn ⇒ DỪNG, nhận HF>0. Không fallback,
  không hy sinh NSFWI — giữ MCPriority ở cực "MC=0".
- **⚠️ MC=0 by construction; AC=0 KHÔNG.** `Safe` chỉ chặn NSFWI **tụt** dưới ξ ⇒ MC=0 đảm bảo. Nhưng
  nước xóa cần thiết vẫn dịch `W_total` (Theorem 1) ⇒ có thể đẩy non-FWI **vượt** ξ ⇒ phantom ⇒ AC>0,
  ngay cả với filter + safe_check=True. Phản ví dụ (verified): `W={A:.7,B:.4,C:.8,D:.5,E:.1},
  D={CE,ACDE,ABE,ADE}, ξ=0.56, S={AE}` → xóa `E@T2` (cần thiết, qua Safe) → phantom {AD,C,D}, AC=3/5.
  **Bài phải phát biểu: MC=0 by construction, AC=0 là kết quả thực nghiệm** (không by construction).
- **Log bắt buộc:** #no-op-stop, #candidate bị Safe chặn (cột cho bảng thực nghiệm E0).
- **Termination:** Φ giảm HOẶC full-pass-no-move ⇒ break; tối đa Φ(D₀)+1 iteration.
- **Complexity (từ FORMALISM §B2):**
  HFPriority `O(m²ℓ²|S| + m²ℓ log m)`; MCPriority `O(m²ℓ²|~S| + m²ℓ log m)` (thay |S|→|~S|). Hệ số
  |~S| đã ứng với quét toàn ~S mỗi candidate. (`m`=#giao dịch, `ℓ`=độ dài giao dịch tối đa,
  D=tổng số item xóa ≤ mℓ.)
- **Verify (golden):**
  - `safe=True, mc_tid`: `E@T1 → C@T2 → C@T4` ; residual {AC} (HF=1/2) ; MC=0 ; AC=0.
  - `safe=False, mc_tid`: `E@T1 → E@T2 → A@T3` ; HF=0 ; MC lost {A,AD,ACD,E}=4/7 ; AC=0.

### 3.4 Mô hình Score — VIỆC 0 ĐÃ CHỐT
- **Score = PER-ITEM.** `ScoreHFP(v)=|SCov(v)|·w(v)`, `ScoreMCP(v)=1/(|NSCov(v)|+1)` — không có đối số
  `T_k`. Một item một score, bất biến qua mọi giao dịch và iteration ⇒ precompute một lần.
- **Quyết định xóa = PER-(item, giao dịch)**, two-stage (§3.1). Không có "cặp" nào được chấm điểm như
  một cặp.
- **D1:** HFPriority tw giảm; MCPriority TID order. **D2:** id tăng. **D3** (bài, không phải code): đã
  bỏ overclaim "optimal/best pair".

### 3.5 `select_victim()` — helper two-stage dùng chung
```
select_victim(T_k, sensitive_items, score, safe=None) -> item | None
    Cand = [ i for i in T_k if i in sensitive_items ]
    Cand.sort(key=lambda v: (-score[v], id_key(v)))    # score ↓, tie: id ↑ (D2)
    for v in Cand:
        if safe is None or safe(v): return v
    return None
```
- `id_key(v) = int(v) if v.isdigit() else v` — "id tăng dần" là **numeric ascending**. Dataset FIMI
  dùng id số; sort chuỗi sẽ cho `"10" < "2"` sai thứ tự, phá tính tái lập. (Golden dùng A–E nên
  lexicographic trùng ý định.)
- Ba lời gọi phủ hết cấu hình E0/E5: HFPriority `(…, ScoreHFP, safe=None)`; MCPriority `safe=False`
  `(…, ScoreMCP, safe=None)`; MCPriority `safe=True` `(…, ScoreMCP, safe=Safe)`.

---

## 4. Sửa mining `tw` + chuẩn hóa weight — `datautil/preprocess.py`

**Lỗi 1 (dòng ~214 trong `fwi_hiding_system_v38.py`):** hiện tính `Σ(w×qty)/|T|` (có qty) → SAI định
nghĩa FWI.
```python
# CŨ:  utility = sum(weights.get(i,0.0) * qty[i] for i in t) / len(t)
# MỚI: tw      = sum(weights.get(i,0.0)          for i in t) / len(t)
```
- Áp cho **cả mining lẫn re-mine** (tính metric). Loader giữ nguyên (vẫn đọc qty), qty chỉ **bị bỏ
  qua** ở bước tính `tw`. Dataset có qty>1 vẫn nạp được.
- **Ranh giới Q9:** đây là **sửa định nghĩa** (bài định nghĩa `tw=Σw/|T|`, code cũ thêm qty = bug).
  Đây là **Fix A**. Engine (weighted N-list/SWU-N-list) còn một fix nữa đã áp trong Đợt A — **Fix B**:
  `swunl_intersection_optimized` over-prune k≥3 làm rớt ~504/584 FWI (chess@0.90) → sửa thành giao
  tidset. Cả hai theo SPEC_PART3_FIX; ngoài đó mọi logic traversal giữ nguyên.

**Chuẩn hóa /10 (Q4):** `W = {i: raw/10}`. Bất biến chứng minh được: `ws = Σtw / W_total`; nhân mọi
`w` với hằng `k` ⇒ tử và mẫu cùng nhân `k` ⇒ `ws` không đổi ⇒ **FWI set y hệt ∀ξ**. Mine trước/sau
/10 chỉ để sanity-check.

**Kiểm định dạng:** warn item không có weight (dùng `weights.get(i,0.0)`); **error** nếu SFWI singleton
(|X|<2, phá §3.1); warn `w(i) ≤ 0` (phá `w>0`).

---

## 5. Metrics FWI — `metrics/metrics.py` (định nghĩa lại trên tw/ws)

| Metric | Công thức | Ghi chú tính |
|---|---|---|
| **HF** | `\|{s∈S : ws_san(s) ≥ ξ}\| / \|S\| × 100%` | recompute ws(s) trên DB san. HF=0 = ẩn hết. |
| **MC** | `\|{ns∈~S : ws_san(ns) < ξ}\| / \|~S\| × 100%` | `~S` **đóng băng từ DB gốc**. |
| **AC** | `\|FWI(san) \ FWI(orig)\| / \|FWI(san)\| × 100%` | mẫu = **\|FWI(san)\|** (v3_7). Guard `\|FWI(san)\|=0 → AC=0`. Re-mine **đầy đủ**, không giới hạn kích thước itemset. |
| **RT** | wall-clock **chỉ pha hiding**, chốt TRƯỚC khi dựng evaluator/re-mine | RT một nguồn — 1 máy GCP (Q8). |

- `ws_san` dùng `W_total` của **DB đã sanitize** (không phải gốc) — Bẫy #1.
- HF/MC rẻ (recompute trên tập đóng băng). **AC đắt** (mine lại toàn bộ) ⇒ bước eval **không
  deadline**, chạy tới xong.
- KHÔNG port IUS/DUS/TMR/DDI (dựa `TU=Σw·qty`, sai định nghĩa FWI).

---

## 6. Golden test + Safe fixture — ĐÃ VERIFY BẰNG FRACTION

**Running example (ξ=0.55):**
```
W = {A:0.9, B:0.4, C:0.7, D:0.5, E:0.2}   (chưa /10; ws bất biến theo scale)
D: T1=ACDE  T2=BCE  T3=ACD  T4=ABCE  T5=ACDE  T6=BDE
W_total = 16/5 = 3.2 ;  ws(AC) = 0.75
FWI(0.55) = {A,C,D,E, AC,AD,CD,CE, ACD}  (9)
S = {AC,CE} ; ~S = {A,C,D,E, AD,CD,ACD}
ScoreHFP: A=0.9, C=1.4(max), E=0.2, D=0, B=0
ScoreMCP: B=1.0, E=0.5, A=0.25, C=0.25, D=0.2
```
Kết quả bắt buộc tái tạo (khớp CHÍNH XÁC tập itemset, không chỉ con số tổng):

| Config | Trace | HF | MC | AC |
|---|---|---|---|---|
| HFPriority | `C@T3 → C@T1` | 0 | lost {C,CD,ACD} = 3/7 | 0 |
| MCPriority `safe=True` (TID) | `E@T1 → C@T2 → C@T4` | 1/2, residual {AC} | 0/7 | 0 |
| MCPriority `safe=False` (TID) | `E@T1 → E@T2 → A@T3` | 0 | lost {A,AD,ACD,E} = 4/7 | 0 |

**Safe fixture (regression test riêng — golden KHÔNG bắt được lỗi reduced-check):**
```
W = {A:2/5, B:1/10, C:4/5, D:2/5} ,  ξ = 11/25
D = {T1:AB, T2:BD, T3:ABC} ,  S = {ABC} ,  ~S = {A,AB,AC,B,BC,C}
Safe(B, T2):  xóa B nhẹ → W_total 14/15 → 13/12  (Δ=+3/20)
  AC, BC, C  (đều ⊄ T2, ở T3) tụt 13/28 → 2/5 < 11/25
Kỳ vọng:  full-check → False (đúng) ; reduced-check "chỉ ns⊆T2" → True (SAI, bỏ sót AC/BC/C)
```
> Trên golden example, reduced-check và full-check **không phân kỳ** ở bất kỳ (v,T_k) nào ⇒ một
> implementation cài SAI vẫn PASS golden. Bắt buộc dùng fixture này để verify yêu cầu "kiểm toàn ~S".

Bảng verify từng hàm:
| Hàm | Verify |
|---|---|
| `tw`,`ws`,`delete` | `W_total=3.2`; `ws(AC)=0.75`; sau delete cập nhật đúng `W_total`. |
| `preprocess`(/10) | FWI(orig) trước/sau /10 giống hệt ở cùng ξ. |
| `ScoreHFP` | A=0.9, C=1.4, E=0.2, D=0. |
| `ScoreMCP` | A=C=1/4, D=1/5, E=1/2, B=1. |
| `Safe` | golden: `Safe(E,T1)=Safe(C,T2)=Safe(C,T4)=True`, các nước sau đều False → no-op. fixture: `Safe_full(B,T2)=False` nhưng `Safe_reduced=True`. |
| `HFPriority` | HF=0, MC lost {C,CD,ACD}, AC=0. |
| `MCPriority` | `safe=True`: residual {AC}, MC=0, AC=0, no-op dừng. `safe=False`: HF=0, MC lost 4/7. |
| float64+round3 | ba trace + HF/MC/AC khớp Fraction, zero mismatch. |

---

## 7. CẦN QUYẾT ĐỊNH — còn đúng 2 mục (ngoài Q1–Q10 & §3, không tự quyết)
1. **IoT dataset tĩnh (Q7):** chọn dataset nào (tên / nguồn / kích thước). Chưa có trong project.
2. **Target #FWI/#SFWI để calibrate ξ mỗi dataset.**

Ngoài lề, không chặn PART 4:
- **Baseline PPUM-HUIM (Q10):** nguồn đã thấy trong project (`Efficient…hiding sensitive high utility
  itemsets.pdf`); spec `baseline_ppum.py` là việc riêng sau.
- **Wording FORMALISM dòng ~140** ("ns⊆T_k") cần sửa thành "toàn ~S" — việc theory-side của control;
  box complexity không đổi.

Các mục §7 draft cũ đã đóng: Việc 0 (per-item/per-txn), tối ưu Safe (toàn ~S), ordering (TID), denom
AC (|FWI(san)|), số mũ complexity (từ FORMALISM), kiểu số production (float64+round3).

### ⚑ CẦN QUYẾT ĐỊNH thêm — từ handoff conversation thực thi

- **⚑ Fix #1 (filter `T_sensitive`) — ĐỀ NGHỊ KHÔNG ÁP.** Handoff đề xuất bỏ filter `∧ ws(s)≥ξ` để
  khớp Algorithm 1/2 (không filter). Verify độc lập (control): golden bất biến NHƯNG off-golden bỏ
  filter gây **xóa thừa** — 49/15000 ca đổi số deletion, **4/15000 ca đổi metric** (có ca `HF` lật
  0↔1/2, có ca `AC` đổi). Filter là **guard đúng**, không phải divergence. → Giữ filter ở MCPriority;
  và vì nhất quán, **thêm cùng filter vào HFPriority §3.2** (hiện thiếu). Để code==bài, **sửa BÀI**:
  Algorithm 1&2 ghi rõ IdentifyTransactions trả giao dịch còn chứa ≥1 SFWI **frequent** (`ws(s)≥ξ`).
  **Không tự áp — chờ control chốt hướng (giữ filter + sửa bài) hay literal-pseudocode.**
- **MAX_PATTERN_LENGTH=7 cap:** an toàn ở ξ cao (G6). Ở ξ thấp (thực nghiệm) có thể **rớt FWI dài >7**.
  Khi calibrate ξ phải chạy oracle `maxlen>7` để chắc không bỏ sót; nếu có → nâng cap hoặc ghi rõ giới
  hạn trong bài. (Cùng loại rủi ro "silent drop" như bug Fix B — phải kiểm.)
- **§V CŨ VÔ HIỆU:** engine trước Fix B rớt ~504/584 FWI ⇒ mọi HF/MC/AC/RT + Fig 1–7 cũ **không dùng
  được**, phải chạy lại toàn bộ §V sau khi vá. (Ghi để track viết; không phải deliverable code.)

---

## 8. Trình bày thuật toán cho bản thảo (EN, giọng tác giả) — TRACK VIẾT (không phải deliverable code)

> Bám thuật ngữ §IV v3_7: *Max-Conflict / Min-Side-Effect strategy, victim pair (T_k, v), safe state,
> look-ahead, clean itemsets, inverted index*. Dùng cho §IV.C — chỉnh nhẹ khi ghép vào bài.

**Scoring, from the paradox.** Theorem 1 shows that removing an item `v` from a transaction shifts its
average weight by `Δ = (tw(T_k) − w(v))/(|T_k| − 1)`, so a single deletion never affects one itemset
in isolation — it moves `W_total` and, with it, the weighted support of every itemset at once. Two
levers follow. To drive the support of a sensitive itemset down as sharply as one deletion allows, the
item removed should carry a large unit weight; to relieve as many sensitive itemsets as possible at
the same time, it should belong to many of them. HFPriority combines the two as
`ScoreHFP(v) = |SCov(v)| × w(v)`. MCPriority inverts the second lever toward preservation, scoring by
`ScoreMCP(v) = 1/(|NSCov(v)| + 1)` so that an item bridging many clean itemsets is given a small score
and thus protected, while an isolated item is preferred for removal.

**HFPriority (Priority on Hiding Failure).** The algorithm adopts the Max-Conflict strategy and works
toward a rapid safe state. Its main loop runs while at least one sensitive itemset `s` still satisfies
`ws(s) ≥ ξ`. On each pass the sensitive transactions — those containing some `s ∈ S` — are collected
and sorted in descending order of transaction weight, ties resolved by ascending TID, so that the
transactions whose editing perturbs `tw` most are handled first. Within a transaction the candidates
are restricted to items belonging to some sensitive itemset, which keeps every deletion admissible in
the sense of Lemma A1, and the candidate with the highest `ScoreHFP` is removed. The affected `tw(T_k)`,
`W_total`, and the supports `ws(s)` are updated through the inverted index, and the loop terminates as
soon as all sensitive itemsets fall below `ξ`. Because HFPriority performs no side-effect screening, it
reduces the Hiding Failure to zero, though at the possible expense of a higher Missing Cost.

**MCPriority (Priority on Missing Cost).** MCPriority pursues the opposite goal, the preservation of
non-sensitive knowledge, and therefore trades weight-based urgency for a look-ahead safeguard. Its
sensitive transactions are processed in identification order rather than by weight, since the algorithm
no longer competes for hiding speed. For each transaction the candidates are ranked by `ScoreMCP`, and
before a deletion is committed the candidate is put through a safe-deletion test: the removal is
simulated over the whole database and accepted only when every non-sensitive itemset stays at or above
`ξ`. This test must range over all of `~S`, not merely the itemsets contained in the current
transaction, because deleting a light item raises `W_total` and can push a non-sensitive itemset that
lies elsewhere below the threshold. When a full pass yields no admissible deletion, MCPriority halts
rather than sacrifice a clean itemset — an explicit no-op that may leave some sensitive itemsets
exposed, so that `HF > 0`, while guaranteeing by construction that the Missing Cost is zero. The
Artificial Cost, in contrast, is not eliminated by construction: the safe-deletion test screens only
for non-sensitive itemsets that would fall below `ξ`, whereas the same coupling through `W_total`
established in Theorem 1 can lift a currently non-frequent itemset above the threshold. A zero
Artificial Cost is therefore reported as an empirical outcome on the benchmark datasets rather than a
structural guarantee.

**Threshold convention (for Experimental Setup).** Weighted supports are computed in double precision
and an itemset is declared frequent when its support, rounded to three decimal places, is at least `ξ`;
the sensitive and non-sensitive sets are frozen from the original database, and the Artificial Cost is
obtained by mining the sanitized database in full. Reference traces on the running example were verified
with exact rational arithmetic, and the rounded double-precision procedure reproduces them without a
single itemset misclassified.
