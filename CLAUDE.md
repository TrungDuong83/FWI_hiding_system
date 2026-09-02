# CLAUDE.md — Repo FWI Hiding (IoT-63257-2026)

> File chỉ dẫn cho Claude Code (agent thực thi) khi làm việc trên repo này. Đọc TRƯỚC mọi phiên.
> Trạng thái nằm trong FILE (plan / PROGRESS / báo cáo), không dựa trí nhớ.

---

## PHẦN A — 4 NGUYÊN TẮC CODE (giữ nguyên, áp cho mọi thay đổi)

1. **Think before coding.** Trước khi gõ, nêu 1–3 dòng: sửa cái gì, ở đâu, vì sao, ảnh hưởng gì.
   Không sửa mù.
2. **Simplicity first.** Code tối thiểu giải quyết đúng vấn đề. Không thêm abstraction / config / tối
   ưu không ai yêu cầu. Một hàm 20 dòng đủ đúng thì không viết class 200 dòng.
3. **Surgical.** Giữ nguyên phần đang chạy đúng (mining engine PART 3). Chỉ chạm đúng dòng cần. Mỗi
   thay đổi phải trả lời được "vì sao dòng này phải đổi".
4. **Goal-driven + verify.** Mỗi thành phần có tiêu chí kiểm được (golden test §B.6). Chạy được golden
   test trước khi coi là xong. Không tự tuyên bố "đã fix" mà chưa verify.

---

## PHẦN B — QUY ƯỚC REPO FWI

### B.0 Repo này là gì
Code cho bài **"Efficient Methods for Hiding Frequent Weighted Itemsets"** (IEEE IoT Journal,
resubmit). Hai thuật toán ẩn FWI bằng **item deletion**: **HFPriority** (ưu tiên ẩn nhanh, Max-Conflict
strategy) và **MCPriority** (ưu tiên bảo toàn NSFWI, Min-Side-Effect strategy). Kế thừa **mining engine
PART 3** (**weighted N-list / SWU-N-list** [21] Bui/Vo ESWA 2018; N-list gốc [22] Deng 2012 —
**KHÔNG phải WIT-tree**, đã xác minh bằng code v38) + 7 dataset FIMI mở rộng.

> **Nguyên nhân gốc bài bị reject:** code ≠ pseudocode ≠ văn xuôi. Repo này code LẠI cho khớp bài (bản
> lý thuyết đã sửa, khóa trên v3_7). Mọi thay đổi phải làm giảm — không tăng — độ lệch này.

### B.1 Định nghĩa nền — CODE PHẢI KHỚP TỪNG CHỮ
- **Transaction weight:** `tw(T) = Σ_{i∈T} w(i) / |T|` — **trung bình cộng weight, KHÔNG quantity.**
- **W_total = Σ_T tw(T)** — trên **toàn bộ** giao dịch (kể cả không nhạy cảm).
- **Weighted support:** `ws(X) = [Σ_{T⊇X} tw(T)] / W_total`.
- **FWI:** X là FWI ⟺ `ws(X) ≥ ξ`.
- **SFWI (S):** itemset nhạy cảm cần ẩn. **NSFWI (~S):** FWI không nhạy cảm.
- **SCov(v)** = #SFWI chứa item v. **NSCov(v)** = #NSFWI chứa v.
- **ScoreHFP(v) = |SCov(v)| × w(v)** ; **ScoreMCP(v) = 1 / (|NSCov(v)| + 1)** — cả hai **per-item**,
  precompute một lần, bất biến qua giao dịch và iteration.
- **Inverted index** ID(i) = tập TID chứa item i (lookup O(1)).
- **Backend số:** golden/calibration = `Fraction` (exact); production = `float64` với ngưỡng
  `round(ws, 3) ≥ ξ`; ξ mỗi dataset lưu ≤ 3 dp. (Đã verify float+round3 khớp Fraction, zero mismatch.)

> **Bẫy #1 hay sai nhất:** sau mỗi lần xóa item, `tw` giao dịch đó đổi ⇒ **W_total đổi ⇒ MỌI ws dịch.**
> Mọi check `ws(X) < ξ` hay `Safe(...)` phải tính theo **W_total mới**. Quên cập nhật W_total = sai (đã
> xác minh bằng tay). Gom mọi cập nhật DB vào `delete()`.

