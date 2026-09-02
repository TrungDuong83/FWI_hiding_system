# HANDOFF: CONTROL → QUẢN LÝ THỰC THI — đồng nhất spec (IoT-63257-2026)

> Trả lời cho `HANDOFF_CONTROL_TODO.md`. Đọc để đồng bộ trước khi mở Đợt B. Mọi số dưới đây control
> đã verify độc lập bằng `Fraction`. File nguồn chốt (single source of truth): **SPEC_PART4_HIDING.md,
> CLAUDE.md, REPO_STRUCTURE_FWI.md** (bản đã cập nhật kèm handoff này).

---

## 1. ⛔ FIX #1 (filter `T_sensitive`) — ĐÃ QUYẾT: **GIỮ FILTER. KHÔNG áp Fix #1.**

Mục 3.1 của HANDOFF_CONTROL_TODO (bỏ filter `∧ ws(s)≥ξ`) **bị bác**. Lý do (control verify độc lập):

- Golden ĐÚNG là bất biến khi bỏ filter — **nhưng đó là lý do không đủ** (G2 không phân biệt được, như
  chính handoff cảnh báo). Off-golden thì khác.
- Bỏ filter ⇒ MCPriority thăm cả giao dịch mà SFWI trong đó **đã ẩn** ⇒ **xóa thừa** ⇒ dịch `W_total`
  ⇒ bơm itemset giả. Tái hiện được ca **AC: 0 → 1/9** (safe_check=True).
- Kết luận: filter là **guard đúng** (loại bỏ nước xóa vô ích + AC/side-effect kèm theo), không phải
  divergence code≠bài. (Lưu ý: filter loại **phantom từ nước thừa**; nó KHÔNG bảo đảm AC=0 — xem §7.)

**Việc code (Đợt B):**
- `T_sensitive = { T_k | ∃ s∈S : s⊆T_k ∧ ws(s)≥ξ }` — **áp cho CẢ HAI** thuật toán.
- HFPriority §3.2 hiện **thiếu** filter → **thêm vào** (control verify: golden `C@T3→C@T1` và metrics
  giữ nguyên khi thêm filter — an toàn).

**Việc bài (track VIẾT, không phải việc execution):** sửa Algorithm 1/2 + định nghĩa
`IdentifyTransactions` để ghi rõ chỉ lấy giao dịch còn chứa SFWI **frequent** (`ws(s)≥ξ`). Execution
code theo spec guarded ngay; bài text theo sau. Sau khi cả hai xong → pseudocode == claim == code.

---

## 2. GATE MỚI bắt buộc thêm cho Đợt B — filter-guard fixture

Golden KHÔNG bắt được lỗi filter (đã chứng minh). Cần regression test riêng:
```
W = {A:3/10, B:1/10, C:3/10, D:4/5} ,  ξ = 41/100
D = {T1:ABCD, T2:ACD, T3:ABCD, T4:BC, T5:ACD}
S = {AC, BC} ,  ~S = {A,ACD,AD,B,C,CD,D}
MCPriority safe_check=True:
    CÓ filter    → (HF=1/2, MC=0, AC=0)      ✅ đúng
    BỎ filter    → (HF=1/2, MC=0, AC=1/9)    ❌ bơm AC
```
Code (giữ filter) phải cho `AC=0` ở fixture này. Nếu ra `1/9` ⇒ filter bị bỏ đâu đó ⇒ FAIL gate.

---

## 3. ĐÃ ĐỒNG NHẤT (không cần làm gì — chỉ để hai bên khớp nhận thức)
- **Engine = weighted N-list / SWU-N-list [21]** (N-list gốc [22]), **KHÔNG WIT-tree**. Đã phản ánh
  trong cả 3 file control. (Fix mục 4.1 handoff: `CONTEXT_HANDOFF_PHA2:187` — control lo bên project.)
- **2 fix engine** (control đã duyệt): Fix A (`tw` bỏ qty) + Fix B (`swunl_intersection_optimized`
  giao tidset, vá over-prune k≥3). Cite miner **[21]** (KHÔNG [15]).
- **§V cũ VÔ HIỆU** — engine trước Fix B rớt ~504/584 FWI ⇒ chạy lại toàn bộ §V, không tái dùng số/hình.
- **Backend số:** golden/calibration = Fraction; production = float64 + `round(ws,3)≥ξ`; ξ ≤ 3dp.
  (Verify: float+round3 khớp Fraction, zero mismatch trên 3 golden trace.)
