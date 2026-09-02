# SPEC_BASELINE.md — Baseline PPUM cho §V (FWI-deletion) — v2

> **Phạm vi:** baseline SOTA độc lập cho bài "Efficient Methods for Hiding FWI" (IoT-63257-2026).
> Baseline = **cặp MSU-MAU + MSU-MIU** (Lin, Wu, Fournier-Viger, Lin, Zhan, Voznak, EAAI 55, 2016),
> port sang $tw/ws$, **giữ nguyên nguyên lý thuật toán**, chỉ đổi thao tác thành *item deletion*.
> **Quyết định đã chốt (Trung):** dùng cả cặp; nguyên lý bất biến, chỉ biến đổi cho hợp $tw/ws$.
> **v2:** viết lại theo **Algorithm 1/2 nguyên văn** (đã có fulltext EAAI 2016). Mọi số verify `Fraction`.

---

## 0. VERDICT (chiếu 3 tiêu chí handoff)

| Ứng viên | Victim item rule | (a) khác HFP/MCP? | (b) port? | (c) không circular? | KL |
|---|---|---|---|---|---|
| **MSU-MSI** | $\max\|SCov\|$ (max sensitive conflict) | **FAIL** = HFPriority bỏ term $w$ (ablation) | (moot) | chạm circular | **LOẠI** |
| **MSU-MAU** | $\max w(i)$ trong $X$ | PASS (magnitude-only) | PASS | PASS (SOTA cite) | **DÙNG** |
| **MSU-MIU** | $\min w(i)$ trong $X$ | PASS | PASS | PASS | **DÙNG** |

MSU-MSI loại: victim-rule $\arg\max_i|SCov(i)|$ **chính là** $\text{Score}_{HFP}=|SCov|\cdot w$ bỏ thừa số
$w$ → reviewer đọc thành ablation của HFPriority, không phải competitor độc lập.

---

## 1. NGUỒN & CẤU TRÚC GỐC (Algorithm 1/2, EAAI 2016)

Lin, T.-Y. Wu, P. Fournier-Viger, G. Lin, J. Zhan, M. Voznak (2016), *Fast algorithms for hiding
sensitive high-utility itemsets in privacy-preserving utility mining*, EAAI **55**: 269–284,
DOI `10.1016/j.engappai.2016.07.003`. Có fulltext (Alg 1 = MSU-MAU, Alg 2 = MSU-MIU).

Cấu trúc chung (cả hai Alg, đọc từ pseudocode):
- **Preprocessing (lines 1–5):** xây `iTable` (projection); với mỗi SFWI tính $f(i_j)$ = occurrence
  frequency của item, sort → **"overlapping weight"**; **duyệt SFWI theo overlapping weight giảm dần**.
- **Hiding loop:** với mỗi SFWI, lặp chọn *victim transaction* rồi *victim item*, xóa/giảm-qty tới khi ẩn.
  - **Victim transaction = "maximum sensitive utility"** $\arg\max u(s_d,T_d)$:
    - **MAU (Alg1 l.9):** re-select **động** trong `while` mỗi vòng.
    - **MIU (Alg2 l.11):** **sort tĩnh MỘT LẦN** $D_{s_d}$ theo $u(s_d,T_d)$ giảm dần, rồi duyệt tuần tự.
  - **Victim item trong $T^{vic}$:** MAU (l.10) $=\max u(i_k,T^{vic})$; MIU (l.14) $=\min$.
  - Nhánh **delete** khi $u(i^{vic},T^{vic})<du$; ngược lại nhánh **giảm quantity** (l.15–18 / l.21–24).

**3-tầng:** *What* = 2-tầng (txn max-sensitive-utility + item max/min utility). *Why* = xóa item nào
trong SFWI cũng cho **cùng hiệu ứng ẩn**; MIU chọn item nhẹ để giảm mất mát utility, MAU chọn item nặng.
*Trade-off* = MAU vs MIU khác nhau ở nhiễu gây cho non-sensitive qua dịch chuyển mẫu số chung $W_{total}$
(§5). Cả hai **không** cân nhắc non-sensitive cover tường minh (khác MCPriority).

---

## 2. ADAPTATION SANG $ws/tw$ (ba bất biến — port bị ép duy nhất, không tùy tiện)

Framework khóa: $tw(T)=\frac{\sum_{i\in T}w(i)}{|T|}$; $ws(X)=\frac{\sum_{T\supseteq X}tw(T)}{W_{total}}$,
$W_{total}=\sum_T tw(T)$; **FWI $\iff ws\ge\xi$**; victim $\in X$, $|X|\ge2$; thao tác = **xóa item**.

1. **Victim item thành hằng theo SFWI.** HUIM: $u(i,T)=q(i,T)\cdot pr(i)$ phụ thuộc giao dịch → chọn
   per-transaction (Alg l.10/14). FWI **không quantity** ⇒ $u(i,T)\equiv w(i)\ \forall T$ ⇒
   $v^*(X)=\arg\max_{i\in X}w(i)$ (MAU) hoặc $\arg\min$ (MIU), **bất biến qua giao dịch** → precompute 1 lần.
