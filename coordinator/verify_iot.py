# -*- coding: utf-8 -*-
"""verify_iot.py — VERIFY OUTPUT IoT (trước calibrate). Read-only. python3 verify_iot.py <ds> <csv> <cfg>"""
import os, sys, json, csv
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DS, CSVP, CFGP = sys.argv[1], sys.argv[2], sys.argv[3]
D = os.path.join(ROOT, "datasets")
cfg = json.load(open(CFGP)); na = cfg.get("na_values", {})

q = [l.rstrip("\n") for l in open(f"{D}/{DS}_quantities.txt")]
w = {l.split(":")[0]: l.split(":")[1].strip() for l in open(f"{D}/{DS}_weights.txt") if l.strip()}
im = json.load(open(f"{D}/{DS}_itemmap.json"))
print(f"=== {DS} ===")
print(f"n_txn={len(q)}  n_item={len(im)}  n_weight={len(w)}")

# qty=1
bad_qty = [ln for ln in q if any(p.split(':')[1] != '1' for p in ln.split())]
print(f"[qty=1] all qty=1: {not bad_qty}")
# empty lines
print(f"[no-empty] no empty txn line: {all(ln.strip() for ln in q)}")
# weights int 1..10
wint = all(v.isdigit() and 1 <= int(v) <= 10 for v in w.values())
print(f"[weight] all int in [1,10]: {wint}  distinct={sorted(set(int(v) for v in w.values()))}")
# item in quantities all have weight
qids = set(p.split(':')[0] for ln in q for p in ln.split())
print(f"[coverage] every quantity-item has weight: {qids <= set(w)}  (n_qids={len(qids)})")
print(f"[coverage] every weight-item in itemmap: {set(w) <= set(im)}")
# avg len
tl = [len(ln.split()) for ln in q]
print(f"[avg-len] avg items/txn={sum(tl)/len(tl):.2f} min={min(tl)} max={max(tl)}")

# -1 / na leak: recompute từ CSV
rows = list(csv.DictReader(open(CSVP, newline='')))
print(f"[rows] csv data rows={len(rows)}  vs n_txn={len(q)}  (row=txn: match={len(rows)==len(q) or len(rows)>=len(q)})")
def is_na(c, v):
    v = (v or "").strip(); return v == "" or v in na.get(c, [])
# với continuous có na (Lat/Long): số row có giá trị hợp lệ == số item bin nên item xuất hiện; -1 KHÔNG sinh
item2id = {v: k for k, v in im.items()}
for c in cfg["continuous"]:
    if c not in na:  # chỉ cột có na (-1)
        continue
    valid = sum(1 for r in rows if not is_na(c, r.get(c, "")))
    nas = sum(1 for r in rows if is_na(c, r.get(c, "")))
    # đếm txn có bất kỳ item c=binX
    cbins = [iid for it, iid in item2id.items() if it.startswith(c + "=bin")]
    txn_with_c = sum(1 for ln in q if any(p.split(':')[0] in cbins for p in ln.split()))
    print(f"[na-check {c}] valid_rows={valid} na/-1_rows={nas} | txn_with_{c}_item={txn_with_c} "
          f"→ -1 không lọt: {txn_with_c <= valid} (bins={sorted(it for it in item2id if it.startswith(c+'=bin'))})")

# hằng số: item xuất hiện trong MỌI giao dịch (cột hằng)
idcount = Counter(p.split(':')[0] for ln in q for p in ln.split())
const_items = [(iid, im[iid], cnt) for iid, cnt in idcount.items() if cnt == len(q)]
print(f"[constant] item có mặt MỌI {len(q)} giao dịch (cột hằng — cần báo control nếu có): "
      f"{[(im[i],c) for i,_,c in [(a,b,c) for a,b,c in const_items]]}" if const_items else "[constant] none ✓")

# format vs retail (byte pattern)
r0 = open(f"{D}/retail_quantities.txt").readline().split()[0]
print(f"[format] quantity token pattern: sample='{q[0].split()[0]}' retail='{r0}' (id:1 form: {':1' in q[0].split()[0] or q[0].split()[0].endswith(':1')})")
