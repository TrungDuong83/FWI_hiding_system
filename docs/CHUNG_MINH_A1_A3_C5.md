# HOÀN THIỆN CHỨNG MINH — A1 (Monotonicity), A3 (Termination), C5 (Edge cases)

> **Phạm vi:** dựng chứng minh chặt quanh quyết định thiết kế ĐÃ CHỐT (không đổi):
> escalation MCPriority = **no-op minh bạch**; victim BẮT BUỘC ∈ SFWI đang xét;
> tw=Σw/|T|; ws=Σtw(T⊇X)/W_total; FWI: ws≥ξ; ScoreHFP=|SCov|×w; ScoreMCP=1/(|NSCov|+1).
> **Trọng số dương ngặt** (theo Vo–Coenen–Le 2013: "positive weights") — giả định này được
> dùng trong chứng minh A1 và phải giữ trong bài.
> **Mọi con số dưới đây tự tính bằng Python** (Fraction, không sai số nổi), có mã kèm.
>
> Bộ chuẩn: W={A:0.9,B:0.4,C:0.7,D:0.5,E:0.2}; T1=ACDE,T2=BCE,T3=ACD,T4=ABCE,T5=ACDE,T6=BDE;
> W_total=3.200; ξ=0.55; FWI={A,C,D,E,AC,AD,CD,CE,ACD}; S={{A,C},{C,E}};
> ~S={{A},{C},{D},{E},{A,D},{C,D},{A,C,D}}.

---

## A1 — LEMMA ĐƠN ĐIỆU (victim ∈ S là điều kiện cần)

### Ký hiệu
Cho SFWI $X$, giao dịch $T_k \in \mathrm{cover}(X)$ (tức $X\subseteq T_k$), $n=|T_k|>1$. Đặt:
- $tw_k = tw(T_k)$ (trước xóa), $\mathrm{num}(X)=\sum_{T\supseteq X} tw(T)$, $W=W_{total}$.
- Sau khi xóa item $v$ khỏi $T_k$: $tw'_k = tw(T_k\setminus\{v\})$,
  $\Delta = tw'_k - tw_k = \dfrac{tw_k - w(v)}{n-1}$ (Theorem 1).

### Bổ đề A1 (Monotonicity of in-itemset deletion)
> **Giả thiết:** mọi trọng số dương ngặt ($w(i)>0\ \forall i$). Cho SFWI $X$ và
> $T_k\in\mathrm{cover}(X)$ với $|T_k|>1$. Nếu victim $v\in X$, thì $T_k$ **mất** quan hệ bao
> $X$ (vì $v\notin T_k\setminus\{v\}$), tử số giảm đúng $tw_k$:
> $\mathrm{num}'(X)=\mathrm{num}(X)-tw_k$, và mẫu số $W'=W+\Delta$. Khi đó
> $$ws'(X) < ws(X)\quad\textbf{luôn đúng (giảm ngặt).}$$

### Chứng minh
Vì $v\in X\subseteq T_k$ nên sau khi xóa, $X\not\subseteq T_k\setminus\{v\}$: $T_k$ rời khỏi
$\mathrm{cover}(X)$, do đó $\mathrm{num}'(X)=\mathrm{num}(X)-tw_k$. Các giao dịch khác trong
$\mathrm{cover}(X)$ không đổi. Mẫu số đổi đúng lượng $\Delta$ do chỉ $T_k$ bị sửa:
$W'=W-tw_k+tw'_k=W+\Delta$. Ta cần $\dfrac{\mathrm{num}(X)-tw_k}{W+\Delta}<\dfrac{\mathrm{num}(X)}{W}$.

Cả hai mẫu dương ($W>0$; $W+\Delta = W-tw_k+tw'_k>0$ vì $tw'_k\ge0$ và các giao dịch khác giữ
tw dương). Nhân chéo:
$$W(\mathrm{num}-tw_k) < \mathrm{num}(W+\Delta)
\iff -W\,tw_k < \mathrm{num}\,\Delta
\iff \mathrm{num}\,\Delta + W\,tw_k > 0. \tag{$\star$}$$

