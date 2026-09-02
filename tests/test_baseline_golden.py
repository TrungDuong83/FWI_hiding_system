# -*- coding: utf-8 -*-
"""
tests/test_baseline_golden.py — Gates G-B1…G-B7 cho baseline_ppum (SPEC_BASELINE §5/§6).
Backend Fraction (exact). Entry-guarded; exit != 0 nếu FAIL.

G-B1 Golden trace exact  : MAU A@T3→C@T1 (HF=0, MC=4/7 {A,AD,CD,ACD}, AC=0);
                           MIU C@T3→E@T1 (HF=0, MC=2/7 {CD,ACD}, AC=0).
G-B2 Non-collapse        : MAU/MIU ≠ HFPriority & ≠ MCPriority(safe=T/F).
G-B3 Động vs tĩnh        : fixture 1 SFWI cần ≥2 xóa → MAU 2 lần / MIU 1 lần (khác transaction thứ 2).
G-B4 Invariance victim   : v*(X) bất biến qua giao dịch & độc lập f (chỉ đổi thứ tự duyệt).
G-B5 Fairness guard      : không Safe()/no-op; luôn xóa tới ws<ξ (HF=0); chỉ xóa item (không quantity).
G-B6 Metric parity       : HF/MC/AC = đúng code metric dùng chung; AC denom = |FWI(san)|.
G-B7 Deterministic       : chạy lại y hệt.
"""
import os
import sys
import logging
import inspect
from fractions import Fraction as F

logging.disable(logging.CRITICAL)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for d in ("hiding", "metrics", "mining", "datautil"):
    sys.path.insert(0, os.path.join(ROOT, "src", d))

import baseline_ppum                                                      # noqa: E402
from baseline_ppum import run_msu_mau, run_msu_miu, victim_item, preprocess_order  # noqa: E402
from common import HidingDB                                              # noqa: E402
from hfpriority import hfpriority                                        # noqa: E402
from mcpriority import mcpriority                                        # noqa: E402
import metrics                                                          # noqa: E402
from metrics import hiding_failure, missing_cost, artificial_cost, is_frequent  # noqa: E402
from miner import mine_fwi, fwi_itemsets                                # noqa: E402

# ---- Running example ----
W = {"A": F(9, 10), "B": F(4, 10), "C": F(7, 10), "D": F(5, 10), "E": F(2, 10)}
D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
     "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
XI = F(55, 100)
S = [frozenset("AC"), frozenset("CE")]
NS = [frozenset(x) for x in ["A", "C", "D", "E", "AD", "CD", "ACD"]]
Wf = {k: float(v) for k, v in W.items()}


def _trace_str(tr):
    return [f"{v}@{t}" for v, t in tr]


def _ac(db_D):
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db_D, Wf, 0.55))
    return artificial_cost(fwi_orig, fwi_san)


def _run(fn):
    db = HidingDB(D, W)
    tr = fn(db, S, XI)
    return db, _trace_str(tr)


def test_gb1_golden():
    ok = True
    # MAU
    db, tr = _run(run_msu_mau)
    hf, mc, ac = hiding_failure(db, S, XI), missing_cost(db, NS, XI), _ac(db.D)
    lost = sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), XI))
    okm = (tr == ["A@T3", "C@T1"] and hf == F(0) and mc == F(4, 7)
           and lost == ["A", "ACD", "AD", "CD"] and ac == F(0))
    print(f"[G-B1 MAU] trace={' -> '.join(tr)} HF={hf} MC={mc} lost={lost} AC={ac} ok={okm}")
    # MIU
    db, tr = _run(run_msu_miu)
    hf, mc, ac = hiding_failure(db, S, XI), missing_cost(db, NS, XI), _ac(db.D)
    lost = sorted("".join(sorted(ns)) for ns in NS if not is_frequent(db.ws(ns), XI))
    oki = (tr == ["C@T3", "E@T1"] and hf == F(0) and mc == F(2, 7)
           and lost == ["ACD", "CD"] and ac == F(0))
    print(f"[G-B1 MIU] trace={' -> '.join(tr)} HF={hf} MC={mc} lost={lost} AC={ac} ok={oki}")
    ok = okm and oki
    print("G-B1", "PASS" if ok else "FAIL")
    return ok


