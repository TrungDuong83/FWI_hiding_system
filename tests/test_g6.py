# -*- coding: utf-8 -*-
"""
tests/test_g6.py — Gate G6: engine PART 3 (SWU-N-list, đã vá 2 chỗ) ĐÚNG.

Chuẩn verify (docs/SPEC_PART3_FIX.md §VERIFY):
  1. GOLDEN (running example ξ=0.55) → FWI == 9 tập {A,C,D,E,AC,AD,CD,CE,ACD}.
  2. FIXTURE (W={A:.4,B:.1,C:.8,D:.4}, ξ=11/25, D={T1:AB,T2:BD,T3:ABC}) → 7 tập (có ABC).
  3. MATCH brute-force oracle (tests/oracle_bruteforce.py), 0 miss / 0 extra, per-len khớp:
       - chess_fimi  ξ=0.90 → 584  per_len {1:13,2:67,3:159,4:193,5:117,6:32,7:3}
       - mushroom    ξ=0.60 → 57   per_len {1:8,2:18,3:19,4:10,5:2}

ws bất biến theo scale (Q4) nên engine + oracle dùng CHUNG bộ weights (raw) là hợp lệ:
cùng ξ ⇒ cùng tập FWI. KHÔNG import logic; engine gọi qua adapter mine_fwi().
Entry-guarded (if __name__=="__main__"); trả exit code != 0 nếu FAIL.
"""
import os
import sys
import logging

logging.disable(logging.CRITICAL)          # tắt log engine cho gọn output

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "datasets")
sys.path.insert(0, os.path.join(ROOT, "src", "mining"))
sys.path.insert(0, HERE)

from miner import mine_fwi, fwi_itemsets                                   # noqa: E402
from oracle_bruteforce import (                                            # noqa: E402
    load_transactions_from_file, load_weights_from_file, brute_force_fwi, per_len,
)


def _engine_set(D, W, xi):
    return fwi_itemsets(mine_fwi(D, W, xi))


def test_golden():
    W = {"A": 0.9, "B": 0.4, "C": 0.7, "D": 0.5, "E": 0.2}
    D = {"T1": set("ACDE"), "T2": set("BCE"), "T3": set("ACD"),
         "T4": set("ABCE"), "T5": set("ACDE"), "T6": set("BDE")}
    got = {"".join(sorted(x)) for x in _engine_set(D, W, 0.55)}
    exp = {"A", "C", "D", "E", "AC", "AD", "CD", "CE", "ACD"}
    ok = got == exp
    print(f"[golden]  #{len(got)} match={ok} diff={got ^ exp}")
    return ok


def test_fixture():
    W = {"A": 0.4, "B": 0.1, "C": 0.8, "D": 0.4}
    D = {"T1": set("AB"), "T2": set("BD"), "T3": set("ABC")}
    got = {"".join(sorted(x)) for x in _engine_set(D, W, 11 / 25)}
    exp = {"A", "B", "C", "AB", "AC", "BC", "ABC"}
    ok = got == exp
    print(f"[fixture] #{len(got)} match={ok} diff={got ^ exp}")
    return ok


def test_oracle_match(name, tfile, wfile, xi, exp_count, exp_per_len):
    D = load_transactions_from_file(os.path.join(DATA, tfile))
    W = load_weights_from_file(os.path.join(DATA, wfile))
    eng = _engine_set(D, W, xi)
    orc = brute_force_fwi(D, W, xi)
    missing = orc - eng          # oracle có, engine thiếu
    extra = eng - orc            # engine có, oracle không
    pe, po = per_len(eng), per_len(orc)
    ok = (not missing) and (not extra) and (pe == po) \
        and (len(eng) == exp_count) and (pe == exp_per_len)
    print(f"[{name}] ξ={xi} engine#={len(eng)} oracle#={len(orc)} "
          f"miss={len(missing)} extra={len(extra)} per_len_ok={pe == po} "
          f"target#={exp_count} per_len={pe}")
    if missing:
        print(f"    ! MISSING (oracle\\engine): {sorted(map(sorted, list(missing)[:10]))}")
    if extra:
        print(f"    ! EXTRA  (engine\\oracle): {sorted(map(sorted, list(extra)[:10]))}")
    return ok


def main():
    results = []
    results.append(("golden", test_golden()))
    results.append(("fixture", test_fixture()))
    results.append(("chess_fimi", test_oracle_match(
        "chess_fimi", "chess_fimi_quantities.txt", "chess_fimi_weights.txt",
        0.90, 584, {1: 13, 2: 67, 3: 159, 4: 193, 5: 117, 6: 32, 7: 3})))
    results.append(("mushroom", test_oracle_match(
        "mushroom", "mushroom_quantities.txt", "mushroom_weights.txt",
        0.60, 57, {1: 8, 2: 18, 3: 19, 4: 10, 5: 2})))

    allok = all(ok for _, ok in results)
    print("\nG6", "PASS" if allok else "FAIL",
          "-", ", ".join(f"{n}={'OK' if ok else 'FAIL'}" for n, ok in results))
    return allok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