**Chặn ($\star$) luôn dương.** Viết $tw_k=\frac{w(v)+r}{n}$ với $r=\sum_{i\in T_k\setminus\{v\}}w(i)>0$
(dương ngặt vì $n>1$ và trọng số dương). Khi đó
$\Delta=\frac{tw_k-w(v)}{n-1}=\frac{r-(n-1)w(v)}{n(n-1)}$, và cận dưới của $\Delta$ đạt khi $r\to0^+$:
$\Delta > -\frac{w(v)}{n}$. Suy ra $|\Delta| < \frac{w(v)}{n}$ khi $\Delta<0$. Mặt khác
$tw_k=\frac{w(v)+r}{n} > \frac{w(v)}{n} > |\Delta|$. Vì $T_k\in\mathrm{cover}(X)$ nên $tw_k$ là
**một** trong các số hạng của $\mathrm{num}(X)$, do đó $\mathrm{num}(X)\ge tw_k$; đồng thời
$\mathrm{num}(X)\le W$ (tổng con của tổng toàn bộ tw dương). Kết hợp:
$$\mathrm{num}\,\Delta + W\,tw_k \ge -\mathrm{num}\,|\Delta| + W\,tw_k
> -W\cdot\tfrac{w(v)}{n} + W\,tw_k = W\big(tw_k-\tfrac{w(v)}{n}\big)=W\cdot\tfrac{r}{n} > 0.$$
Với $\Delta\ge0$ (item nhẹ, $w(v)\le tw_k$): ($\star$) hiển nhiên $>0$. Vậy ($\star$) đúng trong
mọi trường hợp ⟹ $ws'(X)<ws(X)$ **ngặt**. $\blacksquare$

### Đối chiếu: victim $v\notin X$ KHÔNG đảm bảo giảm
Nếu $v\notin X$ nhưng $X\subseteq T_k$, sau khi xóa $v$ ta vẫn có $X\subseteq T_k\setminus\{v\}$:
$T_k$ **giữ** quan hệ bao, $\mathrm{num}(X)$ **không mất** $tw_k$ mà chỉ đổi thành
$\mathrm{num}(X)+\Delta$. Nếu $v$ nhẹ ($\Delta>0$) thì cả tử lẫn mẫu cùng tăng $\Delta$, và
$\frac{\mathrm{num}+\Delta}{W+\Delta}>\frac{\mathrm{num}}{W}$ khi $\mathrm{num}<W$ (luôn đúng nếu
có ≥1 giao dịch ngoài cover) ⟹ $ws(X)$ **tăng**. Đây chính là phản ví dụ số.

### Verify (Python, Fraction — chính xác tuyệt đối)
```python
from fractions import Fraction as F; import copy; from itertools import combinations
W={'A':F(9,10),'B':F(4,10),'C':F(7,10),'D':F(5,10),'E':F(2,10)}
T0={1:set('ACDE'),2:set('BCE'),3:set('ACD'),4:set('ABCE'),5:set('ACDE'),6:set('BDE')}
xi=F(55,100)
def tw(s): return sum(W[i] for i in s)/len(s) if s else F(0)
def Wtot(Td): return sum(tw(Td[k]) for k in Td if Td[k])
def ws(X,Td): X=set(X); return sum(tw(Td[k]) for k in Td if X<=Td[k])/Wtot(Td)
FWI=[frozenset(c) for r in range(1,6) for c in combinations(sorted(W),r) if ws(c,T0)>=xi]
# v in X: exhaustively check STRICT decrease over all FWI, all v in X, all cover txns |T|>1
allpass=all(ws(X,{**T0,k:T0[k]-{v}})<ws(X,T0)
            for X in FWI for v in X for k in T0 if X<=T0[k] and len(T0[k])>1)
# v NOT in X: count increases
inc=sum(1 for X in FWI for k in T0 if X<=T0[k] and len(T0[k])>1
        for v in T0[k]-set(X) if ws(X,{**T0,k:T0[k]-{v}})>ws(X,T0))
```
**Kết quả chạy:**
- `v in X: ws(X) STRICTLY DECREASES in ALL cases = True`
- Phản ví dụ điểm: S={A,C}, xóa **C∈X** khỏi T1 → ws(AC) **0.7500 → 0.5778** (giảm);
  xóa **E∉X** khỏi T1 → ws(AC) **0.7500 → 0.7594** (TĂNG). (Khớp con số bài đưa.)
