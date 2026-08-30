# HOÀN THIỆN FORMALISM + COMPLEXITY — V0, B2, B3, C1–C7

> **Tiếp nối** `CHUNG_MINH_A1_A3_C5.md`. Dựng trên bản thảo
> `HidingSFWI_Final_20082026_T_v3_4_Notracking.docx`.
> Quyết định đã chốt: escalation MCPriority = no-op; victim ∈ SFWI; **SFWI |X|≥2 (cấm singleton)**;
> tw=Σw/|T|; ws=Σtw(T⊇X)/W_total; FWI: ws≥ξ; trọng số dương ngặt; ScoreHFP=|SCov|×w;
> ScoreMCP=1/(|NSCov|+1).
> Con số tự tính bằng Python (Fraction). Trích pseudocode nguyên văn từ bản thảo.

---

## VIỆC 0 — CROSS-CHECK MÔ HÌNH SCORE ⚠️ **CHẠM VAN DỪNG**

### Đọc pseudocode (trích nguyên văn)

**HFPriority (Algorithm 1):**
```
2  While (exists s in S such that ws(s) ≥ ξ) do
3    T_sensitive = IdentifyTransactions(D, S)
4    Sort T_sensitive in descending order of tw
5    For each T_k in T_sensitive do
6      MaxScore = -1; VictimItem = null
7      CandidateItems = { i ∈ T_k | i ∈ S }
9      For each item v in CandidateItems do
10       Score_HFP(v) = |SCov(v)| * w(v)
11       If Score_HFP(v) > MaxScore then MaxScore=...; VictimItem=v
17     If VictimItem is not null then
18       Remove VictimItem from T_k
19       Update tw(T_k) and W_total
20       Update ws(s) for all s in S
21       IF (all s in S are hidden) break
```

**MCPriority (Algorithm 2):**
```
6  For each T_k in T_sensitive do
7    MaxScore=-1; VictimItem=null
8    CandidateItems = { i in T_k | i belongs to some s in S }
10   For each item v in CandidateItems do
12     NSCov(v) = CountNonSensitiveSets(v, ~S)
13     Score_MCP(v) = 1/(NSCov(v)+1)
14     If Score_MCP(v) > MaxScore then MaxScore=...; VictimItem=v
20   If VictimItem is not null then
21     Remove VictimItem from T_k
22     Update tw(T_k), W_total, and ws(s)
23     Update Inverted Index for VictimItem
24     If (all s in S are hidden) break
```

### Xác định mô hình
Score được tính cho **CẶP (item, giao dịch)**: victim item được **chọn lại trong mỗi giao dịch**
$T_k$ (vòng For dòng 5/6 → chọn VictimItem trong CandidateItems của **chính $T_k$** → xóa khỏi
$T_k$). **KHÔNG** phải "một victim item toàn cục xóa khỏi nhiều giao dịch". Thứ tự xử giao dịch:
HFPriority theo $tw$ giảm dần (dòng 4); MCPriority "order less critical" (dòng 5). Điều kiện dừng:
While theo $ws(s)\ge\xi$ + break sớm khi mọi $s$ đã giấu (dòng 21/24) — **không** xóa hết mọi giao
dịch, đúng như mô tả.

Điểm tinh tế: $Score_{HFP}(v)=|SCov(v)|\times w(v)$ dùng $|SCov(v)|$ **toàn cục** (số SFWI chứa
$v$), nhưng được **đánh giá lại trong ngữ cảnh từng $T_k$** (chỉ so giữa các candidate của $T_k$).
Vậy hàm score là của item, nhưng **quyết định** là per-(item,txn). Nhất quán, không mâu thuẫn ở
điểm này.

### ⚠️ BA MÂU THUẪN NGHIÊM TRỌNG giữa pseudocode và quyết định đã chốt

Đây là lý do chạm van dừng — pseudocode hiện tại **KHÔNG** phản ánh thiết kế mà A1/A3 đã chứng
minh quanh. Không tự sửa; báo cáo để bạn quyết.

**M1 — MCPriority pseudocode KHÔNG có bước veto.** Toàn bộ mô tả văn xuôi + A3.2 dựa trên "veto:
không xóa nếu làm NSFWI tụt dưới ξ" và "no-op khi mọi candidate bị veto". Nhưng Algorithm 2
**không có dòng nào kiểm tra side-effect trước khi xóa**: dòng 20–21 xóa VictimItem ngay khi
$\ne$ null, không có "If deletion causes any ns ∈ ~S to drop below ξ then skip". Dòng 19 chỉ là
comment "// Apply deletion with side-effect check" nhưng **thân không thực hiện check**. Hệ quả:
pseudocode hiện tại **có thể phá NSFWI** → MC>0, mâu thuẫn tuyên bố "MC=0 by design".

