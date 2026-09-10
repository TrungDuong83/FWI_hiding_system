# Efficient Methods for Hiding Frequent Weighted Itemsets

Source code and datasets for the paper *"Efficient Methods for Hiding Frequent Weighted Itemsets"*.

The project implements two algorithms that hide **sensitive Frequent Weighted Itemsets (FWI)** from a
weighted transaction database by **item deletion**, together with two adapted baselines and an evaluation
pipeline over nine datasets.

## Algorithms

- **HFPriority** (Max-Conflict) — prioritises fast hiding: at each step it removes, from a transaction
  containing an exposed sensitive itemset, the item with the highest `Score_HFP(v) = |SCov(v)| · w(v)`.
  It guarantees all sensitive itemsets are hidden (`HF = 0`) but may distort more non-sensitive itemsets.
- **MCPriority** (Min-Side-Effect) — prioritises preserving non-sensitive itemsets: it performs only
  **safe deletions** (a deletion is *safe* iff no non-sensitive FWI drops below the threshold after the
  removal, checked over the **entire** non-sensitive set) and stops on a no-op pass. It keeps `MC = 0` by
  construction, accepting that some sensitive itemsets may remain exposed. Victims are ranked by
  `Score_MCP(v) = 1 / (|NSCov(v)| + 1)`. An ablation flag toggles the safety check (safe / no-safe).
- **Baselines** — `MSU-MAU` and `MSU-MIU`, an adaptation of the PPUM-style hiding scheme to the weighted
  support setting (item deletion, no safety veto).

## Weighted support model

For a transaction `T` with item weights `w(i)`:

```
tw(T)    = ( Σ_{i∈T} w(i) ) / |T|          # transaction weight (quantities are ignored)
W_total  = Σ_T tw(T)
ws(X)    = ( Σ_{T ⊇ X} tw(T) ) / W_total   # weighted support of itemset X
X is an FWI  ⟺  ws(X) ≥ ξ
```

FWI are mined with a weighted N-list (SWU-N-list) engine (`src/mining/miner.py`).

## Evaluation metrics

| Metric | Meaning |
|---|---|
| **HF** (Hiding Failure) | fraction of sensitive itemsets still frequent after sanitisation (0 = all hidden) |
| **MC** (Missing Cost)   | fraction of non-sensitive FWI lost as a side effect |
| **AC** (Artificial Cost)| fraction of the sanitised FWI set that is new ("phantom" itemsets) |
| **RT** (Runtime)        | wall-clock time of the hiding phase |

## Repository layout

```
src/mining/miner.py            FWI mining engine (weighted N-list)
src/hiding/                    common.py (weighted DB), select_victim.py,
                               hfpriority.py, mcpriority.py, baseline_ppum.py
src/metrics/metrics.py         HF / MC / AC / AC helpers
src/datautil/                  preprocess.py (loader), iot_discretize.py (IoT CSV → transactions)
calibration/                   calibrate.py, per-dataset thresholds (calib_*.json),
                               sensitivity grids (sweep_grid*.json, sweep_grid*.py)
coordinator/run_coordinator.py experiment driver (all datasets × methods → results/summary.csv)
tests/                         golden + property tests (correctness)
datasets/                      9 datasets (see datasets/README.md)
results/summary.csv            reference results (245 cells)
```

## How to run

Requires **Python 3.10+**.

```bash
pip install -r requirements.txt

# Large transaction files are gzipped to keep the repository small — decompress once:
gunzip -k datasets/*_quantities.txt.gz

# 1. Calibrate the per-dataset thresholds ξ (writes calibration/calib_<ds>.json).
#    (Pre-computed calib_*.json are already included; this step reproduces them.)
python3 calibration/calibrate.py

# 2. Run the experiments (each cell: hide → measure HF/MC/AC/RT → re-mine for AC).
#    Results are written to results/result_*.json and aggregated in results/summary.csv.
PYTHONHASHSEED=0 python3 coordinator/run_coordinator.py            # all 9 datasets, 5 methods
#    Or a single dataset:
PYTHONHASHSEED=0 python3 coordinator/run_coordinator.py --ds chess_fimi

# 3. Inspect results/summary.csv (one row per dataset × method × threshold multiplier).
```

Correctness can be checked without the full run (uses only the small datasets):

```bash
for t in test_g1 test_g2_hfp test_g3_mcp test_baseline_golden test_g5_g7 test_g6 test_ginc; do
    PYTHONHASHSEED=0 python3 tests/$t.py
done
```

Runtimes are measured sequentially (one cell at a time) so they are comparable across methods; set
`PYTHONHASHSEED=0` for deterministic tie-breaking. Membership uses `ws ≥ ξ` on 64-bit floats.

## Datasets

Seven standard FIMI datasets (chess, mushroom, accident, retail, bms-pos, kosarak, chainstore) and two IoT
datasets (mnc, rtvcq). See [`datasets/README.md`](datasets/README.md) for statistics, thresholds, sources
and the IoT discretisation procedure.
