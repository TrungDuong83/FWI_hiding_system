#!/usr/bin/env python3
"""IoT raw CSV -> transactional weighted DB (R1-R6), khớp format 7 dataset FIMI.
R1 categorical->item ; R2 continuous->10 equal-width bins->item ; R4 txn_key gộp giao dịch
(None => mỗi dòng 1 giao dịch) ; R5 qty=1 ; R6 weight uniform int[1,10] (file lưu NGUYÊN,
khớp 7-dataset; loader normalize=10 → [0.1,1.0]) seed cố định.
na_values: ô = missing (blank hoặc thuộc na_values[col]) => KHÔNG sinh item, KHÔNG tính vào range."""
import csv, json, random, argparse
from collections import defaultdict

def is_na(col, v, na):
    v=v.strip()
    return v=="" or v in na.get(col, [])

def discretize(rows, cfg, n_bins=10):
    cat=cfg["categorical"]; cont=cfg["continuous"]
    key=cfg.get("txn_key"); na=cfg.get("na_values",{})
    rng={}
    for c in cont:
        vals=[]
        for r in rows:
            if is_na(c, r.get(c,""), na): continue
            try: vals.append(float(r[c]))
            except: pass
        if vals: rng[c]=(min(vals),max(vals))
    def items(r):
        s=set()
        for c in cat:
            if not is_na(c, r.get(c,""), na): s.add(f"{c}={r[c].strip()}")
        for c in cont:
            if is_na(c, r.get(c,""), na) or c not in rng: continue
            try: x=float(r[c])
            except: continue
            lo,hi=rng[c]
            b=0 if hi==lo else min(max(int((x-lo)/(hi-lo)*n_bins),0),n_bins-1)
            s.add(f"{c}=bin{b}")
        return s
    txns=defaultdict(set)
    for i,r in enumerate(rows):
        k=tuple(r.get(c,"") for c in key) if key else i
        txns[k]|=items(r)
    tl=[s for s in txns.values() if s]
    allit=sorted({it for s in tl for it in s})
    iid={it:i+1 for i,it in enumerate(allit)}
    return tl, iid

def gen_weights(iid, seed=42):
    # KHỚP 7-dataset: file lưu weight NGUYÊN [1,10]; loader preprocess.load_weights(normalize=10)
    # chia /10 → [0.1,1.0]. (Script cũ viết /10.0 = 0.1..1.0 vào file → loader /10 lần nữa = 0.01..0.10,
    # lệch scale + phá use_fraction. Control precondition-3: sửa gen_weights cho khớp.)
    rnd=random.Random(seed)
    return {i: rnd.randint(1,10) for i in iid.values()}

def write(ds, tl, iid, w, outdir="."):
    with open(f"{outdir}/{ds}_quantities.txt","w") as f:
        for s in tl: f.write(" ".join(f"{i}:1" for i in sorted(iid[it] for it in s))+"\n")
    with open(f"{outdir}/{ds}_weights.txt","w") as f:
        for i in sorted(w): f.write(f"{i}:{w[i]}\n")
    json.dump({str(v):k for k,v in iid.items()}, open(f"{outdir}/{ds}_itemmap.json","w"), indent=0)
    return len(tl), len(iid)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for a in ["--csv","--ds","--cfg","--out"]: ap.add_argument(a)
    ap.add_argument("--bins",type=int,default=10); ap.add_argument("--seed",type=int,default=42)
    a=ap.parse_args(); a.out=a.out or "."
    rows=list(csv.DictReader(open(a.csv,newline='')))
    tl,iid=discretize(rows,json.load(open(a.cfg)),a.bins); w=gen_weights(iid,a.seed)
    nt,ni=write(a.ds,tl,iid,w,a.out)
    print(f"{a.ds}: {nt} giao dịch, {ni} item, {a.bins} bins, seed={a.seed}")
