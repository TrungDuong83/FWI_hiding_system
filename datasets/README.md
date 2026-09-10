# Datasets

Nine datasets in the extended **FIMI** text format. Each dataset has two files:

- `<name>_quantities.txt` — one line per transaction, space-separated tokens `item:quantity`.
  (Quantities are **ignored** by the weighted-support model; only the item set of each line is used.)
- `<name>_weights.txt` — one line per item, `item:weight`, where **weight is an integer in [1, 10]**.
  The loader normalises weights by dividing by 10, giving item weights in `(0, 1]`.

The four largest transaction files are stored gzipped (`*_quantities.txt.gz`); run
`gunzip -k datasets/*_quantities.txt.gz` before using them.

## Weighted-itemset definitions

```
tw(T)   = ( Σ_{i∈T} w(i) ) / |T|          transaction weight (average item weight)
W_total = Σ_T tw(T)
ws(X)   = ( Σ_{T ⊇ X} tw(T) ) / W_total   weighted support
X is a Frequent Weighted Itemset (FWI)  ⟺  ws(X) ≥ ξ
```

Weights are drawn i.i.d. **uniformly from {1, …, 10}** (fixed seed) for every dataset, so all datasets
share the same item-weight scheme.

## Statistics and thresholds

`#Trans`, `#Items`, average / max transaction length and density are computed directly from the
`_quantities.txt` files. `ξ`, `#FWI` and `#SFWI` (sensitive itemsets) are the calibrated values stored in
`calibration/calib_<name>.json` (chosen so that `50 ≤ #FWI ≤ 300`; `#SFWI` is the top ~10% by overlap
score, clamped to `[10, 40]`).

| Dataset | #Trans | #Items | Avg len | Max len | Density | ξ | #FWI | #SFWI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| chess_fimi | 3,196 | 75 | 37.00 | 37 | 49.33% | 0.920 | 293 | 28 |
| mushroom | 8,416 | 119 | 23.00 | 23 | 19.33% | 0.457 | 299 | 28 |
| accident | 340,183 | 468 | 33.81 | 51 | 7.22% | 0.751 | 299 | 28 |
| bms-pos | 515,596 | 1,657 | 6.53 | 164 | 0.39% | 0.021 | 276 | 21 |
| retail | 88,162 | 16,470 | 10.31 | 76 | 0.063% | 0.008 | 241 | 14 |
| kosarak | 990,002 | 41,270 | 8.10 | 2,498 | 0.020% | 0.011 | 263 | 22 |
| chainstore | 1,112,949 | 46,086 | 7.23 | 170 | 0.016% | 0.003 | 264 | 10 |
| mnc (IoT) | 736,974 | 96 | 14.00 | 14 | 14.58% | 0.204 | 297 | 27 |
| rtvcq (IoT) | 63,336 | 76 | 7.25 | 8 | 9.54% | 0.057 | 295 | 26 |

Sensitivity experiments additionally use thresholds `ξ(m) = round(m · ξ, 3)` for multipliers
`m ∈ {0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6}`; the feasible points are listed in
`calibration/sweep_grid.json` (FIMI) and `calibration/sweep_grid_iot.json` (IoT).

> **mushroom** has 8,416 transaction lines = **8,124 distinct item sets** + 292 records that repeat an
> item set with a different quantity annotation. Since quantities are ignored, these are equivalent
> transactions; all lines are kept (each line is one transaction, as with any repeated transaction). The
> 8,124 distinct item sets match the standard FIMI mushroom dataset.

## Sources

- **Standard datasets** (chess, mushroom, accident, retail, bms-pos, kosarak, chainstore): the FIMI
  Repository / SPMF collection of frequent-itemset-mining benchmarks. Item weights are generated
  synthetically (uniform integers in [1, 10]); `bms-pos` was normalised from its raw CSV to FIMI format.
- **mnc** — *Mobile Network Coverage* measurements, Data in Brief, DOI `10.1016/j.dib.2024.111146`.
  17 of 33 fields were selected and discretised (see below).
- **rtvcq** — *Call Voice Quality Experience* (TRAI / Kaggle, April 2018 release). Eight fields discretised.

## IoT discretisation (`src/datautil/iot_discretize.py`, configs `src/datautil/cfg_*.json`)

Each CSV row becomes one transaction. For each configured field:

1. **Categorical** field → one item `field=value`.
2. **Continuous** field → 10 equal-width bins (range computed over the whole file) → item `field=binK`.
3. Missing values (blank or the configured sentinels, e.g. `-1`) produce **no item** and are excluded
   from the range.
4. Every item is emitted with quantity 1; weights follow the uniform [1, 10] scheme above.

For **mnc**, three fields were dropped and only 14 remain (6 categorical + 8 continuous): a constant field
(`Location Status`) and two non-discriminative continuous fields whose values fall almost entirely into a
single bin (`Latitude`, `Downstream Bandwidth`, ≥ 99% in one bin). The exact field lists are in
`cfg_mnc.json` and `cfg_rtvcq.json`. Item-index maps are provided as `mnc_itemmap.json` / `rtvcq_itemmap.json`.