**M2 — Không có cơ chế no-op / full-pass-no-move.** A3.2 chứng minh termination dựa vào nhánh
"một full pass mọi candidate đều bị veto → break". Pseudocode không có khái niệm này (vì không có
veto). Vòng For dòng 6 luôn xóa 1 item mỗi $T_k$ có candidate. Nếu thêm veto (M1) mà **không** thêm
nhánh no-op, sẽ rơi đúng bẫy vòng lặp While vô hạn mà A3.2 cảnh báo.

**M3 — Ràng buộc "SFWI |X|≥2 (cấm singleton)" chưa xuất hiện trong bài.** Quyết định C5.2 đã chốt
cấm singleton, nhưng Problem Definition (§III.E) và Def 5 không nêu. Cần thêm giả định tường minh.

### Đề xuất pseudocode MCPriority đã vá (để bạn duyệt, KHÔNG tự áp)
```
3  While (exists s in S: ws(s) ≥ ξ) do
4    T_sensitive = IdentifyTransactions(D, S)
       movedThisPass = false
6    For each T_k in T_sensitive do
7      MaxScore=-1; VictimItem=null
8      CandidateItems = { i in T_k | i ∈ some s in S }
10     For each v in CandidateItems (by Score_MCP desc) do
12       NSCov(v)=CountNonSensitiveSets(v,~S)
13       Score_MCP(v)=1/(NSCov(v)+1)
+ + +    // VETO look-ahead: simulate deletion
+ + +    if deleting v from T_k keeps ws(ns) ≥ ξ for ALL ns ∈ ~S:
+ + +        VictimItem=v; break        // take first non-vetoed by score order
       End for
20     If VictimItem is not null then
21       Remove VictimItem from T_k; movedThisPass=true
22       Update tw(T_k), W_total, ws(s); Update Index
24       If (all s hidden) break
       End for
+ + + If (not movedThisPass) then break   // NO-OP escalation: full pass, all vetoed
27   End While
```

**VERDICT VIỆC 0: CẦN QUYẾT ĐỊNH** — pseudocode phải được cập nhật (M1+M2+M3) để khớp thiết kế đã
chốt; nếu không, mọi chứng minh A3.2/C5 và tuyên bố MC=0 không có cơ sở trong bài. Đề xuất vá ở
trên; chờ bạn duyệt trước khi đưa vào bản thảo.

---

## VIỆC B2 — COMPUTATIONAL COMPLEXITY

Ký hiệu: $m$=số giao dịch, $\ell$=độ dài giao dịch tối đa, $|I|$=số item, $|S|$=số SFWI,
$|{\sim}S|$=số NSFWI, $D$=tổng số item bị xóa (biến kết thúc). Cận: $D\le m\cdot\ell$.

**Giả định nêu rõ:** (i) test $X\subseteq T_k$ là $O(\ell)$ (dùng hash-set item trong giao dịch);
(ii) $|SCov(v)|$ = duyệt $S$, mỗi phép kiểm $v\in s$ là $O(1)$ → $O(|S|)$; $|NSCov(v)|$ tương tự
$O(|{\sim}S|)$; (iii) cập nhật $ws$ cho mọi $s$ là $O(|S|\cdot m)$ khi tính lại tử số (hoặc
$O(|S|)$ nếu duy trì tử số tăng dần — nêu cả hai).

### HFPriority — phân tích từng pha (mỗi iteration của While)
| Pha | Thao tác | Chi phí |
|-----|----------|---------|
| P1 | IdentifyTransactions: quét $m$ giao dịch, mỗi cái test $|S|$ tập, mỗi test $O(\ell)$ | $O(m\,\ell\,|S|)$ |
| P2 | Sort $T_{sensitive}$ theo $tw$ | $O(m\log m)$ |
| P3 | Vòng For $T_k$ ($\le m$): CandidateItems $O(\ell)$; với mỗi $v$ ($\le\ell$) tính $|SCov(v)|$ $O(|S|)$ | $O(m\,\ell\,|S|)$ |
| P4 | Cập nhật $tw,W_{total}$ $O(\ell)$; cập nhật $ws$ mọi $s$ | $O(|S|\,m)$ hoặc $O(|S|)$ (incremental) |