2. **"Max sensitive utility" transaction $\to\max tw(T)$.** Đóng góp của $T$ vào $ws(X)$ đúng bằng
   $tw(T)/W_{total}$; xóa $v\in X$ khỏi $T$ làm $T$ rời $cover(X)$, giảm tử số đúng $tw(T)$. Vậy giao dịch
   giảm $ws(X)$ mạnh nhất/vòng = $\arg\max_{T\in cover(X)}tw(T)$. (KHÔNG port thành $\sum_{i\in X}w(i)/|T|$.)
3. **Nhánh giảm-quantity biến mất → dùng test $ws\ge\xi$ trực tiếp.** Vì không có quantity, luôn rơi vào
   nhánh **delete**; bookkeeping $du=u(s_d)-\delta$ (HUIM artifact, xấp xỉ) được thay bằng test **exact**
   $ws(X)\ge\xi$ mỗi vòng. Port trung thực và chặt hơn bản gốc.

*Overlapping weight:* $f(i)$ trong Alg l.3 = "occurrence frequency" — bản OCR không nói rõ là tần suất
trong DB hay overlap giữa SFWI. Chọn nghĩa khớp thuật ngữ "overlapping weight" = $|SCov(i)|$ (số SFWI
chứa $i$); overlapping weight của SFWI $= \sum_{i\in X}|SCov(i)|$. Chỉ dùng cho **thứ tự duyệt**, KHÔNG
đụng victim-rule (danh tính thuật toán) → an toàn; ghi rõ ở §6/§7.

---

## 3. PSEUDOCODE (adapted, trung thực với Alg 1/2)

**Preprocessing dùng chung (Alg 1/2, lines 1–5):**
```
f(i) ← |SCov(i)| = #{X ∈ S : i ∈ X}                    # occurrence frequency
owt(X) ← Σ_{i∈X} f(i)                                  # overlapping weight
sort S giảm dần theo owt  (tie: ws(X) desc; tie: lexicographic)
```

**MSU-MAU-ws  (faithful Alg 1: DYNAMIC max-tw):**
```
for each X in sorted S:
    v* ← argmax_{i∈X} w(i)                 # max item utility; tie: item-id nhỏ
    while ws(X) ≥ ξ:                       # thay cho du>0; test exact (backend: round(ws,3)≥ξ)
        cover ← { T ∈ D : X ⊆ T }
        T*   ← argmax_{T ∈ cover} tw(T)     # RE-SELECT ĐỘNG mỗi vòng (Alg1 l.9); tie: TID nhỏ
        D[T*] ← D[T*] \ {v*}                # xóa item
return D
```

**MSU-MIU-ws  (faithful Alg 2: STATIC pre-sort):**
```
for each X in sorted S:
    if ws(X) < ξ: continue                 # Alg2 l.6-8
    v* ← argmin_{i∈X} w(i)                 # min item utility; tie: item-id nhỏ
    cover_sorted ← sort { T ∈ D : X ⊆ T } giảm dần theo tw(T)   # SORT TĨNH 1 LẦN (Alg2 l.11); tie TID nhỏ
    for T* in cover_sorted:
        if ws(X) < ξ: break
        if X ⊆ D[T*]: D[T*] ← D[T*] \ {v*}
return D
```

- Bất đối xứng MAU(động)/MIU(tĩnh) là **theo đúng bản gốc**, không được đồng nhất hóa.
- **KHÔNG** re-mine, **KHÔNG** Safe()/no-op, **KHÔNG** né non-sensitive — giữ nguyên bản chất baseline.
- Chấm dứt: mỗi lần xóa $v^*\in X$ ⇒ $T^*$ rời $cover(X)$ ⇒ $ws(X)$ giảm ngặt (Lemma A1) ⇒ hữu hạn bước.
- `iTable`/projection = speedup tùy chọn (không đổi kết quả, chỉ RT).

---

## 4. CÔNG BẰNG (Q10)

- Cùng dataset, cùng $\xi$ (calibrate), cùng 4 metric (HF/MC/AC/RT), **cùng deadline 2h/dataset**.
- Baseline được phép HF/MC/AC > 0. **KHÔNG** thêm safe-check/no-op của ta.
- **RT một nguồn:** chạy baseline trên **cùng máy** (c2-standard-16 on-demand) như HFP/MCP; không reuse số cũ.

---

## 5. GOLDEN VERIFICATION (Fraction-exact; verify với cấu trúc trung thực Alg 1/2)

Bộ chuẩn: $W$={A:.9,B:.4,C:.7,D:.5,E:.2}; T1=ACDE,T2=BCE,T3=ACD,T4=ABCE,T5=ACDE,T6=BDE; $W_{total}=3.2$;
$\xi=0.55$; FWI(9)={A,C,D,E,AC,AD,CD,CE,ACD}; $S$={AC,CE}; $\sim\!S$=7. $|SCov|$: A=1,C=2,E=1.
$owt$(AC)=$owt$(CE)=3 (tie) → tie-break ws: AC(.75) trước CE(.667). Victim: MAU{AC:A,CE:C}; MIU{AC:C,CE:E}.