- Quét v∉X trên bộ chuẩn: **40 lần tăng / 30 giảm / 3 giữ nguyên** ⟹ xóa ngoài X **không** đảm
  bảo giảm.
- **Monte-Carlo** 200,000 cấu hình trọng số dương ngẫu nhiên ($n\in[2,7]$, cover/non-cover ngẫu
  nhiên): **0 lần** ($\star$) sai ⟹ bổ đề bền, không chỉ đúng trên bộ chuẩn.

### Kết luận A1
Bổ đề chứng minh **victim ∈ X là điều kiện đủ để $ws(X)$ giảm ngặt**, và phản ví dụ cho thấy
victim ∉ X **không** đủ. Đây là biện minh đúng đắn (correctness invariant) cho ràng buộc
`CandidateItems ∈ S` trong cả hai pseudocode: chỉ xóa item thuộc chính SFWI mới bảo đảm mỗi thao
tác đẩy support đi đúng hướng. **VERDICT: ĐÃ XONG.**

---

## A3 — TERMINATION (tính dừng)

### Mệnh đề A3.1 (HFPriority dừng)
> Với victim ∈ S và trọng số dương, HFPriority kết thúc sau hữu hạn bước, số iteration của vòng
> `While` bị chặn trên bởi $\sum_{i}\mathrm{occ}_S(i)$ = tổng số lần xuất hiện của các item-thuộc-S
> trong toàn CSDL (hữu hạn).

**Chứng minh.** Mỗi iteration xóa đúng **một** item $v\in s\subseteq S$ khỏi **một** giao dịch
$T_k$ mà trước đó chứa $v$. Định nghĩa hàm thế năng
$\Phi(D)=\sum_{k}|\{i\in T_k : i\in\bigcup_{s\in S}s\}|$ = tổng số vị trí (giao dịch × item-của-S)
còn tồn tại. $\Phi$ nguyên, không âm, và mỗi iteration làm $\Phi$ **giảm đúng 1** (xóa 1 vị trí,
không bao giờ thêm — thuật toán chỉ xóa). Do $\Phi\ge0$ và giảm ngặt mỗi bước, số iteration
$\le\Phi(D_0)<\infty$. Điều kiện thoát `While` (không còn SFWI lộ) chỉ có thể đến sớm hơn.
$\blacksquare$

*(Không cần dùng A1 cho termination — chỉ cần tính đơn điệu của $\Phi$. A1 đảm bảo tiến-độ-đúng-hướng,
$\Phi$ đảm bảo hữu hạn. Hai thứ độc lập.)*

### Mệnh đề A3.2 (MCPriority với no-op dừng)
> Với escalation no-op đã chốt, MCPriority kết thúc sau hữu hạn bước. Mỗi iteration hoặc (a) xóa
> ≥1 item ⟹ $\Phi$ giảm ngặt, hoặc (b) một **full pass** qua mọi candidate mà mọi lựa chọn đều bị
> veto ⟹ `break` (no-op). Không nhánh nào lặp vô hạn.

**Chứng minh.** Xét một iteration. Thuật toán duyệt toàn bộ candidate
$(s\text{ lộ},\ T_k\in\mathrm{cover}(s),\ v\in s)$ theo thứ tự $ScoreMCP$ giảm dần, thử từng cái:
- Nếu **tồn tại** một candidate mà xóa không làm NSFWI nào tụt dưới $\xi$ (không bị veto): thực
  hiện xóa, $\Phi$ giảm đúng 1. Trường hợp (a).
- Nếu **mọi** candidate đều bị veto: đây là full-pass-no-move ⟹ `break`. Trường hợp (b).

Trường hợp (a) chỉ xảy ra hữu hạn lần ($\le\Phi(D_0)$). Trường hợp (b) xảy ra **nhiều nhất một
lần** rồi thuật toán dừng. Do đó tổng số iteration $\le\Phi(D_0)+1<\infty$. $\blacksquare$

### Ghi chú termination vs timeout
Cả hai mệnh đề cho **điều kiện dừng logic** (potential-function + full-pass-no-move). Timeout
3600s trong §V **không phải** cơ chế termination hợp lệ — nó chỉ là giới hạn tài nguyên; phải
loại bỏ vai trò "đảm bảo dừng" của timeout và dựa vào A3.1/A3.2. (Timeout vẫn có thể giữ như biện
pháp an toàn kỹ thuật, nhưng KHÔNG được viện dẫn như lý do thuật toán kết thúc.)

