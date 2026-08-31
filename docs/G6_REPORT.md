# G6_REPORT — Verify engine PART 3 (SWU-N-list đã vá 2 chỗ)

> Gate G6: engine coi là ĐÚNG ⟺ golden + fixture khớp VÀ khớp brute-force oracle
> (0 miss / 0 extra, per-len khớp) trên ≥2 dataset. Chuẩn: docs/SPEC_PART3_FIX.md §VERIFY.
> Mọi số dưới đây là output THẬT của `python3 tests/test_g6.py` (không bịa).

## Thành phần
- Engine: `src/mining/miner.py` (port PART 3 v38; gỡ Colab; **FIX A** `tw=Σw/|T|` bỏ qty;
  **FIX B** `swunl_intersection_optimized` giao tidset + wiring `tw_map`). KHÔNG đổi logic khác.
- Oracle độc lập: `tests/oracle_bruteforce.py` (Apriori level-wise + giao tidset, KHÔNG import engine).
- Adapter test: `mine_fwi()` (đơn luồng, tất định) → `fwi_itemsets()` (set frozenset).
- `ws` bất biến theo scale (Q4) ⇒ engine + oracle dùng CHUNG weights raw, cùng ξ ⇒ cùng tập FWI.

## Kết quả chạy (real)
```
[golden]  #9 match=True diff=set()
[fixture] #7 match=True diff=set()
[chess_fimi] ξ=0.9 engine#=584 oracle#=584 miss=0 extra=0 per_len_ok=True target#=584 per_len={1: 13, 2: 67, 3: 159, 4: 193, 5: 117, 6: 32, 7: 3}
[mushroom] ξ=0.6 engine#=57 oracle#=57 miss=0 extra=0 per_len_ok=True target#=57 per_len={1: 8, 2: 18, 3: 19, 4: 10, 5: 2}

G6 PASS - golden=OK, fixture=OK, chess_fimi=OK, mushroom=OK
```
Wall-clock toàn bộ test: ~1.6s (đơn luồng).

## Bảng đối chiếu với target SPEC_PART3_FIX §VERIFY
| Case | ξ | Target #FWI | Engine #FWI | Oracle #FWI | miss / extra | per-len khớp target |
|---|---|---|---|---|---|---|
| Golden running example | 0.55 | 9 `{A,C,D,E,AC,AD,CD,CE,ACD}` | 9 | — | 0 / 0 | ✓ |
| Fixture (có ABC) | 11/25 | 7 `{A,B,C,AB,AC,BC,ABC}` | 7 | — | 0 / 0 | ✓ |
| chess_fimi | 0.90 | 584 `{1:13,2:67,3:159,4:193,5:117,6:32,7:3}` | 584 | 584 | 0 / 0 | ✓ |
| mushroom | 0.60 | 57 `{1:8,2:18,3:19,4:10,5:2}` | 57 | 57 | 0 / 0 | ✓ |

## Kết luận
Engine PART 3 sau khi vá 2 chỗ tái tạo CHÍNH XÁC golden + fixture và khớp oracle brute-force
(0 miss / 0 extra, per-len khớp) tới k=7 trên chess_fimi và tới k=5 trên mushroom.
Bug over-prune k≥3 (FIX B) và bug `*qty` (FIX A) đã được sửa và verify độc lập.

**VERDICT G6: PASS.**

## Tái lập
```
pip install -r requirements.txt
python3 tests/test_g6.py        # exit 0 = PASS
```