| Method | trace (golden) | HF | #MC | #AC | $W_{total}:3.2\to$ |
|---|---|---|---|---|---|
| **MSU-MAU** | `A@T3 → C@T1` | 0 | 4 `{A,AD,CD,ACD}` | 0 | **3.058 ↓** (heavy → mẫu số↓) |
| **MSU-MIU** | `C@T3 → E@T1` | 0 | 2 `{CD,ACD}` | 0 | **3.325 ↑** (light → mẫu số↑) |
| HFPriority (ta) | `C@T3 → C@T1` | 0 | 3 `{C,CD,ACD}` | 0 | 3.158 |
| MCPriority safe=T (ta) | `E@T1→C@T2→C@T4` no-op | resid `{AC}` | 0 | 0 | — |

**Non-collapse gate: PASS** — trace MAU/MIU ≠ HFPriority & MCPriority.
(Golden mỗi itemset ẩn sau 1 lần xóa nên khác biệt động/tĩnh chưa lộ — chỉ hiện trên dữ liệu thật.)

**HAI CẢNH BÁO TRUNG THỰC (bắt buộc khi viết §V):**
1. **Golden KHÔNG chứng minh contrast AC** — cả 4 method AC=0 (DB 5-item quá đặc). Contrast AC là
   **empirical** (chess/mushroom/IoT). Cơ chế golden xác nhận qua chiều $W_{total}$: **MAU heavy →
   $W_{total}\downarrow$ → regime sinh AC**; **MIU light → $W_{total}\uparrow$ → regime sinh MC**.
   → Cặp MAU+MIU **bracket đẹp** hai failure-mode qua đúng Weight Transformation.
2. **Baseline không yếu tầm thường** — golden MSU-MIU MC(2) < HFPriority MC(3). Mạnh/yếu là empirical;
   **KHÔNG viết trước** khi có số §V.

> Đính chính handoff: "MSU-MIU xóa item nhẹ → AC↑" **sai chiều**. Item nhẹ kéo $W_{total}\uparrow$ ⇒ hạ
> $ws$ chuẩn hóa ⇒ **MC↑**, không phải AC. Regime AC↑ là MSU-MAU (heavy).

---

## 6. TIÊU CHÍ VERIFY (gate cho `baseline_ppum.py`)

1. **Golden trace khớp §5** (Fraction, cả MAU & MIU) — 2 vòng sạch liên tiếp.
2. **Non-collapse:** golden trace ≠ HFPriority & ≠ MCPriority (safe=T/F).
3. **Cấu trúc trung thực:** MAU = re-max **động** trong while; MIU = sort tw-desc **tĩnh 1 lần** rồi duyệt.
   Kiểm bằng fixture: itemset cần ≥2 lần xóa trên dữ liệu nhỏ → MAU và MIU có thể chọn transaction thứ 2
   khác nhau (động vs tĩnh) — nếu code cho cùng thứ tự ở cả hai ⇒ sai (đồng nhất hóa nhầm).
4. **Invariance:** $v^*(X)$ precompute 1 lần == tính per-$T^{vic}$ (bất biến 1).
5. **Order-không-đụng-rule:** đổi định nghĩa $f(i)$ (DB-freq vs $|SCov|$) chỉ được đổi **thứ tự**, KHÔNG
   đổi victim-item rule; assert victim của mỗi $X$ bất biến với lựa chọn $f$.
6. **Fairness guard:** module KHÔNG gọi Safe()/no-op; luôn xóa tới $ws(X)<\xi$ hoặc hết deadline; nhánh
   giảm-quantity KHÔNG tồn tại (assert).
7. **Metric parity:** HF/MC/AC = $\alpha/\beta/\gamma$ chuẩn (Bertino 2005; EAAI Def 1/2/3 = Lin survey
   Def 4/5/6), AC denom = $|FWI(\text{san})|$; dùng chung code metric với HFP/MCP.
8. **Deterministic:** seed cố định; tie item-id/TID/lexicographic tăng dần; chạy lại y hệt.

---

## 7. TRẠNG THÁI ĐIỂM CHỜ

- **[ĐÃ GIẢI QUYẾT] Thứ tự duyệt SFWI:** bài gốc quy định = **overlapping weight giảm dần** (Alg l.2–5),
  không còn là chọn tùy ý. Tie-break ws-desc rồi lexicographic (deterministic).
- **[GHI CHÚ, không cản] Định nghĩa $f(i)$:** OCR mơ hồ (DB-freq vs $|SCov|$). Chọn $|SCov|$ (khớp
  "overlapping weight"); trên golden hai cách đều tie ⇒ trace như nhau. Verify gate #5 chặn rủi ro.
- **[XÁC NHẬN] Projection** = speedup tùy chọn; **không** ảnh hưởng HF/MC/AC, chỉ RT.

**Mang về control:** verdict (§0) + spec trung thực Alg 1/2 (§1–4) + golden Fraction (§5) + gates (§6).
Control tích hợp PLAN → calibrate $\xi$ per dataset → §V (3 cấu hình ta + MAU + MIU). Execution: `baseline_ppum.py`.