Mỗi iteration: $O(m\,\ell\,|S| + m\log m)$. Số iteration $\le D\le m\ell$.

$$\boxed{\text{HFPriority: } O\big(m\ell\cdot(m\,\ell\,|S| + m\log m)\big)=O(m^2\ell^2|S| + m^2\ell\log m).}$$

**Bottleneck:** P1+P3 (nhận diện giao dịch nhạy cảm + tính score) lặp lại mỗi iteration. Nếu duy
trì $T_{sensitive}$ và $|SCov|$ tăng dần thay vì tính lại, giảm được một bậc $m$ ở P1.

### MCPriority — cùng khung, thay $|SCov|$ ($O(|S|)$) bằng $|NSCov|$ ($O(|{\sim}S|)$)
Pha P3 thành $O(m\,\ell\,|{\sim}S|)$; thêm **P-veto**: mỗi candidate mô phỏng xóa rồi kiểm mọi
NSFWI bị ảnh hưởng. NSFWI bị ảnh hưởng bởi xóa $v$ khỏi $T_k$ là các $ns$ mà $ns\subseteq T_k$
(giới hạn, $\le|{\sim}S|$), mỗi phép tính $ws(ns)$ mới là $O(1)$ nếu duy trì tử số/mẫu tăng dần,
hoặc $O(m)$ nếu tính lại. Veto: $O(\ell\cdot|{\sim}S|)$ per $T_k$ (incremental) → $O(m\ell|{\sim}S|)$.

$$\boxed{\text{MCPriority: } O\big(m\ell\cdot(m\,\ell\,|{\sim}S| + m\log m)\big)=O(m^2\ell^2|{\sim}S| + m^2\ell\log m).}$$

**Bottleneck:** tính $|NSCov|$ + veto look-ahead. Vì $|{\sim}S|\gg|S|$ thông thường (NSFWI nhiều
hơn SFWI nhiều), **MCPriority đắt hơn HFPriority một hệ số $|{\sim}S|/|S|$** — khớp quan sát RT
trong §V (MCPriority chậm hơn).

### Đối chiếu inverted index (Def 11)
Index tăng tốc **bước lấy tập giao dịch chứa item** (cover computation) — thay vì quét lại $D$
($O(m)$) thì tra $ID(v)$ trực tiếp. Nó **KHÔNG** giảm bậc của việc **liệt kê $|{\sim}S|$** để đếm
$NSCov$. Nói cách khác: index cải thiện **hằng số / một hệ số $m$** ở bước cover, không đổi bậc
tổng theo $|{\sim}S|$. (Xem B3 để phát biểu chính xác.)

**Verify (đếm thao tác trên bộ chuẩn):** $m=6,\ell=4,|S|=2,|{\sim}S|=7,|FWI|=9$. Kích thước cover
đã tính: cover(C)=5, cover(CE)=4, cover(AC)=4… (khớp mô hình P1/P3 quét theo $m$). Cấu trúc chi
phí mô phỏng khớp các pha trên.

**VERDICT B2: ĐÃ XONG** (Big-O chặt, nêu rõ giả định + bottleneck; không bịa hằng số).

---

## VIỆC B3 — SỬA CLAIM O(1) CỦA DEF 11

**Sai hiện tại:** "The time complexity of the lookup operation is reduced from $O(N)$ to $O(1)$."
Trộn hai thao tác khác bậc.

**Phân tách chính xác:**
- **O(1):** truy xuất **con trỏ tới danh sách** $ID(i)$ (tra hash-map theo item $i$). Đây là cái
  duy nhất $O(1)$.
- **O(|ID(i)|):** đọc/duyệt danh sách TID của $i$ (độ dài = số giao dịch chứa $i$, tối đa $m$).
- **KHÔNG O(1):** tính $|NSCov(v)|$ = đếm số NSFWI chứa $v$ → cần duyệt $\sim S$: $O(|{\sim}S|)$
  (có thể nhân $\ell$ nếu kiểm bao). Index **không** rút gọn bước này.
- **O(|ID(v)|) hoặc O(1) amortized:** cập nhật index sau khi xóa $v$ khỏi $T_k$ = xóa 1 TID khỏi
  $ID(v)$ (nếu dùng cấu trúc cho phép xóa $O(1)$, vd doubly-linked / hash-set) → $O(1)$; nếu mảng
  thì $O(|ID(v)|)$.