def test_gb2_noncollapse():
    _, mau = _run(run_msu_mau)
    _, miu = _run(run_msu_miu)
    db = HidingDB(D, W); hfp = _trace_str(hfpriority(db, S, XI))
    db = HidingDB(D, W); mcpT = _trace_str(mcpriority(db, S, NS, XI, safe_check=True))
    db = HidingDB(D, W); mcpF = _trace_str(mcpriority(db, S, NS, XI, safe_check=False))
    others = [hfp, mcpT, mcpF]
    ok = (mau not in others) and (miu not in others) and (mau != miu)
    print(f"[G-B2] MAU={mau} MIU={miu} | HFP={hfp} MCP_T={mcpT} MCP_F={mcpF} ok={ok}")
    print("G-B2", "PASS" if ok else "FAIL")
    return ok


def test_gb3_dynamic_vs_static():
    # Fixture: 1 SFWI={AB} cần ≥2 xóa; MAU (xóa A nặng, W_total↓) cần 2 lần, MIU (xóa B nhẹ,
    # W_total↑) chỉ 1 lần ⇒ transaction thứ 2 KHÁC nhau (MAU:T2 ; MIU: không có) ⇒ không đồng nhất.
    Wg = {"A": F(8, 10), "B": F(2, 10), "C": F(2, 10)}
    Dg = {"T1": set("AB"), "T2": set("ABC"), "T3": set("C")}
    Sg = [frozenset("AB")]
    xi = F(2, 5)
    dbm = HidingDB(Dg, Wg); mau = _trace_str(run_msu_mau(dbm, Sg, xi))
    dbi = HidingDB(Dg, Wg); miu = _trace_str(run_msu_miu(dbi, Sg, xi))
    ok = (mau == ["A@T1", "A@T2"] and miu == ["B@T1"] and mau != miu
          and len(mau) == 2 and len(miu) == 1)
    print(f"[G-B3] MAU={mau} (2 xóa, txn2=T2) MIU={miu} (1 xóa, không txn2) khác={mau != miu} ok={ok}")
    print("G-B3", "PASS" if ok else "FAIL")
    return ok


def test_gb4_invariance():
    db = HidingDB(D, W)
    # (a) v*(X) bất biến qua giao dịch: tính trước và sau vài lần xóa → không đổi.
    vmax_before = {("".join(sorted(X))): victim_item(X, db.W, "max") for X in S}
    vmin_before = {("".join(sorted(X))): victim_item(X, db.W, "min") for X in S}
    db.delete("C", "T3"); db.delete("A", "T1")            # thay đổi DB tùy ý
    vmax_after = {("".join(sorted(X))): victim_item(X, db.W, "max") for X in S}
    ok_inv = (vmax_before == vmax_after)
    # (b) độc lập f: đổi f (DB-freq) chỉ đổi THỨ TỰ, victim mỗi X bất biến.
    db2 = HidingDB(D, W)
    f_dbfreq = {i: sum(1 for t in db2.D if i in db2.D[t]) for i in db2.W}
    order_scov = ["".join(sorted(X)) for X in preprocess_order(db2, S)]
    order_dbf = ["".join(sorted(X)) for X in preprocess_order(db2, S, f=f_dbfreq)]
    vmax_scov = {("".join(sorted(X))): victim_item(X, db2.W, "max") for X in S}
    ok_f = (vmax_scov == vmax_before)          # victim không phụ thuộc f
    print(f"[G-B4] v*max before={vmax_before} after={vmax_after} inv={ok_inv} ; "
          f"v*min={vmin_before} ; order|SCov|={order_scov} order_dbfreq={order_dbf} victim_f_indep={ok_f}")
    ok = ok_inv and ok_f
    print("G-B4", "PASS" if ok else "FAIL")
    return ok


