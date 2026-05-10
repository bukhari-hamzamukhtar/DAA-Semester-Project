# DAA Semester Project
## Comparison of Apriori for Frequent Itemset Mining with State-of-the-Art Algorithms and Optimization Strategies

**CS-378: Design and Analysis of Algorithms**  
GIK Institute of Engineering Sciences and Technology

**Authors:** Syed Hamza Mukhtar Bukhari · Muhammad Saim · Muhammad Moosa

---

## Repository Structure

```
DAA-Semester-Project/
│
├── src/
│   ├── apriori.py          # Baseline Apriori algorithm + benchmark wrapper
│   ├── sota.py             # SHFIM-dECLAT (Al-Bana et al., 2022)
│   ├── optimizations.py    # Apriori_Bitmap + Apriori_TIDlist
│   └── benchmark.py        # Full benchmark orchestrator (all 4 algos × 3 datasets × 4 thresholds)
│
├── data/
│   ├── chess.dat           # 3,196 transactions · 75 items · dense
│   ├── connect.dat         # 67,557 transactions · 130 items · dense
│   └── accidents.txt       # ← open this file for the Google Drive download link
│                           #   (file was too large to commit directly)
│
├── results/
│   └── benchmark_results.csv   # Full benchmark output (all runs, all algorithms)
│
├── figures/
│   ├── fig1_chess.png      # Runtime vs min-support — Chess
│   ├── fig1_connect.png    # Runtime vs min-support — Connect
│   ├── fig1_accidents.png  # Runtime vs min-support — Accidents
│   ├── fig2_memory.png     # Peak memory at 85% (tracemalloc delta — see paper §VI)
│   ├── fig3_speedup.png    # Speedup ratio over baseline Apriori
│   └── fig4_itemsets.png   # Frequent itemsets discovered — Chess
│
├── paper/
│   └── ieee_report_final.html  # Final IEEE-format report (print to PDF for submission)
│
└── README.md
```

---

## Dataset Setup

`chess.dat` and `connect.dat` are already in the `data/` folder and will work out of the box.

`accidents.dat` was too large to commit. To get it:
1. Open `data/accidents.txt`
2. Copy the Google Drive link inside it
3. Download `accidents.dat` and drop it into `data/`
4. Run benchmarks normally — `benchmark.py` will find it automatically

---

## Running the Baseline Apriori

To run just the baseline and get averaged performance stats, import the benchmark wrapper:

```python
from src.apriori import benchmark_baseline

# Runs the algorithm 3 times and returns averaged metrics
metrics = benchmark_baseline("chess", "data/chess.dat", 0.90)
print(metrics)
```

To call the raw algorithm directly (single run):

```python
from src.apriori import load_dataset, apriori

transactions = load_dataset("data/chess.dat")
result = apriori(transactions, 0.90)

print(f"Runtime:    {result['runtime_sec']:.4f}s")
print(f"Memory:     {result['memory_mb']:.4f} MB")
print(f"Itemsets:   {result['frequent_itemsets']}")
print(f"Candidates: {result['candidates_generated']}")
```

---

## Running SHFIM-dECLAT

```python
from src.apriori import load_dataset
from src.sota import sota_fim

transactions = load_dataset("data/chess.dat")
result = sota_fim(transactions, 0.90)

print(f"Runtime:  {result['runtime_sec']:.4f}s")
print(f"Itemsets: {result['frequent_itemsets']}")
```

---

## Running the Optimizations

```python
from src.apriori import load_dataset
from src.optimizations import apriori_bitmap, apriori_tidlist

transactions = load_dataset("data/chess.dat")

# Bitmap-based support counting
bitmap_result = apriori_bitmap(transactions, 0.90)

# TID-list intersection
tidlist_result = apriori_tidlist(transactions, 0.90)
```

---

## Running the Full Benchmark

This runs all four algorithms across all three datasets at all four thresholds, three times each, and writes results to `results/benchmark_results.csv`. Takes a while — Connect and Accidents at lower thresholds are slow.

```bash
cd DAA-Semester-Project
python src/benchmark.py
```

Progress prints to the terminal live. Any run exceeding 600 seconds is marked `DNF` and the next combo starts immediately.

> **Note:** `benchmark.py` uses `signal.SIGALRM` for hard timeouts. This requires macOS or Linux. It will not work on Windows as-is.

---

## Expected Output Format

Every algorithm returns the same dictionary structure so the benchmark runner and figure scripts work without modification:

```python
{
    'algorithm':            'Apriori',      # or 'SHFIM-dECLAT', 'Apriori_Bitmap', 'Apriori_TIDlist'
    'dataset':              'chess',
    'min_sup':              0.90,
    'runtime_sec':          0.5700,         # average of 3 runs
    'memory_mb':            0.0,            # tracemalloc delta — see §VI of report for why this reads 0
    'frequent_itemsets':    601,
    'candidates_generated': 4847
}
```

If you're adding a new algorithm, match this format exactly or the benchmark CSV columns will break.

---

## Results Folder

`results/benchmark_results.csv` contains the full output of `benchmark.py` — every algorithm, dataset, threshold, and individual run time. Columns:

| Column | Description |
|---|---|
| `algorithm` | Algorithm name |
| `dataset` | chess / connect / accidents |
| `min_sup` | Minimum support threshold (0.80 – 0.95) |
| `run_1_time` … `run_3_time` | Wall-clock time per individual run (seconds), or `DNF` |
| `avg_time` | Average of completed runs, or `DNF` |
| `memory_mb` | Peak memory via tracemalloc (see note above) |
| `frequent_itemsets` | Count of frequent itemsets discovered |
| `candidates_generated` | Candidate itemsets generated (Apriori-family only) |

DNF = Did Not Finish within the 600-second hard limit.

---

## A Note on Memory Values

All `memory_mb` values in the CSV are `0.0`. This is not a bug in the algorithms — it is a known limitation of Python's `tracemalloc` module: it measures memory *allocations made after the tracker starts* (a delta), not the absolute resident set size. Because the transaction database is loaded into memory before `tracemalloc.start()` is called inside each algorithm, the dominant memory cost is invisible to the tracker. The paper discusses this in full in §VI. Future work would use `psutil.Process().memory_info().rss` for absolute RSS measurement.

---

## Dependencies

Standard library only — no pip installs required:

```
python >= 3.9
time, tracemalloc, signal, csv, os  (all built-in)
```

---

## Reference

Al-Bana, M. R., Farhan, M. S., and Othman, N. A. (2022). "An efficient Spark-based hybrid frequent itemset mining algorithm for big data." *MDPI Data*, vol. 7, no. 1, Art. no. 11. DOI: [10.3390/data7010011](https://doi.org/10.3390/data7010011)
