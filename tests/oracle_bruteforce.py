"""
oracle_bruteforce.py — Independent brute-force FWI miner (G6 oracle).

MỤC ĐÍCH: nguồn chân lý ĐỘC LẬP để kiểm engine SWU-N-list (PART 3) sau khi vá.
KHÔNG import engine. Tính ws TRỰC TIẾP từ giao dịch bằng level-wise Apriori
(anti-monotone của ws) + giao tidset. Dùng trong tests/test_g6.py.

Định nghĩa FWI (khớp bài, Def 1–4, cite [15]):
    tw(T)   = ( Σ_{i∈T} w(i) ) / |T|          # KHÔNG quantity
    W_total = Σ_T tw(T)
    ws(X)   = ( Σ_{T⊇X} tw(T) ) / W_total
    X là FWI  ⟺  ws(X) ≥ ξ
"""
from itertools import combinations


def load_transactions_from_file(filepath):
    """Đọc file '<item>:<qty> ...' -> {tid: set(item)}. qty BỎ QUA (FWI, qty=1)."""
    D = {}
    with open(filepath, "r") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            items = set()
            for part in line.split():
                items.add(part.split(":")[0] if ":" in part else part)
            if items:
                D[f"T{i+1}"] = items
    return D


def load_weights_from_file(filepath):
    """Đọc file '<item>:<w>' hoặc '<item>,<w>' -> {item: float(w)}."""
    W = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.replace(",", ":").split(":")
            if len(parts) >= 2:
                W[parts[0]] = float(parts[1])
    return W


def brute_force_fwi(D, W, xi, maxlen=7, tol=1e-12):
    """
    D: {tid: set(item)} ; W: {item: weight} ; xi: ngưỡng ws.
    Trả về: set(frozenset(itemset)) gồm mọi X với ws(X) >= xi (tới độ dài maxlen).
    Level-wise Apriori: an toàn vì ws đơn điệu giảm theo bao hàm.
    """
    tset = {t: set(s) for t, s in D.items() if s}
    tw = {t: sum(W.get(i, 0.0) for i in s) / len(s) for t, s in tset.items()}
    sumtw = sum(tw.values())
    if sumtw == 0:
        return set()

    tid_of = {}                          # item -> set(tid)
    for t, s in tset.items():
        for i in s:
            tid_of.setdefault(i, set()).add(t)

    def ws_of(tids):
        return sum(tw[t] for t in tids) / sumtw

    FWI = set()
    # L1
    cur = {}
    for i, tids in tid_of.items():
        if ws_of(tids) >= xi - tol:
            cur[(i,)] = tids
            FWI.add(frozenset((i,)))

    k = 2
    while cur and k <= maxlen:
        prev = set(cur.keys())
        keys = list(cur.keys())
        cands = set()
        for a in range(len(keys)):
            for b in range(a + 1, len(keys)):
                u = tuple(sorted(set(keys[a]) | set(keys[b])))
                if len(u) == k:
                    cands.add(u)
        nxt = {}
        for c in cands:
            # apriori prune: mọi (k-1)-subset phải là frequent
            if any(tuple(x for x in c if x != drop) not in prev for drop in c):
                continue
            tids = set.intersection(*(tid_of[i] for i in c))
            if not tids:
                continue
            if ws_of(tids) >= xi - tol:
                nxt[c] = tids
                FWI.add(frozenset(c))
        cur = nxt
        k += 1
    return FWI


def per_len(fwi_set):
    d = {}
    for x in fwi_set:
        d[len(x)] = d.get(len(x), 0) + 1
    return dict(sorted(d.items()))


# --------------------------- SELF-TESTS ---------------------------
def _selftest():
    ok = True

    # Golden running example (ξ=0.55) — kỳ vọng 9 tập
    W = {"A": 0.9, "B": 0.4, "C": 0.7, "D": 0.5, "E": 0.2}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    got = {"".join(sorted(x)) for x in brute_force_fwi(D, W, 0.55)}
    exp = {"A", "C", "D", "E", "AC", "AD", "CD", "CE", "ACD"}
    print(f"[golden] #{len(got)} match={got == exp} diff={got ^ exp}")
    ok &= got == exp

    # Safe fixture (ξ=11/25) — kỳ vọng 7 tập (có ABC)
    Wf = {"A": 0.4, "B": 0.1, "C": 0.8, "D": 0.4}
    Df = {"T1": set("AB"), "T2": set("BD"), "T3": set("ABC")}
    got2 = {"".join(sorted(x)) for x in brute_force_fwi(Df, Wf, 11 / 25)}
    exp2 = {"A", "B", "C", "AB", "AC", "BC", "ABC"}
    print(f"[fixture] #{len(got2)} match={got2 == exp2} diff={got2 ^ exp2}")
    ok &= got2 == exp2

    print("SELFTEST", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        # Dùng: python oracle_bruteforce.py <trans_file> <weight_file> <xi>
        D = load_transactions_from_file(sys.argv[1])
        W = load_weights_from_file(sys.argv[2])
        fwi = brute_force_fwi(D, W, float(sys.argv[3]))
        print(f"#FWI={len(fwi)} per_len={per_len(fwi)}")
    else:
        _selftest()