- **maxlen cap = 7:** an toàn ξ cao; ξ thấp phải chạy oracle `maxlen>7` khi calibrate (SPEC §7, REPO §4).

## 4. Handoff items GIỮ NGUYÊN (execution tiến hành như đã ghi)
- **3.2** — một deletion mỗi lần thăm giao dịch; revisit ở pass While sau (KHÔNG loop-nhiều-xóa/visit).
- **3.3** — giữ tên "Missing Cost"; SPEC §8 là track VIẾT, không phải deliverable code.
- **5.1** — baseline PPUM-HUIM: làm ở Đợt B, cấp ngân sách công bằng (cùng deadline).

---

## 5. CONTRACT VERIFY cho Đợt B (gate, khớp SPEC §6)
1. **Golden 3 trace** (khớp CHÍNH XÁC tập itemset, không chỉ số tổng):
   - HFPriority: `C@T3 → C@T1` ; HF=0 ; MC lost {C,CD,ACD}=3/7 ; AC=0.
   - MCPriority `safe=True, mc_tid`: `E@T1 → C@T2 → C@T4` ; residual {AC} (HF=1/2) ; MC=0 ; AC=0.
   - MCPriority `safe=False, mc_tid`: `E@T1 → E@T2 → A@T3` ; HF=0 ; MC lost {A,AD,ACD,E}=4/7 ; AC=0.
2. **Safe unit fixture** (kiểm `Safe` quét TOÀN ~S, không chỉ ns⊆T_k):
   `W={A:2/5,B:1/10,C:4/5,D:2/5}, ξ=11/25, D={T1:AB,T2:BD,T3:ABC}, S={ABC}` →
   `Safe(B,T2)`: full-check=False (AC,BC,C tụt 13/28→2/5) ; reduced "chỉ ns⊆T2"=True (SAI).
3. **Filter-guard fixture** (§2 trên) — bắt buộc AC=0.
4. **float64 + round(ws,3)≥ξ** tái tạo golden, zero mismatch vs Fraction.

---

## 6. CÒN CHỜ TRUNG (chặn calibrate/GCP, không chặn code Đợt B)
- **Q7** — IoT dataset tĩnh (tên/nguồn/kích thước).
- **Target #FWI/#SFWI** mỗi dataset để calibrate ξ quanh đó.
- **C5.2** — coi như đã đóng ("cấm singleton |X|≥2", khớp `validate_sfwi`); chỉ cần xác nhận để track
  viết ghi giả định.

---

## 7. CLAIM AC — SỬA (execution phản biện, control verify: ĐÚNG)

Execution chỉ ra "AC=0 by construction" là **overclaim** — control verify độc lập, xác nhận đúng:
```
W={A:.7,B:.4,C:.8,D:.5,E:.1}, D={CE,ACDE,ABE,ADE}, ξ=0.56, S={AE}
MCPriority safe=True + filter → xóa E@T2 (nước CẦN THIẾT, qua Safe) → phantom {AD,C,D}, AC=3/5, MC=0
```
`Safe` chỉ chặn NSFWI-tụt (⇒ MC=0 by construction), KHÔNG chặn non-FWI-vọt. Nước xóa cần thiết vẫn dịch
`W_total` (Theorem 1) ⇒ phantom ⇒ AC>0. **Phát biểu đúng trong bài (track VIẾT):** *MC=0 by construction
(qua Safe); AC=0 là kết quả thực nghiệm, không phải structural guarantee.* Đã sửa SPEC §3.3 + §8; nếu bản
thảo đang claim "AC=0 by construction" thì phải đổi (reviewer chạy 1 fixture non-FWI-sát-ξ là bắt được).
Không đổi thuật toán (Safe giữ MC-only theo spec khóa); chỉ đổi câu chữ.

Điểm nhỏ execution nêu — **đã sửa:** CLAUDE.md Q9 nay đồng bộ B.4 (nêu 2 fix theo SPEC_PART3_FIX).

Filter-guard fixture (§2) vẫn là gate hợp lệ: nó test *nước thừa* bị chặn (AC=0 cho fixture đó), khác với
"AC=0 tổng quát" (không đảm bảo). Hai điều độc lập, đều đúng.

---

## TÓM TẮT 1 DÒNG
Giữ filter ở cả hai thuật toán + thêm gate filter-guard ; sửa bài (Algorithm/IdentifyTransactions) để
khớp ; mọi engine-fact đã đồng nhất ; 3 file control là nguồn chốt cho Đợt B.