### B.2 Mười quyết định đã chốt (Q1–Q10) — KHÔNG tự đổi
| # | Quyết định |
|---|---|
| Q1 | CHỈ giải quyết **ws** cho FWI hiding. KHÔNG wus, KHÔNG utility/HUIM. |
| Q2 | **Hướng B**: code lại cho khớp bài (cài đúng 2 công thức Score). |
| Q3 | **tw = Σw/\|T\|, bỏ quantity.** Sửa dòng tính tw trong engine (SPEC §4). |
| Q4 | Chuẩn hóa weight **chia 10** → [0,1]. ws bất biến theo scale, chỉ đổi trình bày. |
| Q6 | Giữ kết quả trung thực dù xấu. KHÔNG diễn giải ngược. |
| Q7 | Thêm ≥1 **IoT dataset tĩnh**. Chạy lại toàn bộ. |
| Q8 | Chạy lại **TOÀN BỘ trên 1 máy GCP** (RT một nguồn). |
| Q9 | **GIỮ engine mining PART 3** (weighted N-list [21]). Gỡ Colab + 2 fix theo SPEC_PART3_FIX (Fix A `tw` bỏ qty, Fix B `swunl_intersection`); ngoài đó KHÔNG đụng logic (đồng bộ B.4). |
| Q10 | Baseline: adapt **PPUM-HUIM** hiding, cấp ngân sách công bằng. |

### B.3 Ràng buộc thuật toán (correctness invariants)
- **Victim BẮT BUỘC ∈ SFWI đang xét.** Lemma A1: xóa item∈X làm ws(X) giảm ngặt; xóa item∉X không đảm
  bảo (phản ví dụ ws tăng — Weight Transformation Paradox). Code KHÔNG cho victim ngoài SFWI.
- **Chọn victim = two-stage per-(item, giao dịch):** vòng ngoài duyệt giao dịch, vòng trong chọn item
  score cao nhất **có mặt trong chính giao dịch đó**. Score là per-item (precompute), nhưng quyết định
  là per-(item, txn). KHÔNG cài "một victim toàn cục xóa khỏi nhiều giao dịch".
- **|X| ≥ 2** cho mọi SFWI (cấm singleton) ⇒ giao dịch không bao giờ rỗng sau xóa. **w(i) > 0** ngặt.
- **Một deletion mỗi lần thăm giao dịch:** mỗi lần vào một giao dịch xóa **nhiều nhất 1 item** rồi
  sang giao dịch khác; chỉ quay lại giao dịch đó ở **pass While sau**. KHÔNG cài loop-nhiều-xóa-trong
  -một-visit. **"Ẩn" = ws(X) < ξ, KHÔNG phải count = 0.**
- **Tie-break: id tăng dần (numeric).** item-id nhỏ hơn thắng; TID nhỏ hơn xử trước. Dùng
  `int(v) if v.isdigit() else v` — dataset FIMI id số, sort chuỗi sẽ sai ("10" < "2").
- **MCPriority chỉ thực hiện SAFE deletion** (`Safe` kiểm **toàn bộ ~S**) + dừng bằng **no-op** minh
  bạch (SPEC §3.3). KHÔNG fallback, KHÔNG hy sinh NSFWI. Chấp nhận HF>0 để giữ MC=0.

### B.4 Ranh giới — KHÔNG ĐỤNG
- **KHÔNG đụng logic mining PART 3** (weighted N-list/SWU-N-list). Chỉ gỡ phụ thuộc Colab (I/O). Hai
  chỗ mining được chạm (đã áp trong Đợt A, theo SPEC_PART3_FIX): **Fix A** dòng `tw` bỏ `*qty` (sửa
  định nghĩa); **Fix B** `swunl_intersection_optimized` → giao tidset (sửa bug over-prune k≥3 làm rớt
  ~504/584 FWI ở chess@0.90). Ngoài hai fix này, mọi logic traversal giữ nguyên.
- **GIỮ metric HF.** Bài FWI DÙNG HF (khác dự án SFWUP cũ đã bỏ HF). Đừng nghe kit cũ bảo bỏ HF.
- **CHỈ 4 metric:** HF, MC, AC, RT. **KHÔNG port IUS/DUS/TMR/DDI** từ repo cũ (dựa TU=Σw·qty, sai định
  nghĩa FWI; số cũ >21000% đã chứng minh không đáng tin).
- **KHÔNG mang** RISWU / SWM / SDIF / SFWUP-đóng-băng / mọi CSV kết quả bài cũ.