**Câu thay đề xuất cho Def 11:**
> "By employing the inverted index, retrieving the transaction list $ID(i)$ of an item is done in
> $O(1)$ (a single hash-map lookup), replacing a full database scan of cost $O(m)$. Traversing that
> list costs $O(|ID(i)|)\le O(m)$. Note that computing $|NSCov(v)|$ still requires enumerating the
> non-sensitive itemsets containing $v$, at cost $O(|{\sim}S|)$; the index accelerates the cover
> retrieval but not this enumeration. Updating the index after a deletion removes one TID from
> $ID(v)$ in $O(1)$ (amortized, with a hash-based list)."

**VERDICT B3: ĐÃ XONG.**

---

## VIỆC C1 — DEF 6 ĐỊNH NGHĨA VÒNG

**Sai hiện tại:** "A victim transaction $T_v$, where the deletion of $v$ reduces the weight
$tw(T_v)$, consequently decreasing the support of SFWI." — mâu thuẫn Theorem 1 (xóa item nhẹ làm
**tăng** tw) và trộn định nghĩa với hiệu ứng.

**Câu thay đề xuất (trung tính):**
> **Definition 6 (Victim Item and Victim Transaction).** A *victim item* $v$ is an item selected
> for deletion from a transaction in order to remove that transaction's contribution to a sensitive
> itemset. A *victim transaction* $T_v$ is a transaction chosen for modification, i.e. one that
> contains at least one sensitive itemset ($SCov(T_v)\ne\varnothing$). The quantitative effect of
> deleting $v$ on $tw(T_v)$ and on $ws$ is characterized separately by Theorem 1 and Lemma [A1].

Tách bạch: định nghĩa nói **cái gì được chọn**, Theorem/Lemma nói **hiệu ứng**. **VERDICT C1: ĐÃ
XONG.**

---

## VIỆC C2 — DEF 10 OVERCLAIM

**Sai hiện tại:** "deleting items with higher weights … results in the **maximum reduction** in the
average transaction weight $tw$." — vô điều kiện; theo Theorem 1, $\Delta=(tw-w(v))/(|T|-1)$, giảm
tw nhiều nhất chỉ khi $w(v)>tw$, và xóa item nặng nhất cho $\Delta$ **âm nhất** chỉ trong các lựa
chọn hiện có.

**Câu thay đề xuất (tương đối + có điều kiện):**
> "Deleting an item with a larger unit weight tends to produce a more negative $\Delta$
> (Theorem 1), i.e. a larger decrease in $tw(T_k)$ **when** $w(v)>tw(T_k)$. Processing items in
> decreasing weight order therefore prioritizes, **among the available candidates**, those whose
> removal drives $tw$ down fastest, helping reach the hiding condition sooner. (When every candidate
> has $w(v)<tw(T_k)$, deletion still proceeds but $tw$ may rise; the ordering only sets relative
> priority, not an absolute guarantee.)"

**VERDICT C2: ĐÃ XONG.**

---

## VIỆC C3 — CẦU NỐI PARADOX → SCORE + LÀM RÕ BẢN CHẤT ẨN FWI

**Đoạn đề xuất cho §IV (chèn giữa Theorem 1 và định nghĩa Score):**

> **From the paradox to the scoring function.** Theorem 1 shows that removing an item $v$ from a
> victim transaction changes $tw$ by $\Delta=(tw(T_k)-w(v))/(|T_k|-1)$. Two levers follow directly.
> First, to push the weighted support of a sensitive itemset $X$ down as sharply as possible in one
> deletion, one should remove an item of **large unit weight** $w(v)$: by Lemma [A1], deleting
> $v\in X$ strips $tw(T_k)$ from the numerator of $ws(X)$, and a larger $w(v)$ maximizes the
> immediate drop. Second, to reduce the exposure of **as many** sensitive itemsets as possible per
> deletion, one should remove an item that lies in the **largest number of sensitive itemsets**,
> i.e. one with large $|SCov(v)|$. Combining both levers multiplicatively yields
> $Score_{HFP}(v)=|SCov(v)|\times w(v)$: an item is a strong victim when it is both heavy and
> broadly shared across sensitive itemsets. MCPriority inverts the second lever toward preservation,
> ranking by $1/(|NSCov(v)|+1)$ so that items shared by many *non-sensitive* itemsets are avoided.

