# -*- coding: utf-8 -*-
"""analyze_bins.py — RULE non-discriminative (control): với MỖI cột continuous, đếm tỉ lệ giao dịch
của TỪNG bin; bin nào ≥99% #giao dịch ⇒ cột non-discriminative ⇒ đề xuất BỎ. Read-only.
Dùng: python3 analyze_bins.py <ds> <cfg> [<csv> để đếm dòng trùng theo Model,'Current Date Time']"""
import os, sys, json, csv
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DS, CFGP = sys.argv[1], sys.argv[2]
D = os.path.join(ROOT, "datasets")
cfg = json.load(open(CFGP))
q = [l.split() for l in open(f"{D}/{DS}_quantities.txt") if l.strip()]
im = json.load(open(f"{D}/{DS}_itemmap.json"))         # id -> "Feat=val"
ntxn = len(q)
# đếm #txn chứa mỗi item-id
idcount = Counter()
for toks in q:
    for t in toks:
        idcount[t.split(":")[0]] += 1
item2id = {v: k for k, v in im.items()}
THR = 0.99
print(f"=== {DS}: {ntxn} giao dịch — RULE bin ≥{THR:.0%} ⇒ non-discriminative ===")
drop = []
for c in cfg["continuous"]:
    bins = sorted([(it, iid) for it, iid in item2id.items() if it.startswith(c + "=bin")],
                  key=lambda x: int(x[0].split("bin")[1]))
    if not bins:
        print(f"  [{c}] KHÔNG có bin nào (mọi giá trị na?) ⇒ đề xuất BỎ"); drop.append(c); continue
    ratios = [(it.split("=")[1], idcount[iid] / ntxn) for it, iid in bins]
    mx = max(r for _, r in ratios)
    flag = mx >= THR
    if flag:
        drop.append(c)
    top = ", ".join(f"{b}={r:.4f}" for b, r in ratios)
    print(f"  [{c}] #bin={len(bins)} max_bin_ratio={mx:.4f} {'⇒ BỎ (≥99%)' if flag else 'giữ'} | {top}")
print(f"\nĐỀ XUẤT BỎ (non-discriminative): {drop if drop else '(none)'}")

# đếm dòng trùng theo (Model, Current Date Time) nếu có csv
if len(sys.argv) > 3:
    rows = list(csv.DictReader(open(sys.argv[3], newline='')))
    keys = [(r.get("Model", ""), r.get("Current Date Time", "")) for r in rows]
    kc = Counter(keys)
    dup = sum(v - 1 for v in kc.values() if v > 1)
    print(f"\n[dup] #dòng={len(rows)} #(Model,Current Date Time) distinct={len(kc)} #dòng trùng(thừa)={dup}")