### B.5 Quy trình chạy (khi tới pha thực thi trên VM — không phải phiên thiết kế)
3 bước, không phóng mù:
1. **CHUẨN BỊ** — viết/kiểm coordinator + verify lưới ô đúng spec + verify logging đủ cột (HF/MC/AC/RT
   + escalation counter cho MCPriority). Chưa chạy ô nào. Báo cáo ra file.
2. **SMOKE TEST** — chạy 1–2 ô đại diện (chọn ô KHÓ NHẤT để bắt edge case) → verify metric ra đúng
   (không NaN) + push OK. Chưa phóng.
3. **PHÓNG** — smoke đạt mới launch toàn bộ (nền, detach).

Hạ tầng chạy dài:
- Chạy nền sống sót rớt SSH:
  `setsid nohup python3 coordinator/run_coordinator.py >/dev/null 2>&1 </dev/null & disown` → verify
  `pgrep -af` + `ps -o ppid= -p <PID>` = 1.
- Coordinator: chạy **ô tuần tự** (RT không tranh tài nguyên → defensible), song song chỉ TRONG 1 ô.
- **Checkpoint + commit+push sau MỖI ô.** Resume idempotent (skip ô đã có file kết quả).
- **MỘT git writer = coordinator.** KHÔNG rebase/force/amend trên branch đang chạy. Experiment ở branch
  riêng `exp/...`, không đụng main tới khi đóng gói.
- `pgrep` là sự thật, KHÔNG dựa log mtime (baseline chạy dài im lặng ≠ chết).
- **KHÔNG chạy script trần** nếu thiếu `if __name__=="__main__"` guard. Luôn chạy qua coordinator.

### B.6 Golden test (chạy được TRƯỚC khi coi là xong bất kỳ hàm nào)
Running example ξ=0.55 (verify độc lập bằng `Fraction`):
```
W = {A:0.9, B:0.4, C:0.7, D:0.5, E:0.2}   (chưa /10)
D: T1=ACDE  T2=BCE  T3=ACD  T4=ABCE  T5=ACDE  T6=BDE
W_total = 16/5 = 3.2 ;  ws(AC) = 0.75
FWI(0.55) = {A,C,D,E, AC,AD,CD,CE, ACD}   (9)
S = {AC,CE} ; ~S = {A,C,D,E, AD,CD,ACD}
SCov(C)=2 ; NSCov(D)=4 ; NSCov(E)=1
ScoreHFP: A=0.9, C=1.4(max), E=0.2, D=0   → HFPriority victim = C
ScoreMCP: B=1.0, E=0.5, A=0.25, C=0.25, D=0.2
```
Kết quả BẮT BUỘC tái tạo (khớp CHÍNH XÁC tập itemset, không chỉ con số tổng):
- **HFPriority** — `C@T3 → C@T1` : `HF=0` ; mất NSFWI {C, CD, ACD} (MC=3/7) ; `AC=0`.
- **MCPriority `safe_check=True`, TID order** — `E@T1 → C@T2 → C@T4` ; nước tiếp không safe → no-op
  dừng ; còn lộ {AC} (`HF=1/2`) ; `MC=0` ; `AC=0`.
- **MCPriority `safe_check=False`, TID order** — `E@T1 → E@T2 → A@T3` ; `HF=0` ; mất {A, AD, ACD, E}
  (MC=4/7) ; `AC=0`.

**Safe fixture (BẮT BUỘC riêng — golden KHÔNG bắt được lỗi reduced-check `Safe`):**
```
W = {A:2/5, B:1/10, C:4/5, D:2/5} , ξ = 11/25 , D = {T1:AB, T2:BD, T3:ABC}
S = {ABC} , ~S = {A,AB,AC,B,BC,C}
Safe(B, T2): full-check → False (AC,BC,C tụt 13/28→2/5) ; reduced "chỉ ns⊆T2" → True (SAI)
```
> Sai lệch bất kỳ tập itemset nào = code sai. `Safe` phải kiểm **toàn bộ ~S** (fixture trên chứng minh
> vì sao "chỉ ns⊆T_k" hỏng).

### B.7 Prompt cho chính agent
Khi được giao việc: viết rõ phạm vi, output ra FILE, in 1 dòng xác nhận rồi DỪNG, nêu rõ "KHÔNG đụng
cái gì". Gặp điểm cần quyết định ngoài Q1–Q10 / SPEC §3 → DỪNG, ghi vào mục "CẦN QUYẾT ĐỊNH", không tự
quyết. Không bịa số; số nào cũng phải truy về output thật.