def test_gb5_fairness():
    # (a) module KHÔNG import/định nghĩa Safe/no-op.
    no_safe = not hasattr(baseline_ppum, "is_safe")
    src = inspect.getsource(baseline_ppum)
    # thân code (bỏ docstring) không có 'no-op' logic hay giảm-quantity — kiểm bằng behavior + không import.
    # (b) behavior: luôn ẩn hết (HF=0) + CHỈ xóa item (Σ|D| giảm đúng len(trace), không đổi quantity).
    ok = no_safe
    for fn in (run_msu_mau, run_msu_miu):
        db = HidingDB(D, W)
        before = sum(len(db.D[t]) for t in db.D)
        tr = fn(db, S, XI)
        after = sum(len(db.D[t]) for t in db.D)
        hf = hiding_failure(db, S, XI)
        pure_delete = (before - after == len(tr))       # mỗi bước xóa đúng 1 item, không quantity
        ok = ok and (hf == F(0)) and pure_delete
        print(f"[G-B5 {fn.__name__}] HF={hf} (exp 0) items_removed={before - after}=={len(tr)}=len(trace) "
              f"pure_item_delete={pure_delete}")
    print(f"[G-B5] no Safe/no-op import: {no_safe}")
    print("G-B5", "PASS" if ok else "FAIL")
    return ok


def test_gb6_metric_parity():
    # HF/MC/AC dùng ĐÚNG code metric dùng chung (import từ metrics), AC denom=|FWI(san)|.
    shared = (hiding_failure.__module__ == "metrics"
              and missing_cost.__module__ == "metrics"
              and artificial_cost.__module__ == "metrics")
    db, _ = _run(run_msu_mau)
    fwi_orig = fwi_itemsets(mine_fwi(D, Wf, 0.55))
    fwi_san = fwi_itemsets(mine_fwi(db.D, Wf, 0.55))
    ac_metric = artificial_cost(fwi_orig, fwi_san)
    # denom = |FWI(san)|: tái tạo bằng tay
    phantom = fwi_san - fwi_orig
    ac_manual = F(len(phantom), len(fwi_san)) if fwi_san else F(0)
    ok = shared and (ac_metric == ac_manual)
    print(f"[G-B6] metric funcs from 'metrics'={shared} ; AC={ac_metric} == |phantom|/|FWI(san)|="
          f"{len(phantom)}/{len(fwi_san)}={ac_manual} ok={ok}")
    print("G-B6", "PASS" if ok else "FAIL")
    return ok


def test_gb7_determinism():
    ok = True
    for fn in (run_msu_mau, run_msu_miu):
        r1 = _run(fn); r2 = _run(fn)
        m1 = (r1[1], hiding_failure(r1[0], S, XI), missing_cost(r1[0], NS, XI), _ac(r1[0].D))
        m2 = (r2[1], hiding_failure(r2[0], S, XI), missing_cost(r2[0], NS, XI), _ac(r2[0].D))
        eq = m1 == m2
        ok = ok and eq
        print(f"[G-B7 {fn.__name__}] run1==run2 = {eq}")
    print("G-B7", "PASS" if ok else "FAIL")
    return ok


def main():
    results = [
        ("G-B1", test_gb1_golden()),
        ("G-B2", test_gb2_noncollapse()),
        ("G-B3", test_gb3_dynamic_vs_static()),
        ("G-B4", test_gb4_invariance()),
        ("G-B5", test_gb5_fairness()),
        ("G-B6", test_gb6_metric_parity()),
        ("G-B7", test_gb7_determinism()),
    ]
    npass = sum(1 for _, ok in results if ok)
    allok = npass == len(results)
    print(f"\nBASELINE gates = {npass}/{len(results)} :",
          ", ".join(f"{n}={'OK' if ok else 'FAIL'}" for n, ok in results))
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