### Verify (mô phỏng trên bộ chuẩn)
```python
# HFPriority: victim=argmax SCov(v)*w(v) over exposed sensitive, tie-break higher tw txn.
# MCPriority: try candidates by 1/(NSCov+1) desc; delete first NON-VETOED; else full-pass -> break.
```
**Kết quả chạy (bộ chuẩn, S={{A,C},{C,E}}):**
- **HFPriority:** iterations=**2**, deletions=**2**, SFWI còn lộ = **[]** (giấu hết). Dừng đúng
  bằng điều kiện `While`.
- **MCPriority (no-op):** iterations=**3**, deletions=**2**, SFWI còn lộ = **[{A,C}]**,
  NSFWI vỡ = **[]** ⟹ **MC=0** (không NSFWI nào tụt dưới ξ), **HF>0** ({A,C} để lộ). Dừng bằng
  full-pass-no-move (no-op) đúng như thiết kế đã chốt.

### Kết luận A3
Cả hai thuật toán dừng, có hàm thế năng $\Phi$ chặn trên số iteration; MCPriority no-op có thêm
lối thoát full-pass-no-move. Timeout bị loại khỏi vai trò termination. **VERDICT: ĐÃ XONG.**

---

## C5 — TRƯỜNG HỢP BIÊN

### C5.1 — $S=\varnothing$: **XÁC NHẬN, không cần sửa**
Điều kiện `While (∃ s∈S: ws(s)≥ξ)` sai ngay từ đầu ⟹ vòng không chạy ⟹ trả $D$ nguyên vẹn.
HF=MC=AC=0. Nên thêm một câu khẳng định trong bài (hành vi đúng, hiện chưa nêu tường minh).

### C5.2 — $|T_k|=1$ và item đó là victim ∈ S: **CHẠM VAN DỪNG → xem "CẦN QUYẾT ĐỊNH"**
**Khi nào phát sinh:** một giao dịch độ dài 1, $T_k=\{i\}$, chỉ bao itemset **singleton** $X=\{i\}$.
Với $|X|\ge2$, mọi giao dịch bao $X$ đều có $|T_k|\ge2$ ⟹ **biên này chỉ xảy ra khi SFWI là một
singleton $\{i\}$ và tồn tại giao dịch bằng đúng $\{i\}$.** (Đã kiểm logic.)

Theorem 1 loại $|T_k|=1$ (mẫu $n-1=0$, chia 0). Nhưng **thuật toán** vẫn có thể gặp: xóa $i$ khỏi
$\{i\}$ ⟹ giao dịch **rỗng**. Có ≥2 cách xử hợp lý cho kết quả **ws giống nhau về số** (tw của
giao dịch rỗng = 0 trong cả hai) nhưng **khác về $|D|$ và ngữ nghĩa** — đây là điểm cần quyết định
thiết kế nằm NGOÀI phạm vi đã chốt, nên **không tự chọn**. Ghi ở mục CẦN QUYẾT ĐỊNH.

Verify (ví dụ nhỏ DB={ {C}, {A,C}, {A,C,D} }, xóa C khỏi T1):
- Option A (xóa hẳn giao dịch rỗng khỏi $D$): còn 2 giao dịch; ws(AC)=1.0; **$|D|$ giảm còn 2**.
- Option B (giữ giao dịch rỗng, tw=0): $W_{total}=1.5$; ws(AC)=1.0; **$|D|$ vẫn =3**.
- Kết quả ws **trùng nhau** (0 đóng góp tw), nhưng $|D|$ khác ⟹ ảnh hưởng mọi thước đo chuẩn hóa
  theo $|D|$ và ý nghĩa "giao dịch".

### C5.3 — Mọi item cùng trọng số $c$: **XÁC NHẬN suy biến, không sai**
$tw(T)=c$ hằng với mọi giao dịch. $ScoreHFP(v)=|SCov(v)|\times c$ ⟹ xếp hạng **chỉ theo
$|SCov(v)|$**, thành phần trọng số mất tác dụng phân biệt. Kiểm số: c=0.5 ⟹ tw(ABC)=tw(AB)=0.5.
Không sai, chỉ **thoái hóa** về tiêu chí phủ thuần. Nên nêu một câu trong bài.