> **Two clarifications specific to FWI hiding.** (i) *Hiding means $ws(X)<\xi$, not
> $\mathrm{count}=0$.* An itemset is hidden once its weighted support falls below the threshold; the
> itemset may still occur in the database. This differs from removing the pattern entirely. (ii)
> *A single deletion ripples through every itemset via $W_{total}$.* Because $ws(X)=\mathrm{num}(X)/
> W_{total}$ and $W_{total}$ is a global normalizer, editing one transaction shifts the denominator
> for **all** itemsets at once — including non-sensitive ones (the source of artificial cost). This
> global coupling is absent in classical frequent-itemset hiding, where support is a local count;
> it is precisely what makes FWI hiding non-monotone and motivates the look-ahead in MCPriority.

**VERDICT C3: ĐÃ XONG** (nối chặt paradox→score qua Lemma A1; làm rõ hai điểm phân biệt FWI vs
FIM hiding).

---

## VIỆC C4 — DOWNWARD CLOSURE SAU SANITIZATION

**Câu xác nhận đề xuất:**
> "Downward closure of FWIs is preserved on the sanitized database $\mathcal{D'}$. The property
> 'if $ws(X)\ge\xi$ then $ws(Y)\ge\xi$ for all $Y\subseteq X$' (Vo–Coenen–Le, 2013) is a structural
> property of *any* weighted transaction database, derived solely from the definitions of $tw$ and
> $ws$; it does not depend on how $\mathcal{D'}$ was obtained. Item deletion produces another valid
> weighted database, on which the closure therefore still holds. Consequently, mining $FWI(\mathcal
> {D'})$ to compute the AC and MC metrics is well-defined."

**Lập luận ngắn:** downward closure là hệ quả trực tiếp của định nghĩa ws (đơn điệu theo bao hàm),
đúng cho mọi database — sanitization chỉ tạo ra một database khác, không phá tính chất. **VERDICT
C4: ĐÃ XONG.**

---

## VIỆC C6 — DEF/§IV.B NHẤT QUÁN NSCov

Các chỗ nhắc $|NSCov|$ với giá trị cụ thể trong bài, và bối cảnh $S$ tương ứng:

| Vị trí | Giá trị nêu | Bối cảnh S ngầm | Cần ghi rõ? |
|--------|-------------|-----------------|-------------|
| Def 8 / Example 4 | $\|NSCov(D)\|=4$, $\|NSCov(E)\|=1$ | $S=\{\{A,C\},\{C,E\}\}$ (⇒ ~S 7 phần tử) | **CÓ** |
| §IV.B Min-Side ví dụ | $\|NSCov(C)\|=3$, $\|NSCov(E)\|=1$ | $S=\{\{A,C\},\{C,E\}\}$ | **CÓ** |
| §IV.D Running example | $\|NSCov(C)\|=4$, $\|NSCov(E)\|=1$ | $S=\{\{C,E\}\}$ (⇒ ~S khác) | **CÓ** |

Ba chỗ dùng **hai bối cảnh $S$ khác nhau** nên $|NSCov(C)|$ hợp lệ khác nhau (3 khi $S$ có cả
$\{A,C\}$; 4 khi $S$ chỉ có $\{C,E\}$ vì lúc đó $\{A,C\}\in{\sim}S$). Không sai, nhưng reviewer đọc
lướt sẽ tưởng mâu thuẫn.

**Đề xuất:** thêm cụm định bối cảnh ở mỗi chỗ, ví dụ:
- Def 8/Ex4: "…for the sensitive set $S=\{\{A,C\},\{C,E\}\}$, $|NSCov(D)|=4$…"
- Running example: "…**for this running example where $S=\{\{C,E\}\}$**, $|NSCov(C)|=4$…"

**VERDICT C6: ĐÃ XONG** (đề xuất câu; áp là chỉnh sửa cơ học).

---

## VIỆC C7 — HFPRIORITY/MCPRIORITY KHÔNG CLAIM TỐI ƯU

**Câu tuyên bố đề xuất (đặt cuối §IV, sau pseudocode):**
> "Both HFPriority and MCPriority are **greedy heuristics**. Lemma [A1] guarantees that each
> deletion moves the weighted support of the targeted sensitive itemset in the correct direction,
> and the potential-function argument [A3] guarantees termination, but neither algorithm claims
> **global optimality**: finding a minimum-cardinality set of deletions that achieves $ws(s)<\xi$
> for all sensitive itemsets while minimizing side effects is a combinatorial optimization problem
> that is NP-hard in general, by analogy with the known NP-hardness of optimal sanitization in
> frequent-itemset hiding [Atallah et al., 1999]. The proposed scores are efficient surrogates that
> trade optimality for scalability."

**Về lập luận NP-hardness:** không dựng chứng minh đầy đủ ở đây (cần reduction cẩn thận từ một bài
NP-hard chuẩn như vertex cover / hitting set sang FWI-deletion — đây là công trình riêng, không
gói gọn trong một đoạn). Bài chỉ cần **tuyên bố heuristic + tham chiếu** kết quả NP-hardness của
sanitization trong FIM hiding (Atallah et al. 1999 là nguồn kinh điển). Nếu muốn khẳng định
NP-hardness *cho chính bài toán FWI-deletion* thì đó là claim cần chứng minh riêng → xem CẦN QUYẾT
ĐỊNH.

**VERDICT C7: ĐÃ XONG** (tuyên bố heuristic + tham chiếu; NP-hardness chặt cho FWI-deletion để
ngỏ, xem dưới).

---

## CẦN QUYẾT ĐỊNH

**[V0] Cập nhật pseudocode để khớp thiết kế đã chốt (BẮT BUỘC, nghiêm trọng nhất).**
Pseudocode MCPriority hiện **không có veto và không có no-op**, mâu thuẫn trực tiếp với tuyên bố
MC=0 và với các chứng minh A3.2/C5. Ba việc cần bạn duyệt:
1. **M1** — thêm bước veto look-ahead trước khi xóa (đề xuất đã cho ở VIỆC 0).
2. **M2** — thêm nhánh no-op `if (not movedThisPass) break`.
3. **M3** — thêm giả định "SFWI $|X|\ge2$" vào Def 5 / §III.E.
→ Đây không phải quyết định thẩm mỹ mà là **sửa để bài tự nhất quán**. Cần bạn xác nhận dùng bản
vá đề xuất hay có cách trình bày khác.

**[C7] Có muốn chứng minh NP-hardness CHẶT cho bài toán FWI-deletion không?**
Hiện đề xuất chỉ **tuyên bố heuristic + tham chiếu** kết quả FIM. Nếu bạn muốn một Theorem
NP-hardness riêng cho FWI-deletion (mạnh hơn, chặn phản biện "sao biết NP-hard cho *bài này*"),
cần dựng reduction — đây là quyết định phạm vi (tốn công, có thể là đóng góp lý thuyết phụ). Không
tự quyết; nếu bạn muốn, mở việc riêng để dựng + verify reduction.

---

## TÓM TẮT

| Việc | Nội dung | Verdict |
|------|----------|---------|
| **V0** | Cross-check mô hình score | Mô hình = per-(item,txn), điều kiện dừng đúng; **CẦN QUYẾT ĐỊNH** (pseudocode thiếu veto+no-op+cấm singleton) |
| **B2** | Complexity HFPriority $O(m^2\ell^2\|S\|+m^2\ell\log m)$; MCPriority thay $\|S\|→\|{\sim}S\|$ | **ĐÃ XONG** |
| **B3** | Sửa O(1): chỉ lookup $ID(i)$ là O(1); $\|NSCov\|$ là $O(\|{\sim}S\|)$ | **ĐÃ XONG** |
| **C1** | Def 6 trung tính (tách hiệu ứng sang Theorem/Lemma) | **ĐÃ XONG** |
| **C2** | Def 10 bỏ "maximum reduction" vô điều kiện | **ĐÃ XONG** |
| **C3** | Cầu nối paradox→score + phân biệt FWI vs FIM hiding | **ĐÃ XONG** |
| **C4** | Downward closure giữ trên D' | **ĐÃ XONG** |
| **C6** | Ghi rõ bối cảnh S ở mỗi chỗ nêu $\|NSCov\|$ | **ĐÃ XONG** |
| **C7** | Tuyên bố heuristic + tham chiếu NP-hardness | **ĐÃ XONG**; NP-hardness chặt cho FWI-deletion **CẦN QUYẾT ĐỊNH** |

**Điểm cần bạn hành động:** (1) **V0** — duyệt bản vá pseudocode MCPriority (veto + no-op + cấm
singleton); đây là mâu thuẫn nghiêm trọng nhất, mọi tuyên bố MC=0 phụ thuộc vào nó. (2) **C7** —
quyết có dựng NP-hardness riêng hay chỉ tham chiếu.

**Nhắc lại giả định phải giữ:** trọng số dương ngặt (cho A1) + SFWI $|X|\ge2$ (cho C5.2) — cả hai
cần nêu tường minh trong phần định nghĩa của bản thảo.