### C5.4 — Item chỉ xuất hiện 1 giao dịch: **XÁC NHẬN ca cực đoan**
Xóa item đó khỏi giao dịch duy nhất chứa nó ⟹ xóa toàn bộ cover của **mọi** itemset chứa nó (item
biến mất khỏi $D$). Hợp lệ nhưng cực đoan — nếu item này ∈ nhiều NSFWI, MCPriority sẽ veto mạnh
(dễ rơi vào no-op). Nên nhắc như tình huống biên đáng lưu ý cho phân tích thực nghiệm.

---

## CẦN QUYẾT ĐỊNH

**[C5.2] Cách xử giao dịch trở nên rỗng sau khi xóa item cuối (chỉ phát sinh với SFWI singleton
$\{i\}$ và giao dịch $=\{i\}$).** Hai phương án đều hợp lý, kết quả ws trùng nhau về số nhưng khác
$|D|$ và ngữ nghĩa:

| | Option A — Xóa giao dịch rỗng khỏi $D$ | Option B — Giữ giao dịch rỗng, $tw=0$ |
|---|---|---|
| $W_{total}$ | không đổi (tw rỗng=0) | không đổi (tw rỗng=0) |
| $|D|$ (số giao dịch) | **giảm 1** | giữ nguyên |
| ws mọi itemset | như nhau | như nhau |
| Metric chuẩn hóa theo $|D|$ | bị ảnh hưởng | không |
| Ngữ nghĩa | "giao dịch biến mất" | "giao dịch trống tồn tại" |
| So với dữ liệu gốc Vo2013 | gốc không định nghĩa giao dịch rỗng | gốc không định nghĩa giao dịch rỗng |

→ **Cần bạn chốt A hay B.** Gợi ý cân nhắc (không tự quyết): nếu bài có bất kỳ metric nào chuẩn
hóa theo $|D|$ (hoặc so sánh số giao dịch trước/sau) thì Option A làm lệch $|D|$; Option B an toàn
hơn về so sánh nhưng đưa vào khái niệm "giao dịch rỗng" mà dữ liệu gốc không có. Một lối thứ ba:
**cấm SFWI singleton** ở tiền xử lý (nêu rõ giả định "sensitive itemsets có $|X|\ge2$") — khi đó
biên C5.2 không bao giờ phát sinh và không cần chọn A/B. Ba lựa chọn này đều là quyết định của
bạn.

---

## TÓM TẮT

| Việc | Nội dung | Verdict |
|------|----------|---------|
| **A1** | Lemma đơn điệu: victim∈X ⟹ ws(X) giảm ngặt (chứng minh tổng quát + Monte-Carlo 200k + phản ví dụ v∉X) | **ĐÃ XONG** |
| **A3** | Termination HFPriority (potential $\Phi$) + MCPriority no-op (full-pass-no-move); loại timeout khỏi vai trò dừng; mô phỏng khớp | **ĐÃ XONG** |
| **C5.1** | $S=\varnothing$ → trả $D$ nguyên | ĐÃ XONG (xác nhận) |
| **C5.2** | $|T_k|=1$, victim singleton → giao dịch rỗng | **CẦN QUYẾT ĐỊNH** (A/B/cấm singleton) |
| **C5.3** | Mọi trọng số bằng nhau → suy biến về $|SCov|$ | ĐÃ XONG (xác nhận) |
| **C5.4** | Item ở 1 giao dịch → xóa toàn cover | ĐÃ XONG (xác nhận) |

**Điểm cần bạn hành động:** chỉ **C5.2** (chọn cách xử giao dịch rỗng, hoặc cấm SFWI singleton).
Mọi phần còn lại đã chứng minh chặt và verify bằng Python (Fraction, không sai số).

**Giả định phải giữ trong bài để A1 đứng vững:** trọng số **dương ngặt** ($w(i)>0$). Nếu bài cho
phép $w(i)=0$, chứng minh A1 cần bổ sung điều kiện (khi $r=0$ bất đẳng thức thành đẳng thức, mất
tính giảm ngặt). Vo–Coenen–Le 2013 dùng "positive weights" nên giả định này khớp gốc — chỉ cần
**nêu tường minh** một lần trong phần định nghĩa.
